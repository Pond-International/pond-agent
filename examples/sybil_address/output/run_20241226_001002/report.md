# Model Development Report 
2024-12-26 00:10:10




## Development Plan 
2024-12-26 00:10:10

{'summary': "The task is a supervised classification problem where the goal is to predict whether a given blockchain address is associated with Sybil attacks. The labels for training are found in the 'LABEL' column of the 'TRAIN_ADDRESSES' table.", 'preprocessing': {'tables': {'TRAIN_ADDRESSES': {'columns': ['ADDRESS', 'LABEL'], 'actions': "Load and use as the primary dataset for training, ensuring that the 'LABEL' column is used as the target variable."}, 'TRANSACTIONS': {'columns': ['FROM_ADDRESS', 'TO_ADDRESS', 'VALUE', 'TX_HASH'], 'actions': 'Aggregate transaction data by address to create features such as total transaction count, total ETH sent/received, and average transaction value.'}, 'TOKEN_TRANSFERS': {'columns': ['FROM_ADDRESS', 'TO_ADDRESS', 'AMOUNT_PRECISION', 'AMOUNT_USD'], 'actions': 'Aggregate token transfer data by address to create features such as total token transfers, total USD value of tokens transferred, and average token transfer value.'}, 'DEX_SWAPS': {'columns': ['ORIGIN_FROM_ADDRESS', 'TX_TO', 'AMOUNT_IN', 'AMOUNT_OUT', 'AMOUNT_IN_USD', 'AMOUNT_OUT_USD'], 'actions': 'Aggregate DEX swap data by address to create features such as total swaps, total USD value of swaps, and average swap value.'}}}, 'feature_engineering': {'steps': ["For each address, calculate the total number of transactions, total ETH sent, and total ETH received from the 'TRANSACTIONS' table.", "For each address, calculate the total number of token transfers, total token amount transferred, and total USD value of tokens transferred from the 'TOKEN_TRANSFERS' table.", "For each address, calculate the total number of DEX swaps, total amount of tokens swapped in and out, and total USD value of swaps from the 'DEX_SWAPS' table.", 'Normalize or scale features as necessary to ensure they are on a similar scale for modeling.']}, 'modeling': {'model_type': 'Random Forest Classifier', 'hyperparameters': {'n_estimators': 100, 'max_depth': 10, 'random_state': 42}, 'actions': "Train the model using the engineered features and the 'LABEL' column from the 'TRAIN_ADDRESSES' table as the target variable."}, 'submission': {'instructions': "Generate predictions for the 'ADDRESS' column in the 'TEST_ADDRESSES' table using the trained model. Create a CSV file with two columns: 'ADDRESS' and 'PRED', where 'PRED' contains the predicted labels (0 or 1) for each address. Ensure all addresses in the test set are included in the submission."}}


## Data Processing 
2024-12-26 00:10:44

Processed data:

- **TRAIN_ADDRESSES**
  - Shape: (27320, 2)
  - Columns:
    - ADDRESS: String
    - LABEL: Decimal(precision=1, scale=0)
- **DEX_SWAPS**
  - Shape: (5614, 4)
  - Columns:
    - ORIGIN_FROM_ADDRESS: String
    - total_swaps: Int64
    - total_usd_value_swaps: Float64
    - avg_swap_value: Float64
- **TRANSACTIONS**
  - Shape: (87953, 4)
  - Columns:
    - FROM_ADDRESS: String
    - total_tx_count: Int64
    - total_eth_sent: Float64
    - avg_tx_value: Float64
- **TOKEN_TRANSFERS**
  - Shape: (62594, 4)
  - Columns:
    - FROM_ADDRESS: String
    - total_token_transfers: Int64
    - total_usd_value: Float64
    - avg_token_transfer_value: Float64


## Feature Engineering 
2024-12-26 00:10:55

Created feature matrix:

- **TRAIN**
  - Shape: (27320, 11)
  - Columns:
    - ADDRESS: String
    - LABEL: Decimal(precision=1, scale=0)
    - total_tx_count: Float64
    - total_eth_sent: Float64
    - avg_tx_value: Float64
    - total_token_transfers: Float64
    - total_usd_value: Float64
    - avg_token_transfer_value: Float64
    - total_swaps: Float64
    - total_usd_value_swaps: Float64
    - avg_swap_value: Float64


## Model 
2024-12-26 00:11:21

Model report not implemented yet


## Submission File 
2024-12-26 00:11:49

Shape: (4822, 2)  
Preview:  
| ADDRESS                                    |   PRED |
|:-------------------------------------------|-------:|
| 0x8c68ec7995b29c6b33006e91e5993ba3fe5a1635 |      1 |
| 0xc47aec3468fe6ac9b5cf169e6d4f5f39def92220 |      0 |
| 0xe4d6c505b202385b214e9d050403d8da4b60ec02 |      1 |
| 0x978e91547652d2ad3a63cf9e7873fedfc73bf66f |      0 |
| 0x43aae3d56e5302a564ac250a0ad0799e5b6b3e72 |      0 |
