import pandas as pd

def load_and_preprocess_data(file_path):
    # Load dataset
    df = pd.read_csv(file_path)
    
    # Handle missing values
    df = df.dropna()
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Standardize column names
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Define appliance columns for training
    appliance_cols = ['fan', 'refrigerator', 'airconditioner', 'television', 'monitor', 'motorpump']
    
    # Standardize names for units and bill
    rename_map = {
        'monthlyhours': 'units_consumed',
        'electricitybill': 'bill_amount',
        'tariffrate': 'tariff'
    }
    
    # Rename only if the source column exists
    rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    
    # Ensure all required columns exist (appliance counts, units, tariff, bill, city)
    required_cols = appliance_cols + ['city', 'units_consumed', 'tariff', 'bill_amount']
    if 'month' in df.columns:
        required_cols.append('month')
        
    # Filter to only keep necessary columns that exist
    available_cols = [col for col in required_cols if col in df.columns]
    
    return df[available_cols]

if __name__ == "__main__":
    import os
    file_path = os.path.join('dataset', 'electricity_bill_dataset.csv')
    if os.path.exists(file_path):
        df = load_and_preprocess_data(file_path)
        print("Preprocessed DataFrame Columns:", df.columns.tolist())
        print(df.head())
    else:
        print(f"File not found: {file_path}")
