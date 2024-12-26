
import pandas as pd
import os

# Define file paths
input_paths = {
    'TOKEN_TRANSFERS': '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/token_transfers.parquet',
    'TEST_ADDRESSES': '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/test_addresses.parquet',
    'DEX_SWAPS': '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/dex_swaps.parquet',
    'TRAIN_ADDRESSES': '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/train_addresses.parquet',
    'TRANSACTIONS': '/home/ubuntu/pond-agent/examples/sybil_address/input/dataset/transactions.parquet'
}

output_dir = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/processed_data'

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load datasets
print("Loading datasets...")
train_addresses = pd.read_parquet(input_paths['TRAIN_ADDRESSES'])
transactions = pd.read_parquet(input_paths['TRANSACTIONS'])
token_transfers = pd.read_parquet(input_paths['TOKEN_TRANSFERS'])
dex_swaps = pd.read_parquet(input_paths['DEX_SWAPS'])

# Preprocess TRAIN_ADDRESSES
print("Processing TRAIN_ADDRESSES...")
# No specific preprocessing required as per instructions

# Preprocess TRANSACTIONS
print("Processing TRANSACTIONS...")
transactions_agg = transactions.groupby('FROM_ADDRESS').agg(
    total_tx_count=('TX_HASH', 'count'),
    total_eth_sent=('VALUE', 'sum'),
    avg_tx_value=('VALUE', 'mean')
).reset_index()

# Preprocess TOKEN_TRANSFERS
print("Processing TOKEN_TRANSFERS...")
token_transfers_agg = token_transfers.groupby('FROM_ADDRESS').agg(
    total_token_transfers=('FROM_ADDRESS', 'count'),
    total_usd_value=('RAW_AMOUNT', 'sum'),  # Assuming RAW_AMOUNT is in USD
    avg_token_transfer_value=('RAW_AMOUNT', 'mean')
).reset_index()

# Preprocess DEX_SWAPS
print("Processing DEX_SWAPS...")
dex_swaps_agg = dex_swaps.groupby('ORIGIN_FROM_ADDRESS').agg(
    total_swaps=('ORIGIN_FROM_ADDRESS', 'count'),
    total_usd_value_swaps=('AMOUNT_IN_USD', 'sum'),
    avg_swap_value=('AMOUNT_IN_USD', 'mean')
).reset_index()

# Save processed data
print("Saving processed data...")
train_addresses.to_parquet(os.path.join(output_dir, 'TRAIN_ADDRESSES.parquet'))
transactions_agg.to_parquet(os.path.join(output_dir, 'TRANSACTIONS.parquet'))
token_transfers_agg.to_parquet(os.path.join(output_dir, 'TOKEN_TRANSFERS.parquet'))
dex_swaps_agg.to_parquet(os.path.join(output_dir, 'DEX_SWAPS.parquet'))

print("Data preprocessing completed.")
