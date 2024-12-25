"""Tests for the ML competition agent."""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from pond_agent.competition import MLAgent


def test_agent_initialization():
    """Test basic agent initialization."""
    agent = MLAgent()
    assert agent.model is None
    assert agent.config == {}

    model = LogisticRegression()
    config = {"test": True}
    agent = MLAgent(model=model, config=config)
    assert agent.model is model
    assert agent.config == config


def test_predict_without_model():
    """Test prediction without a trained model raises error."""
    agent = MLAgent()
    with pytest.raises(RuntimeError):
        agent.predict(pd.DataFrame())
