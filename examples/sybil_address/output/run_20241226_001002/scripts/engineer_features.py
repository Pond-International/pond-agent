
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

# Define file paths
train_addresses_path = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/processed_data/TRAIN_ADDRESSES.parquet'
dex_swaps_path = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/processed_data/DEX_SWAPS.parquet'
transactions_path = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/processed_data/TRANSACTIONS.parquet'
token_transfers_path = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/processed_data/TOKEN_TRANSFERS.parquet'
output_path = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/feature_data/train.parquet'

# Load datasets
print("Loading datasets...")
train_addresses = pd.read_parquet(train_addresses_path)
dex_swaps = pd.read_parquet(dex_swaps_path)
transactions = pd.read_parquet(transactions_path)
token_transfers = pd.read_parquet(token_transfers_path)

# Feature engineering
print("Calculating features...")

# Transactions features
transactions_features = transactions.groupby('FROM_ADDRESS').agg(
    total_tx_count=('total_tx_count', 'sum'),
    total_eth_sent=('total_eth_sent', 'sum'),
    avg_tx_value=('avg_tx_value', 'mean')
).reset_index().rename(columns={'FROM_ADDRESS': 'ADDRESS'})

# Token transfers features
token_transfers_features = token_transfers.groupby('FROM_ADDRESS').agg(
    total_token_transfers=('total_token_transfers', 'sum'),
    total_usd_value=('total_usd_value', 'sum'),
    avg_token_transfer_value=('avg_token_transfer_value', 'mean')
).reset_index().rename(columns={'FROM_ADDRESS': 'ADDRESS'})

# DEX swaps features
dex_swaps_features = dex_swaps.groupby('ORIGIN_FROM_ADDRESS').agg(
    total_swaps=('total_swaps', 'sum'),
    total_usd_value_swaps=('total_usd_value_swaps', 'sum'),
    avg_swap_value=('avg_swap_value', 'mean')
).reset_index().rename(columns={'ORIGIN_FROM_ADDRESS': 'ADDRESS'})

# Merge all features with train addresses
print("Merging features with training labels...")
features = train_addresses.merge(transactions_features, on='ADDRESS', how='left')
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

# Save the feature table
print("Saving feature table...")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
features.to_parquet(output_path)

print("Feature engineering completed and saved to:", output_path)
