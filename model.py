from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import pandas as pd
import numpy as np

def train_model(df):
    # Features for the model:
    # 1. Units consumed (the primary driver)
    # 2. Tariff (city-specific cost)
    # 3. INTERACTION: Units * Tariff (This is the ACTUAL formula for a bill)
    # 4. Appliance counts (to capture specific usage patterns)
    
    appliance_cols = ['fan', 'refrigerator', 'airconditioner', 'television', 'monitor', 'motorpump']
    # Filter available appliance columns
    app_cols = [col for col in appliance_cols if col in df.columns]
    
    df_train = df.copy()
    # Add interaction term: This is crucial for accuracy as Bill = Units * Tariff
    df_train['units_x_tariff'] = df_train['units_consumed'] * df_train['tariff']
    
    X = df_train[['units_consumed', 'tariff', 'units_x_tariff'] + app_cols]
    y = df_train['bill_amount']
    
    # Using LinearRegression with an interaction term is extremely accurate for bills
    # and extrapolates perfectly for new inputs.
    model = LinearRegression(fit_intercept=False)
    model.fit(X, y)
    
    # Calculate R² score
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    return model, r2

def predict_bill(model, units, tariff, appliances_data):
    # Map UI dictionary to model features
    
    feature_data = {
        'units_consumed': units,
        'tariff': tariff,
        'units_x_tariff': units * tariff, # Include the interaction term for prediction
        'fan': appliances_data.get('fan', {}).get('count', 0),
        'refrigerator': appliances_data.get('refrigerator', {}).get('count', 0),
        'airconditioner': appliances_data.get('ac', {}).get('count', 0),
        'television': appliances_data.get('tv', {}).get('count', 0),
        'monitor': appliances_data.get('monitor', {}).get('count', 0),
        'motorpump': appliances_data.get('motor', {}).get('count', 0)
    }
    
    # Ensure we use the exact features the model expects in the correct order
    try:
        features = model.feature_names_in_
    except AttributeError:
        # Fallback if model doesn't have feature_names_in_
        features = ['units_consumed', 'tariff', 'units_x_tariff', 'fan', 'refrigerator', 'airconditioner', 'television', 'monitor', 'motorpump']
    
    # Create input DataFrame with correct feature names and order
    input_df = pd.DataFrame([feature_data], columns=features)
    
    # Fill any missing columns with 0
    input_df = input_df.fillna(0)
    
    # If units consumed is 0, return 0 to avoid baseline intercept bias
    if units == 0:
        return 0.0
    
    prediction = model.predict(input_df)
    
    # Ensure prediction doesn't go below 0
    return max(0, prediction[0])
