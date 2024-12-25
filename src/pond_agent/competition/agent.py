"""AutoML agent that orchestrates the ML development process."""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from ..llm import LLMClient
from .base import BaseAgent
from .data_processor import DataProcessor
from .feature_engineer import FeatureEngineer
from .model_builder import ModelBuilder
from .utils import (
    read_data_dictionary,
    read_problem_description,
)

logger = logging.getLogger(__name__)
TIMEZONE = datetime.now().astimezone().tzinfo


class CompetitionAgent(BaseAgent):
    """Agent for automating machine learning tasks."""

    def __init__(
        self,
        input_dir: str | Path,
        llm_provider: str = "openai",
        model_name: str = "gpt-4o",
    ) -> None:
        """Initialize AutoML agent.

        Args:
            input_dir: Directory containing problem descriptions and data files
            llm_provider: LLM provider to use
            model_name: Name of the model to use

        """
        super().__init__()
        self.input_dir = Path(input_dir).resolve()
        self.data_dir = self.input_dir / "dataset"
        now = datetime.now(tz=TIMEZONE)
        self.output_dir = Path.cwd() / "output" / f"run_{now.strftime('%Y%m%d_%H%M%S')}"
        self.processed_dir = self.output_dir / "processed_data"
        self.feature_dir = self.output_dir / "feature_data"
        self.model_dir = self.output_dir / "models"
        self.script_dir = self.output_dir / "scripts"
        self.report_dir = self.output_dir / "reports"

        # Create output directories
        self._setup_output_dirs()

        # Initialize LLM client
        self.llm = LLMClient(llm_provider, model_name)

        # Load and analyze problem description
        self.problem_desc = read_problem_description(self.input_dir / "overview.md")
        self.data_dictionary = read_data_dictionary(
            self.input_dir / "data_dictionary.xlsx"
        )
        self.task_description = self.plan_tasks()

        # Initialize other agents with shared information
        if "preprocessing" in self.task_description:
            self.data_processor = DataProcessor(
                self.llm,
                input_dir=self.data_dir,
                output_dir=self.processed_dir,
                script_dir=self.script_dir,
                task_description=self.task_description,
                data_dictionary=self.data_dictionary,
            )
        else:
            self.data_processor = None
            self.processed_dir = self.data_dir

        if "feature_engineering" in self.task_description:
            self.feature_engineer = FeatureEngineer(
                self.llm,
                input_dir=self.processed_dir,
                output_dir=self.feature_dir,
                script_dir=self.script_dir,
                task_description=self.task_description,
                data_dictionary=self.data_dictionary,
            )
        else:
            self.feature_engineer = None
            self.feature_dir = self.processed_dir

        if "modeling" in self.task_description:
            self.model_builder = ModelBuilder(
                self.llm,
                input_dir=self.feature_dir,
                output_dir=self.model_dir,
                script_dir=self.script_dir,
                task_description=self.task_description,
                data_dictionary=self.data_dictionary,
            )
        else:
            self.model_builder = None

        # Initialize report
        self.report = []
        self.report_path = self.report_dir / "competition_report.md"
        self._add_to_report("# Competition Development Report", self.problem_desc)

    def _setup_output_dirs(self) -> None:
        """Create output directories."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.processed_dir).mkdir(parents=True, exist_ok=True)
        Path(self.feature_dir).mkdir(parents=True, exist_ok=True)
        Path(self.script_dir).mkdir(parents=True, exist_ok=True)
        Path(self.report_dir).mkdir(parents=True, exist_ok=True)
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)

    def plan_tasks(
        self,
    ) -> dict[str, str]:
        """Analyze problem description using LLM.

        Returns:
            Dictionary containing analyzed information:
            - summary: Concise problem summary
            - ml_task: Specific ML task description
            - train_table: Name of table containing ground truth labels
            - eval_table: Name of table for model evaluation

        """
        context = {
            "problem_desc": self.problem_desc,
            "data_dictionary": self.data_dictionary,
        }
        sys_prompt = self.load_prompt_template("competition_agent_system.txt")
        user_prompt = self.load_prompt_template("competition_agent_user.txt", context)

        resp = self.llm.get_response(user_prompt, sys_prompt, json_response=True)
        return resp

    def _save_script(self, name: str, content: str) -> Path:
        """Save generated script to file."""
        script_path = self.script_dir / f"{name}.py"
        with open(script_path, "w") as f:  # noqa: PTH123
            f.write(content)
        logger.info("Saved script: %s", script_path)
        return script_path

    def _add_to_report(self, header: str, content: str) -> None:
        """Add section to report."""
        timestamp = datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        self.report.append(f"{header} \n{timestamp}\n\n{content}\n")
        with open(self.report_path, "w") as f:  # noqa: PTH123
            f.write("\n\n".join(self.report))

    def process_data(self) -> dict[str, pd.DataFrame]:
        """Process raw data.

        Returns:
            Dictionary of processed DataFrames

        """
        logger.info("Processing data")
        # Process data and save to disk
        processed_data = self.data_processor.process()

        # Add to report
        summary = []
        for name, df in processed_data.items():
            summary.append(f"### {name}")
            summary.append(f"- Shape: {df.shape}")
            summary.append(f"- Columns: {list(df.columns)}")
            summary.append(f"- Data Types:\n```\n{df.dtypes}\n```\n")

        self._add_to_report(
            "## Data Processing",
            "Processed the following datasets:\n\n" + "\n".join(summary),
        )

        return processed_data

    def engineer_features(self) -> pd.DataFrame:
        """Engineer features from processed data.

        Returns:
            DataFrame containing engineered features

        """
        logger.info("Engineering features")

        # Engineer features and save to disk
        feature_df = self.feature_engineer.build_features(target="train")

        # Add to report
        summary = []
        for name, df in feature_df.items():
            summary.append(f"### {name}")
            summary.append(f"- Shape: {df.shape}")
            summary.append(f"- Columns: {list(df.columns)}")
            summary.append(f"- Data Types:\n```\n{df.dtypes}\n```\n")

        self._add_to_report(
            "## Feature Engineering",
            "Created feature matrix:\n\n" + "\n".join(summary),
        )

        return feature_df

    def build_model(self) -> None:
        """Build and train an appropriate ML model."""
        logger.info("Building model")

        # Build and train model
        model_result = self.model_builder.build()

        # Generate summary
        summary = [
            "Model Details:",
            f"- Type: {type(model_result.model).__name__}",
            f"- Parameters: {model_result.get_params() or 'N/A'}",
            "\nModel Performance:",
            "```",
            model_result.summary(),
            "```",
        ]

        # Add to report
        self._add_to_report(
            "## Model Development",
            "\n".join(summary),
        )

        # Generate reference script
        script = self.model_builder.generate_script()
        self._save_script("model_training", script)

    def run(self) -> None:
        """Run the complete AutoML pipeline."""
        logger.info("Starting AutoML pipeline")

        # Process data
        self.process_data()

        # Engineer features
        self.engineer_features()

        # Build and train model
        self.build_model()

        # Make predictions
        self.feature_engineer.build_features(target="eval")
        prediction = self.model_builder.predict()
        prediction.to_csv(
            self.output_dir / "predictions.csv",
            index=False,
            columns=["ADDRESS", "PRED"],
        )

        logger.info("AutoML pipeline completed")