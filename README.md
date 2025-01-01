# Pond Agent

A Python package for building AI agents to solve [Pond's AI model competitions](https://cryptopond.xyz/modelFactory/list). This package is mainly for educational purposes and intended to show you how AI agents work under the hood. Hence, it is designed to be lightweight and doesn't use those popular agent frameworks. Moreover, it is also intended to be a good starting point for those who are not sure how to start with the competition. Lastly, you are more than welcome to build on top of this package to crack the competitions or build your own agent.

Currently, the package only includes the competition agent. More agents might be added in the future and you are invited to build them together!

**Note**:
* Because LLMs (e.g., GPT-4o) are non-deterministic, results may vary each time they run. They can also generate incorrect or non-executable code. While a bug-fixing agent is included, it may not catch every issue. If you encounter errors, please re-run the notebook/script. If problems persist, open an [issue](https://github.com/Pond-International/pond-agent/issues) on GitHub.
* This package is still under development and is not intended for production use. Please proceed at your own risk.
* There is no guarantee it will solve all ML problems or competitions. At present, only binary classification and regression tasks have been tested.

## Table of Contents
- [Features](#features)
- [What's Next](#whats-next)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Development](#development)

## Features
- End-to-end agent for solving [Pond's AI model competitions](https://cryptopond.xyz/modelFactory/list). Currently, the agent supports supervised learning tasks but not recommendation tasks. 
- Automatic competition data scraping - just provide the competition URL and the agent will download all necessary files
- Minimalistic agent implementation using OpenAI's API directly. This way you can easily understand how the agent works and debug if things go wrong: use LLM to get instructions on how to solve a problem, use LLM to turn the instructions into code, and call tools such as Python to execute the code. However, this simplistic approach means it doesn't support many advanced features, such as memory, general tool usage, and complex workflows. But once you grasp the basics, it is easy to start with the fancier frameworks such as [LangChain](https://www.langchain.com/), [LlamaIndex](https://www.llamaindex.ai), [crewai](https://www.crewai.com/), [autogen](https://github.com/microsoft/autogen), [PydanticAI](https://ai.pydantic.dev/), just to name a few.
- Modular architecture for easy extension. The competition agent is actually a collection of agents and tools including data processor, feature engineer, model builder, etc. You can add your own agents, tools, and LLMs.

## What's Next
- Add unit tests
- Add GitHub actions for CI/CD
- Add more competition examples
- Support more LLMs
- Support more ML tasks
- Develop a whole new agent 

## Installation

```bash
pip install pond-agent
```

### Browser Setup
The package uses Playwright for web scraping, which requires Chrome browser. After installing the package, run:
```bash
# Install browser
playwright install chromium
```
If you're on Linux, you might need to install additional dependencies.

## Usage

Check out the [Examples](#Examples) below for quick start.

There are two ways to set up the competition data:

### Option 1: Automatic Download (Recommended)
Simply provide the competition URL when creating the agent:

```python
from pond_agent import CompetitionAgent

# Initialize agent with competition URL
agent = CompetitionAgent(
    working_dir="path/to/working/directory",
    competition_url="https://cryptopond.xyz/modelFactory/detail/2",
    llm_provider="openai",
    model_name="gpt-4o"
)

# Run the pipeline
agent.run()
```

The agent will automatically download:
- Competition overview (`overview.md`)
- Data dictionary (`data_dictionary.xlsx`)
- Dataset files in the `dataset/` directory

### Option 2: Manual Setup
You can also manually set up the required files in your working directory:
1. `overview.md`: Description of the competition in markdown format. Copy from the Overview tab on the competition webpage.
2. `data_dictionary.xlsx`: Dataset description Excel file. Download from the Dataset tab.
3. `dataset/`: Directory containing data in parquet format. Download and unzip from the Dataset tab.

Then initialize the agent without a competition URL:
```python
agent = CompetitionAgent(
    working_dir="path/to/working/directory",
    llm_provider="openai",
    model_name="gpt-4o"
)
```

**Note**: If all required files already exist in your working directory, the agent will skip downloading even if `competition_url` is provided.

### OpenAI API Setup
Create a `.env` file in your project directory with your OpenAI API key:
```env
OPENAI_API_KEY=your-api-key-here
```

### Output Structure
When you run the agent, it will:
1. Create an `output/run_YYYYMMDD_HHMMSS/` directory containing:
   - `processed_data/`: Clean and preprocessed datasets
   - `feature_data/`: Data with engineered features
   - `models/`: Trained models
   - `scripts/`: Generated Python scripts for each step
   - `report.md`: Detailed report from each step
   - `submission.csv`: Final predictions in the required format
2. Create daily rotating logs in the `logs` directory:
   - `YYYYMMDD.log`: Current day's execution logs
   - Archived logs are automatically rotated with timestamp suffixes

The agent will provide detailed logs of its progress in both the terminal and the `logs` directory, documenting each step from data processing to submission generation.

## Examples

Check out the [examples](examples/) directory for:
- Complete end-to-end competition solutions
- Sample project structure and configuration
- Examples of execution logs and outputs

Available examples:
1. [Sybil Address Detection](examples/sybil_address/): End-to-end pipeline for the [sybil addresses detection competition](https://cryptopond.xyz/modelFactory/detail/2).

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

4. Install browser for web scraping:
```bash
# Install browser
playwright install chromium
```
If you're on Linux, you might need to install additional dependencies.

### Project Structure
```
pond-agent/
├── src/
│   └── pond_agent/
│       ├── competition/          # Competition-specific implementations
│       │   ├── agent.py          # Main competition agent that plan the tasks and orchestrates the other agents
│       │   ├── base.py           # Base classes and interfaces
│       │   ├── bug_fixer.py      # Bug fixing agent
│       │   ├── data_processor.py # Data processing agent
│       │   ├── feature_engineer.py# Feature engineering agent
│       │   ├── model_builder.py  # Model building agent
│       │   ├── prompts/          # LLM prompt templates
│       │   ├── scraper.py        # Competition data scraper
│       │   ├── submission_generator.py # Submission file handling
│       │   └── utils.py          # Utility functions
│       ├── llm.py               # LLM integration and handling
│       ├── logging_config.py    # Logging configuration
│       └── tools.py             # Tools for the agents to use
├── examples/         # Example usage
├── tests/            # Test files
├── pyproject.toml    # Project configuration and dependencies
├── LICENSE           # License information
└── README.md         # Project documentation
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
def test_MyAgent_initialization():
    agent = MyAgent()
    assert agent is not None
```

### Publishing to PyPI

1. Update version number in `pyproject.toml`:
```toml
[project]
name = "pond-agent"
version = "x.y.z"  # Update this version
```

2. Install build and publish tools:
```bash
pip install --upgrade build twine
```

3. Build the package:
```bash
# Clean previous builds
rm -rf dist/
rm -rf build/

# Build new distribution
python -m build
```

4. Test the package on TestPyPI (recommended):
```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pond-agent
```

5. Publish to PyPI:
```bash
# Upload to PyPI
python -m twine upload dist/*
```

You'll need to provide your PyPI credentials when uploading. You can store them in `~/.pypirc` to avoid typing them each time:
```ini
[pypi]
username = __token__
password = your-pypi-token

[testpypi]
username = __token__
password = your-testpypi-token
```

Make sure to:
- Update the version number following [semantic versioning](https://semver.org/)
- Test the package on TestPyPI before publishing to PyPI
- Keep your PyPI tokens secure and never commit them to version control

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