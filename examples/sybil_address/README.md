# Example Datasets

This directory contains example datasets for demonstrating Pond Agent functionality.

## Dataset Structure

Each dataset should be organized in its own directory with the following structure:
```
dataset_name/
├── data/                  # Raw data files
│   ├── train.parquet
│   └── test.parquet
├── overview.md           # Problem description
└── data_dictionary.xlsx  # Column descriptions and metadata
```

## Available Datasets

### 1. House Price Prediction
Location: `house_prices/`
Type: Regression
Description: Predict house prices based on various features like size, location, and amenities.

### 2. Customer Churn
Location: `customer_churn/`
Type: Binary Classification
Description: Predict customer churn based on usage patterns and customer information.
