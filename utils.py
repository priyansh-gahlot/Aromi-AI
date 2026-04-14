import pandas as pd

def calculate_tariff_mapping(df):
    # tariff = bill_amount / units_consumed
    # Avoid division by zero
    df_copy = df.copy()
    df_copy = df_copy[df_copy['units_consumed'] > 0]
    df_copy['tariff'] = df_copy['bill_amount'] / df_copy['units_consumed']
    
    # Group by city → average tariff
    city_tariff = df_copy.groupby('city')['tariff'].mean().to_dict()
    
    return city_tariff

def calculate_total_units(appliances):
    # Power Ratings (kW):
    # Fan = 0.075, AC = 1.5, Light = 0.02, TV = 0.1, Motor = 1.0, Refrigerator = 0.2
    
    power_ratings = {
        'fan': 0.075,
        'ac': 1.5,
        'light': 0.02,
        'tv': 0.1,
        'motor': 1.0,
        'refrigerator': 0.2,
        'monitor': 0.05
    }
    
    total_units = 0
    for appliance, data in appliances.items():
        count = data.get('count', 0)
        hours = data.get('hours', 0)
        rating = power_ratings.get(appliance, 0)
        total_units += (count * hours * rating)
        
    return total_units

def get_appliance_contribution(appliances):
    power_ratings = {
        'fan': 0.075,
        'ac': 1.5,
        'light': 0.02,
        'tv': 0.1,
        'motor': 1.0,
        'refrigerator': 0.2,
        'monitor': 0.05
    }
    
    contribution = {}
    for appliance, data in appliances.items():
        count = data.get('count', 0)
        hours = data.get('hours', 0)
        rating = power_ratings.get(appliance, 0)
        contribution[appliance] = count * hours * rating
        
    return contribution
