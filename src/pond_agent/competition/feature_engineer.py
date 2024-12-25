"""Feature engineering module with LLM-powered recommendations."""

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


class FeatureEngineer(BaseAgent):
    """Feature engineering component."""

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
        """Generate feature engineering script.

        Returns:
            String containing Python script

        """
        logger.info("Generating feature engineering script")

        # Load processed data to get schema
        processed_data, data_paths = load_parquet_data(self.input_dir, return_path=True)

        # Get feature engineering script
        script = self._get_script_from_llm(processed_data, data_paths)

        # Save script
        script_path = self.script_dir / "engineer_features.py"
        with open(script_path, "w") as f:  # noqa: PTH123
            f.write(script)
            logger.info("Saved feature engineering script to %s", script_path)

        return script_path

    def _get_script_from_llm(
        self,
        processed_data: dict[str, pl.DataFrame],
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
        for name, df in processed_data.items():
            data_dict = self.data_dictionary.get(name, {})
            info = {
                "name": name,
                "description": data_dict.get("description", ""),
                "shape": df.shape,
                "column_dtypes": {
                    str(col): str(dtype) for col, dtype in df.schema.items()
                },
                "column_descriptions": data_dict.get("columns", {}),
            }
            dataset_info.append(info)

        context = {
            "output_dir": self.output_dir,
            "problem_summary": self.task_description["summary"],
            "dataset_info": dataset_info,
            "data_paths": data_paths,
            "feature_engineering_instructions": self.task_description[
                "feature_engineering"
            ],
        }

        sys_prompt = self.load_prompt_template("feature_engineer_system.txt")
        user_prompt = self.load_prompt_template("feature_engineer_user.txt", context)

        resp = self.llm.get_response(user_prompt, sys_prompt, json_response=False)
        resp = resp.strip().strip("`").removeprefix("python")
        self.script = resp
        return resp

    def run(self, retry_count: int = 3) -> dict[str, pl.DataFrame]:
        """Engineer features by executing generated script.

        Returns:
            Dictionary of processed DataFrames

        """
        logger.info("Engineering features")

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
                msg = f"Error executing feature engineering script: {stderr}"
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
                else:
                    logger.error("Error fixing bug")
                    raise RuntimeError("Error fixing bug") from None

            logger.info("Successfully executed feature engineering script")

            # Load processed datasets
            return load_parquet_data(self.output_dir)

        except subprocess.CalledProcessError as e:
            msg = f"Error executing feature engineering script: {e.stderr}"
            logger.error(msg)
            raise RuntimeError(msg) from e