# Pond Agent

A Python package for AI agents designed to participate in machine learning competitions.

## Features

- Competition-ready ML agents
- Modular architecture for easy extension
- Built-in competition utilities and helpers

## Installation

```bash
pip install pond-agent
```

## Quick Start

```python
from pond_agent.competition import MLAgent

agent = MLAgent()
agent.train(dataset)
predictions = agent.predict(test_data)
```

## Examples

Check out the [examples](examples/) directory for:
- Jupyter notebooks with step-by-step tutorials
- Sample datasets for testing
- Custom agent implementations

Common examples:
1. [Basic Competition Agent](examples/notebooks/01_quickstart.ipynb)
2. [Custom Agent Development](examples/notebooks/02_custom_agent.ipynb)

## Development

### Getting Started

1. Clone the repository and create a new branch:
```bash
git clone https://github.com/cryptopond/pond-agent.git
cd pond-agent
git checkout -b feature/your-feature-name
```

2. Create a virtual environment (choose one):
```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate  # Windows

# Using conda
conda create -n pond-agent python=3.11
conda activate pond-agent
```

3. Install package in development mode:
```bash
pip install -e ".[dev]"
```

### Testing

The project uses `pytest` for testing. Tests are located in the `tests/` directory.

To run tests:
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=pond_agent

# Run specific test file
pytest tests/test_agent.py
```

To add new tests:
1. Create test files in the `tests/` directory with the prefix `test_`
2. Use pytest fixtures for common setup
3. Follow the existing test structure for consistency
4. Ensure tests are atomic and independent

Example test:
```python
def test_agent_initialization():
    agent = MLAgent()
    assert agent.model is None
```

### Contributing

1. Make your changes in your feature branch
2. Add tests for new functionality
3. Ensure all tests pass and code is formatted:
```bash
pytest
ruff check .
ruff format .
```
4. Commit your changes with clear messages
5. Push to your fork and submit a Pull Request

## License

See [LICENSE](LICENSE) file for details.