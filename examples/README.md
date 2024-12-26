# Pond Agent Examples

This directory contains example notebooks and datasets demonstrating how to use the Pond Agent package.

## Directory Structure

```
examples/
├── data/                    # Example datasets
│   └── README.md           # Dataset descriptions and sources
├── notebooks/              # Jupyter notebooks with examples
│   ├── 01_quickstart.ipynb
│   └── 02_custom_agent.ipynb
└── README.md              # This file
```

## Getting Started

1. Install dependencies:
```bash
pip install -e ".[dev]"
pip install jupyter
```

2. Start Jupyter:
```bash
jupyter notebook
```

3. Navigate to the `notebooks` directory and open the desired notebook.

## Examples

### 1. Quickstart
[01_quickstart.ipynb](notebooks/01_quickstart.ipynb) - Basic usage of CompetitionAgent with a simple classification task.

### 2. Custom Agent
[02_custom_agent.ipynb](notebooks/02_custom_agent.ipynb) - How to create and customize your own competition agent.
