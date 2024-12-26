"""Bug fixer agent for Python code."""

from typing import Optional

from .base import BaseAgent
from ..llm import LLMClient


class BugFixer(BaseAgent):
    """Bug fixer agent for Python code."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize bug fixer agent.

        Args:
            llm_client: LLM client for getting fixes
        """
        super().__init__()
        self.llm_client = llm_client

    def fix_bug(self, code: str, error: str) -> Optional[str]:
        """Fix bug in code based on error message.

        Args:
            code: Code containing the bug
            error: Error message from running the code

        Returns:
            Fixed code if successful, None if unable to fix
        """
        context = {
            "code": code,
            "error": error,
        }
        sys_prompt = self.load_prompt_template("bug_fixer_system.txt")
        user_prompt = self.load_prompt_template("bug_fixer_user.txt", context)
        response = self.llm_client.get_response(
            user_prompt, sys_prompt, json_response=False
        )
        if response:
            response = response.strip().strip("`").removeprefix("python")
        return response if response else None
