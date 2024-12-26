# Sybil Address Prediction Example

This example demonstrates how to use the Competition Agent to solve the [Sybil Addresses Prediction competition](https://cryptopond.xyz/modelFactory/detail/2). It shows a complete end-to-end pipeline from data processing to submission.

## Directory Structure
```
sybil_address/
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

1. Set up your OpenAI API key in `.env`:
```env
OPENAI_API_KEY=your-api-key-here
```

2. Download the competition data:
   - Visit the [competition page](https://cryptopond.xyz/modelFactory/detail/2)
   - Download and unzip the dataset files into the `input/dataset/` directory

3. Place the files in the correct locations:
   - Copy text on Overview tab to `input/overview.md`, which is already done in this example.
   - Download data dictionary to `input/data_dictionary.xlsx`, which is already done in this example.

4. Run the example:
   - Open `auto_ml.ipynb` in Jupyter
   - Follow the step-by-step instructions
   - Watch the agent build and train your model

## What to Expect

The notebook will guide you through:
1. Config logging
2. Create the competition agent
3. Run the whole pipeline

Check the `output/` directory for generated artifacts and the `logs/` directory for detailed execution logs.

**Note**: As LLMs (e.g., GPT-4o) are not deterministic, the results may vary from run to run. It might even generate wrong code which cannot be executed. A bug fixing agent is included but it is not guaranteed to fix all bugs. If any error occurs, please restart the notebook and run it again. If you encounter any issues, please report them as [GitHub Issues](https://github.com/Pond-International/pond-agent/issues).
