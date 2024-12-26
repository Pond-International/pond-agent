"""Data processing module with LLM-powered analysis."""

import logging
import os
import subprocess
from pathlib import Path

import polars as pl

from ..llm import LLMClient
from ..tools import run_python_script
from .base import BaseAgent
from .bug_fixer import BugFixer
from .utils import load_parquet_data

logger = logging.getLogger(__name__)


class DataProcessor(BaseAgent):
    """Data processing component."""

    def __init__(
        self,
        llm_client: LLMClient,
        input_dir: Path,
        output_dir: Path,
        script_dir: Path,
        task_description: dict,
        data_dictionary: dict,
    ) -> None:
        """Initialize data processor.

        Args:
            llm_client: LLM client for getting recommendations
            input_dir: Directory containing raw data files
            output_dir: Directory to save processed data
            task_description: Task description
            data_dictionary: Optional data dictionary

        """
        super().__init__()
        self.llm = llm_client
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.script_dir = Path(script_dir)
        self.task_description = task_description
        self.data_dictionary = data_dictionary
        self.script = None
        self.bug_fixer = BugFixer(llm_client)

    def generate_script(self) -> str:
        """Generate data processing script.

        Returns:
            String containing Python script

        """
        logger.info("Generating data processing script")

        # Load raw data to get schema
        raw_data, data_paths = load_parquet_data(self.input_dir, return_path=True)

        # Get preprocessing recommendations
        script = self._get_script_from_llm(raw_data, data_paths)

        # Save script
        script_path = self.script_dir / "preprocess_data.py"
        with open(script_path, "w") as f:  # noqa: PTH123
            f.write(script)
            logger.info("Saved processing script to %s", script_path)

        return script_path

    def _get_script_from_llm(
        self,
        raw_data: dict[str, pl.DataFrame],
        data_paths: dict[str, str],
    ) -> str:
        """Get feature engineering recommendations from LLM.

        Args:
            data_paths: Dictionary of data paths
            processed_data: Dictionary of processed DataFrames
        Returns:
            Dictionary containing feature engineering script

        """
        # Prepare dataset info for LLM
        dataset_info = []
        for name, df in raw_data.items():
            data_dict = self.data_dictionary.get(name, {})
            info = {
                "name": name,
                "description": data_dict.get("description", ""),
                "shape": df.shape,
                "column_dtypes": {
                    str(col): str(dtype) for col, dtype in df.schema.items()
                },
                "column_descriptions": data_dict.get("columns", {}),
                "missing_values": {
                    col: count
                    for col, count in zip(df.columns, df.null_count(), strict=False)
                },
            }
            dataset_info.append(info)

        context = {
            "output_dir": self.output_dir,
            "problem_summary": self.task_description["summary"],
            "dataset_info": dataset_info,
            "data_paths": data_paths,
            "preprocessing_instructions": self.task_description["preprocessing"],
        }

        sys_prompt = self.load_prompt_template("data_processor_system.txt")
        user_prompt = self.load_prompt_template("data_processor_user.txt", context)

        resp = self.llm.get_response(user_prompt, sys_prompt, json_response=False)
        resp = resp.strip().strip("`").removeprefix("python")
        self.script = resp
        return resp

    def run(self, retry_count: int = 3) -> dict[str, pl.DataFrame]:
        """Process raw data files by executing generated script.

        Returns:
            Dictionary of processed DataFrames

        """
        logger.info("Processing raw data files")

        # Generate and save script
        script_path = self.generate_script()
        if not script_path.exists():
            msg = f"data_processing.py not found in {self.script_dir}"
            raise ValueError(msg)

        # Execute script in subprocess
        env = os.environ.copy()
        env["PYTHONPATH"] = str(
            Path(__file__).parent.parent.parent
        )  # Add project root to PYTHONPATH

        try:
            returncode, stderr = run_python_script(script_path, env, logger)

            while returncode != 0 and retry_count > 0:
                msg = f"Error executing data processing script: {stderr}"
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

            logger.info("Successfully executed data processing script")
            # Load processed datasets
            return load_parquet_data(self.output_dir)

        except subprocess.CalledProcessError as e:
            msg = f"Error executing data processing script: {e.stderr}"
            logger.error(msg)
            raise RuntimeError(msg) from e

        except RuntimeError as e:
            logger.error(str(e))
            raise