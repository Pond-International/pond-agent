"""Pond AI Agents"""

from .logging_config import setup_logging
from .competition.agent import CompetitionAgent

__version__ = "0.1.0"
__all__ = ["setup_logging", "CompetitionAgent"]