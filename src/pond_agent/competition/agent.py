"""AutoML agent that orchestrates the ML development process."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import asyncio

from ..llm import LLMClient
from .base import BaseAgent
from .data_processor import DataProcessor
from .feature_engineer import FeatureEngineer
from .model_builder import ModelBuilder
from .submission_generator import SubmissionGenerator
from .scraper import CompetitionScraper
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
        working_dir: str | Path,
        competition_url: Optional[str] = None,
        llm_provider: str = "openai",
        model_name: str = "gpt-4o",
    ) -> None:
        """Initialize AutoML agent.

        Args:
            working_dir: Directory containing problem descriptions and data files
            competition_url: Optional URL to competition page. If provided, data will be scraped
            llm_provider: LLM provider to use
            model_name: Name of the model to use

        """
        super().__init__()
        self.working_dir = Path(working_dir).resolve()
        self.data_dir = self.working_dir / "dataset"
        now = datetime.now(tz=TIMEZONE)
        self.output_dir = self.working_dir / "output" / f"run_{now.strftime('%Y%m%d_%H%M%S')}"
        self.processed_dir = self.output_dir / "processed_data"
        self.feature_dir = self.output_dir / "feature_data"
        self.model_dir = self.output_dir / "models"
        self.script_dir = self.output_dir / "scripts"

        # Create output directories
        self._setup_output_dirs()

        # Initialize LLM client
        self.llm = LLMClient(llm_provider, model_name)

        # If competition URL is provided, scrape the data
        if competition_url:
            logger.info(f"Scraping competition data from {competition_url}")
            scraper = CompetitionScraper(str(self.working_dir))
            scrape_result = asyncio.run(scraper.scrape(competition_url))
            if not scrape_result or not scrape_result["dataset_dir"]:
                raise RuntimeError("Failed to scrape competition data")
            logger.info("Successfully scraped competition data")

        # Verify required files exist
        if not (self.working_dir / "overview.md").exists():
            raise FileNotFoundError("overview.md not found in working directory")
        if not (self.working_dir / "data_dictionary.xlsx").exists():
            raise FileNotFoundError("data_dictionary.xlsx not found in working directory")
        if not self.data_dir.exists():
            raise FileNotFoundError("dataset directory not found in working directory")

        # Load and analyze problem description
        self.problem_desc = read_problem_description(self.working_dir / "overview.md")
        self.data_dictionary = read_data_dictionary(
            self.working_dir / "data_dictionary.xlsx"
        )
        self.task_description = self.plan_tasks()

        # Initialize other agents with shared information
        self.data_processor = DataProcessor(
            self.llm,
            input_dir=self.data_dir,
            output_dir=self.processed_dir,
            script_dir=self.script_dir,
            task_description=self.task_description,
            data_dictionary=self.data_dictionary,
        )

        self.feature_engineer = FeatureEngineer(
            self.llm,
            input_dir=self.processed_dir,
            output_dir=self.feature_dir,
            script_dir=self.script_dir,
            task_description=self.task_description,
            data_dictionary=self.data_dictionary,
        )

        self.model_builder = ModelBuilder(
            self.llm,
            input_dir=self.feature_dir,
            output_dir=self.model_dir,
            script_dir=self.script_dir,
            task_description=self.task_description,
            data_dictionary=self.data_dictionary,
        )

        self.submission_generator = SubmissionGenerator(
            self.llm,
            raw_data_dir=self.data_dir,
            output_dir=self.output_dir,
            script_dir=self.script_dir,
            task_description=self.task_description,
            data_dictionary=self.data_dictionary,
        )

        # Initialize report
        self.report = []
        self.report_path = self.output_dir / "report.md"
        self._add_to_report("# Model Development Report", "")
        self._add_to_report("## Development Plan", self.task_description)

    def _setup_output_dirs(self) -> None:
        """Create output directories."""
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.processed_dir).mkdir(parents=True, exist_ok=True)
        Path(self.feature_dir).mkdir(parents=True, exist_ok=True)
        Path(self.script_dir).mkdir(parents=True, exist_ok=True)
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)

    def plan_tasks(self) -> dict[str, str]:
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

    def _add_to_report(self, header: str, content: str) -> None:
        """Add section to report."""
        timestamp = datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        self.report.append(f"{header} \n{timestamp}\n\n{content}\n")
        with open(self.report_path, "w") as f:  # noqa: PTH123
            f.write("\n\n".join(self.report))

    def process_data(self) -> None:
        """Process raw data.

        Returns:
            Dictionary of processed DataFrames

        """
        logger.info("Processing data")
        # Process data and save to disk
        processed_data = self.data_processor.run()

        # Add to report
        summary = []
        for name, df in processed_data.items():
            summary.append(f"- **{name}**")
            summary.append(f"  - Shape: {df.shape}")
            summary.append("  - Columns:")
            for col, dtype in df.schema.items():
                summary.append(f"    - {col}: {dtype}")

        self._add_to_report(
            "## Data Processing",
            "Processed data:\n\n" + "\n".join(summary),
        )

    def engineer_features(self) -> None:
        """Engineer features from processed data.

        Returns:
            DataFrame containing engineered features

        """
        logger.info("Engineering features")

        # Engineer features and save to disk
        feature_df = self.feature_engineer.run()

        # Add to report
        summary = []
        for name, df in feature_df.items():
            summary.append(f"- **{name}**")
            summary.append(f"  - Shape: {df.shape}")
            summary.append("  - Columns:")
            for col, dtype in df.schema.items():
                summary.append(f"    - {col}: {dtype}")

        self._add_to_report(
            "## Feature Engineering",
            "Created feature matrix:\n\n" + "\n".join(summary),
        )

    def build_model(self) -> None:
        """Build and train an appropriate ML model."""
        logger.info("Building model")

        # Build and train model
        self.model_builder.run()

        # Add to report
        self._add_to_report(
            "## Model",
            "Model report not implemented yet",
        )

    def generate_submission(self) -> None:
        """Generate submission file."""
        logger.info("Generating submission")
        submit_df = self.submission_generator.run()

        summary = []
        summary.append(f"Shape: {submit_df.shape}  ")
        summary.append("Preview:  ")
        summary.append(f"{submit_df.head().to_markdown(index=False)}")

        # Add to report
        self._add_to_report(
            "## Submission File",
            "\n".join(summary),
        )

    def run(self) -> None:
        """Run the complete model development pipeline."""
        logger.info("Starting model development pipeline")

        # Process data
        self.process_data()

        # Engineer features
        self.engineer_features()

        # Build and train model
        self.build_model()

        # Make predictions
        self.generate_submission()

        logger.info("Model development pipeline completed")
