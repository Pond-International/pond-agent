# Examples

This directory contains example projects demonstrating how to use the Competition Agent to solve the [Sybil Addresses Prediction competition](https://cryptopond.xyz/modelFactory/detail/2). Each example is a complete end-to-end solution for a specific competition.

## Available Examples

### [Sybil Address Prediction](sybil_address/)
A complete example showing how to use the Competition Agent to predict sybil addresses in blockchain data. This example demonstrates:

## Example Structure
Each example follows a consistent structure:
```
example_name/
├── input/                 # Competition materials
│   ├── overview.md        # Competition description
│   ├── data_dictionary.xlsx # Dataset documentation
│   └── dataset/           # Competition datasets
├── output/                # Generated outputs
│   └── run_YYYYMMDD_HHMMSS/ # Timestamped run results
├── logs/                  # Execution logs
├── .env                   # OpenAI API configuration
└── auto_ml.ipynb         # Step-by-step tutorial notebook
```

## Getting Started
1. Choose an example that matches your interest
2. Follow the README.md in that example's directory
3. Make sure to set up your OpenAI API key in the example's `.env` file

**Note**: Examples use GPT-4o by default. Results may vary between runs due to the non-deterministic nature of LLMs. If you encounter any issues, please report them as [GitHub Issues](https://github.com/Pond-International/pond-agent/issues).
