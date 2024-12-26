
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# Define file paths
test_addresses_path = '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/test_addresses.parquet'
dex_swaps_path = '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/dex_swaps.parquet'
transactions_path = '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/transactions.parquet'
token_transfers_path = '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/token_transfers.parquet'
model_path = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/models/random_forest_model.joblib'
submission_output_path = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/submission.csv'

# Load datasets
print("Loading test dataset...")
test_addresses = pd.read_parquet(test_addresses_path)
dex_swaps = pd.read_parquet(dex_swaps_path)
transactions = pd.read_parquet(transactions_path)
token_transfers = pd.read_parquet(token_transfers_path)

# Feature engineering for test set
print("Calculating features for test set...")

# Transactions features
transactions_features = transactions.groupby('FROM_ADDRESS').agg(
    total_tx_count=('BLOCK_NUMBER', 'count'),
    total_eth_sent=('VALUE', 'sum'),
    avg_tx_value=('VALUE', 'mean')
).reset_index().rename(columns={'FROM_ADDRESS': 'ADDRESS'})

# Token transfers features
token_transfers_features = token_transfers.groupby('FROM_ADDRESS').agg(
    total_token_transfers=('BLOCK_NUMBER', 'count'),
    total_usd_value=('RAW_AMOUNT', 'sum'),
    avg_token_transfer_value=('RAW_AMOUNT', 'mean')
).reset_index().rename(columns={'FROM_ADDRESS': 'ADDRESS'})

# DEX swaps features
dex_swaps_features = dex_swaps.groupby('ORIGIN_FROM_ADDRESS').agg(
    total_swaps=('BLOCK_NUMBER', 'count'),
    total_usd_value_swaps=('AMOUNT_IN_USD', 'sum'),
    avg_swap_value=('AMOUNT_IN_USD', 'mean')
).reset_index().rename(columns={'ORIGIN_FROM_ADDRESS': 'ADDRESS'})

# Merge all features with test addresses
print("Merging features with test addresses...")
features = test_addresses.merge(transactions_features, on='ADDRESS', how='left')
features = features.merge(token_transfers_features, on='ADDRESS', how='left')
features = features.merge(dex_swaps_features, on='ADDRESS', how='left')

# Fill NaN values with 0
features.fillna(0, inplace=True)

# Normalize features
print("Normalizing features...")
scaler = MinMaxScaler()
features[['total_tx_count', 'total_eth_sent', 'avg_tx_value',
          'total_token_transfers', 'total_usd_value', 'avg_token_transfer_value',
          'total_swaps', 'total_usd_value_swaps', 'avg_swap_value']] = scaler.fit_transform(
    features[['total_tx_count', 'total_eth_sent', 'avg_tx_value',
              'total_token_transfers', 'total_usd_value', 'avg_token_transfer_value',
              'total_swaps', 'total_usd_value_swaps', 'avg_swap_value']])

# Load the trained model
print("Loading the trained model...")
rf_model = joblib.load(model_path)

# Predict using the model
print("Generating predictions...")
features['PRED'] = rf_model.predict(features[['total_tx_count', 'total_eth_sent', 'avg_tx_value',
                                               'total_token_transfers', 'total_usd_value', 'avg_token_transfer_value',
                                               'total_swaps', 'total_usd_value_swaps', 'avg_swap_value']])

# Ensure all test addresses are included in the submission
print("Ensuring all test addresses are included in the submission...")
submission = test_addresses[['ADDRESS']].merge(features[['ADDRESS', 'PRED']], on='ADDRESS', how='left')
submission['PRED'].fillna(0, inplace=True)

# Save the submission file
print("Saving the submission file...")
os.makedirs(os.path.dirname(submission_output_path), exist_ok=True)
submission.to_csv(submission_output_path, index=False)

print("Submission file saved to:", submission_output_path)
