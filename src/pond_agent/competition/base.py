"""Base class for AutoML agent."""

import importlib.resources


class BaseAgent:
    """Base class for AutoML agent."""

    def __init__(self) -> None:
        """Initialize class for AutoML agent."""

    def load_prompt_template(self, template_name: str, context: dict) -> str:
        """Load prompt template from resources."""
        template = importlib.resources.read_text(
            "pond_agent.competition.prompts", template_name
        )
        return template.format(**context)