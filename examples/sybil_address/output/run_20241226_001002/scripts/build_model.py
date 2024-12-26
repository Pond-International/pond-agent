
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

# Load the training data
train_data_path = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/feature_data/train.parquet'
print("Loading training data from:", train_data_path)
train_df = pd.read_parquet(train_data_path)

# Define feature columns and target column
feature_columns = [
    'total_tx_count', 'total_eth_sent', 'avg_tx_value', 
    'total_token_transfers', 'total_usd_value', 
    'avg_token_transfer_value', 'total_swaps', 
    'total_usd_value_swaps', 'avg_swap_value'
]
target_column = 'LABEL'

# Prepare the data
X = train_df[feature_columns]
y = train_df[target_column].astype('int')

# Split the data into training and validation sets
print("Splitting data into training and validation sets...")
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the Random Forest Classifier
print("Initializing the Random Forest Classifier...")
rf_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)

# Train the model
print("Training the model...")
rf_model.fit(X_train, y_train)

# Validate the model
print("Validating the model...")
y_pred = rf_model.predict(X_val)
print("Classification Report:\n", classification_report(y_val, y_pred))

# Save the trained model
model_output_dir = '/home/ubuntu/pond-agent/examples/sybil_address/output/run_20241226_001002/models'
os.makedirs(model_output_dir, exist_ok=True)
model_output_path = os.path.join(model_output_dir, 'random_forest_model.joblib')
print("Saving the model to:", model_output_path)
joblib.dump(rf_model, model_output_path)

print("Model training and saving completed.")
