"""AutoML agent that orchestrates the ML development process."""

import logging
from datetime import datetime
import json
from pathlib import Path
from typing import Optional, Union
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
                only if required files don't already exist
            llm_provider: LLM provider to use
            model_name: Name of the model to use

        Raises:
            FileNotFoundError: If competition_url is not provided and required files are missing
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
        self.competition_url = competition_url
        self.skip_scraping = False

        # Create output directories
        self._setup_output_dirs()

        # Initialize LLM client
        self.llm = LLMClient(llm_provider, model_name)

        # Check for existing dataset files
        has_overview = (self.working_dir / "overview.md").exists()
        has_data_dict = (self.working_dir / "data_dictionary.xlsx").exists()
        has_dataset = self.data_dir.exists()

        self.scraper = CompetitionScraper(str(self.working_dir))
        if competition_url:
            # If all files exist, set flag to skip scraping
            if has_overview and has_data_dict and has_dataset:
                logger.warning(
                    "Competition files already exist in working directory. "
                    "Skipping competition data scraping."
                )
                self.skip_scraping = True
        else:
            # If no competition URL, verify required files exist
            if not has_overview:
                raise FileNotFoundError("overview.md not found in working directory")
            if not has_data_dict:
                raise FileNotFoundError("data_dictionary.xlsx not found in working directory")
            if not has_dataset:
                raise FileNotFoundError("dataset directory not found in working directory")

        # Initialize report
        self.report = []
        self.report_path = self.output_dir / "report.md"
        self._add_to_report("# Model Development Report", "")

        # Initialize other agents without task description and data dictionary
        self.data_processor = DataProcessor(
            self.llm,
            input_dir=self.data_dir,
            output_dir=self.processed_dir,
            script_dir=self.script_dir,
            task_description={},
            data_dictionary={},
        )

        self.feature_engineer = FeatureEngineer(
            self.llm,
            input_dir=self.processed_dir,
            output_dir=self.feature_dir,
            script_dir=self.script_dir,
            task_description={},
            data_dictionary={},
        )

        self.model_builder = ModelBuilder(
            self.llm,
            input_dir=self.feature_dir,
            output_dir=self.model_dir,
            script_dir=self.script_dir,
            task_description={},
            data_dictionary={},
        )

        self.submission_generator = SubmissionGenerator(
            self.llm,
            raw_data_dir=self.data_dir,
            output_dir=self.output_dir,
            script_dir=self.script_dir,
            task_description={},
            data_dictionary={},
        )

    def _update_agent_configs(self, task_description: dict, data_dictionary: dict) -> None:
        """Update task description and data dictionary for all agents.

        Args:
            task_description: Task description dictionary
            data_dictionary: Data dictionary
        """
        for agent in [
            self.data_processor,
            self.feature_engineer,
            self.model_builder,
            self.submission_generator,
        ]:
            agent.task_description = task_description
            agent.data_dictionary = data_dictionary

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

    def _format_task_description(self, task_dict: dict) -> str:
        """Format task description dictionary into readable markdown.

        Args:
            task_dict: Dictionary containing task description

        Returns:
            Formatted markdown string
        """
        lines = []

        def format_value(value) -> str:
            if not value:
                return "No information provided"
            if isinstance(value, str):
                return value
            return f"```json\n{json.dumps(value, indent=2)}\n```"

        # Problem Summary
        lines.append("### Problem Summary")
        lines.append(format_value(task_dict.get("summary", "")))
        lines.append("")

        # Data Preprocessing
        lines.append("### Data Preprocessing")
        lines.append(format_value(task_dict.get("preprocessing", "")))
        lines.append("")

        # Feature Engineering
        lines.append("### Feature Engineering")
        lines.append(format_value(task_dict.get("feature_engineering", "")))
        lines.append("")

        # Modeling
        lines.append("### Modeling")
        lines.append(format_value(task_dict.get("modeling", "")))
        lines.append("")

        # Submission
        lines.append("### Submission")
        lines.append(format_value(task_dict.get("submission", "")))

        return "\n".join(lines)

    def _add_to_report(self, header: str, content: Union[str, dict]) -> None:
        """Add section to report.

        Args:
            header: Section header
            content: Content to add, can be string or dictionary for task description
        """
        timestamp = datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(content, dict):
            formatted_content = self._format_task_description(content)
        else:
            formatted_content = content

        self.report.append(f"{header} \n{timestamp}\n\n{formatted_content}\n")
        with open(self.report_path, "w") as f:
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

        # If competition URL is provided and scraping not skipped, scrape the data
        if self.competition_url and not self.skip_scraping:
            logger.info(f"Scraping competition data from {self.competition_url}")
            scrape_result = asyncio.run(self.scraper.scrape(self.competition_url))
            if any(val is None for val in scrape_result.values()):
                raise RuntimeError(f"Failed to scrape competition data: {scrape_result}")
            logger.info("Successfully scraped competition data")

            # Verify required files exist after scraping
            if not (self.working_dir / "overview.md").exists():
                raise FileNotFoundError("overview.md not found in working directory")
            if not (self.working_dir / "data_dictionary.xlsx").exists():
                raise FileNotFoundError("data_dictionary.xlsx not found in working directory")
            if not self.data_dir.exists():
                raise FileNotFoundError("dataset directory not found in working directory")

        # Load and analyze problem description
        self.problem_desc = read_problem_description(self.working_dir / "overview.md")
        self.data_dictionary = read_data_dictionary(self.working_dir / "data_dictionary.xlsx")
        self.task_description = self.plan_tasks()

        # Update agent configurations with task description and data dictionary
        self._update_agent_configs(self.task_description, self.data_dictionary)

        # Add development plan to report
        self._add_to_report("## Development Plan", self.task_description)

        # Process data
        self.process_data()

        # Engineer features
        self.engineer_features()

        # Build and train model
        self.build_model()

        # Make predictions
        self.generate_submission()

        logger.info("Model development pipeline completed")
