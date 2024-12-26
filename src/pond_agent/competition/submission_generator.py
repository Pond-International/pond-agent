"""Submission generation module with LLM-powered recommendations."""

import logging
import os
import subprocess
from pathlib import Path

import polars as pl
import pandas as pd

from ..llm import LLMClient
from ..tools import run_python_script
from .base import BaseAgent
from .bug_fixer import BugFixer
from .utils import load_parquet_data

logger = logging.getLogger(__name__)


class SubmissionGenerator(BaseAgent):
    """Submission generation component."""

    def __init__(
        self,
        llm_client: LLMClient,
        raw_data_dir: Path,
        output_dir: Path,
        script_dir: Path,
        task_description: dict,
        data_dictionary: dict,
    ) -> None:
        """Initialize submission generator.

        Args:
            llm_client: LLM client for getting recommendations
            input_dir: Directory containing raw data files
            output_dir: Directory to save processed data
            task_description: Task description
            data_dictionary: Optional data dictionary

        """
        super().__init__()
        self.llm = llm_client
        self.raw_data_dir = Path(raw_data_dir)
        self.output_dir = Path(output_dir)
        self.script_dir = Path(script_dir)
        self.task_description = task_description
        self.data_dictionary = data_dictionary
        self.script = None
        self.bug_fixer = BugFixer(llm_client)

    def generate_script(self) -> str:
        """Generate submission script.

        Returns:
            String containing Python script

        """
        logger.info("Generating submission script")

        # Load raw data to get schema
        raw_data, data_paths = load_parquet_data(self.raw_data_dir, return_path=True)

        # Get submission script
        script = self._get_script_from_llm(raw_data, data_paths)

        # Save script
        script_path = self.script_dir / "generate_submission.py"
        with open(script_path, "w") as f:  # noqa: PTH123
            f.write(script)
            logger.info("Saved submission script to %s", script_path)

        return script_path

    def _get_script_from_llm(
        self,
        raw_data: dict[str, pl.DataFrame],
        data_paths: dict[str, str],
    ) -> str:
        """Get submission script from LLM.

        Args:
            raw_data: Dictionary of raw DataFrames
            data_paths: Dictionary of data paths
        Returns:
            String containing submission script

        """
        # Prepare dataset info for LLM
        dataset_info = []
        for name, df in raw_data.items():
            info = {
                "name": name,
                "column_dtypes": {
                    str(col): str(dtype) for col, dtype in df.schema.items()
                },
            }
            dataset_info.append(info)

        with open(self.script_dir / "engineer_features.py") as f:
            fe_code = f.read()
        with open(self.script_dir / "build_model.py") as f:
            train_code = f.read()

        context = {
            "output_dir": self.output_dir,
            "task_summary": self.task_description["summary"],
            "submission_instructions": self.task_description["submission"],
            "dataset_info": dataset_info,
            "data_paths": data_paths,
            "fe_code": fe_code,
            "train_code": train_code,
        }

        sys_prompt = self.load_prompt_template("submission_generator_system.txt")
        user_prompt = self.load_prompt_template(
            "submission_generator_user.txt", context
        )

        resp = self.llm.get_response(user_prompt, sys_prompt, json_response=False)
        resp = resp.strip().strip("`").removeprefix("python")
        self.script = resp
        return resp

    def run(self, retry_count: int = 3) -> dict[str, pl.DataFrame]:
        """Generate submission file by executing generated script.

        Returns:
            Dictionary of processed DataFrames

        """
        logger.info("Generating submission")

        # Generate and save script
        script_path = self.generate_script()
        if not script_path.exists():
            msg = f"Submission generation script not found in {self.script_dir}"
            raise ValueError(msg)

        # Execute script in subprocess
        env = os.environ.copy()
        env["PYTHONPATH"] = str(
            Path(__file__).parent.parent.parent
        )  # Add project root to PYTHONPATH

        try:
            returncode, stderr = run_python_script(script_path, env, logger)

            while returncode != 0 and retry_count > 0:
                msg = f"Error executing submission generation script: {stderr}"
                logger.error(msg)
                logger.info("Attempting to fix bug, %d attempts remaining", retry_count)
                with open(script_path) as script_file:
                    script = script_file.read()
                fixed_code = self.bug_fixer.fix_bug(script, stderr)
                if fixed_code:
                    with open(script_path, "w") as script_file:
                        script_file.write(fixed_code)
                    returncode, stderr = run_python_script(script_path, env, logger)
                retry_count -= 1
            
            if returncode != 0:
                msg = f"Cannot fix the bug: {stderr}"
                logger.error(msg)
                raise RuntimeError(msg) from None

            logger.info("Successfully executed submission generation script")

            # Load processed datasets
            return pd.read_csv(self.output_dir / "submission.csv")

        except subprocess.CalledProcessError as e:
            msg = f"Error executing submission generation script: {e.stderr}"
            logger.error(msg)
            raise RuntimeError(msg) from e

        except RuntimeError as e:
            logger.error(str(e))
            raise