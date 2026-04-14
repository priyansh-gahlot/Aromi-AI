import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from preprocess import load_and_preprocess_data
from utils import calculate_tariff_mapping, calculate_total_units, get_appliance_contribution
from model import train_model, predict_bill

# --- Page Configuration ---
st.set_page_config(
    page_title="Electricity Consumption & Bill Predictor",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- Custom Professional Dark Styling ---
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Custom Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
    }
    
    /* Professional Metric Cards - Dark Mode */
    [data-testid="stMetric"] {
        background-color: #1e293b !important;
        padding: 24px !important;
        border-radius: 16px !important;
        border: 2px solid #334155 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #3b82f6 !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
    }
    
    [data-testid="stMetricValue"] > div {
        color: #3b82f6 !important; /* Primary blue for values */
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] > div > p {
        color: #94a3b8 !important; /* Slate for labels */
        font-weight: 600 !important;
        font-size: 1rem !important;
        text-transform: uppercase;
    }
    
    /* Input field styling */
    .stNumberInput input {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    /* Info box styling */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        background-color: #1e3a8a !important; /* Dark blue alert */
        color: #bfdbfe !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #3b82f6 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
    }
    
    /* Sidebar Section Divider */
    .sidebar-divider {
        margin: 1.5rem 0;
        border-top: 1px solid #334155;
    }

    /* DataFrame styling for Dark Mode */
    .stDataFrame {
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border-bottom: 1px solid #334155 !important;
    }
    
    /* Custom Button Styling for +/- */
    div.stButton > button:first-child {
        background-color: #334155;
        color: #f8fafc;
        border: 1px solid #475569;
        height: 35px;
        padding: 0;
        font-size: 1.2rem;
    }
    div.stButton > button:hover {
        border-color: #3b82f6 !important;
        color: #3b82f6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Data Loading & Setup ---
@st.cache_data
def get_data():
    file_path = os.path.join('dataset', 'electricity_bill_dataset.csv')
    if not os.path.exists(file_path):
        return None
    return load_and_preprocess_data(file_path)

df = get_data()

if df is None:
    st.error("🚨 Dataset not found. Please ensure the 'dataset/electricity_bill_dataset.csv' file exists.")
    st.stop()

city_tariff_map = calculate_tariff_mapping(df)
model, r2_score_val = train_model(df)

# --- Sidebar Content ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/lightning-bolt.png", width=60)
    st.title("Settings")
    
    st.markdown("### 📍 Location")
    selected_city = st.selectbox("Select City", sorted(list(city_tariff_map.keys())), help="The tariff rate is determined based on the selected city.")
    tariff = city_tariff_map[selected_city]
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    st.markdown("### 🔌 Appliance Usage")
    st.caption("Enter the number of units and average daily usage hours for each appliance.")
    
    appliances = {
        'fan': {'count': 0, 'hours': 0, 'icon': '🌀'},
        'ac': {'count': 0, 'hours': 0, 'icon': '❄️'},
        'light': {'count': 0, 'hours': 0, 'icon': '💡'},
        'tv': {'count': 0, 'hours': 0, 'icon': '📺'},
        'motor': {'count': 0, 'hours': 0, 'icon': '🚿'},
        'refrigerator': {'count': 0, 'hours': 0, 'icon': '🍦'},
        'monitor': {'count': 0, 'hours': 0, 'icon': '🖥️'}
    }

    app_labels = {
        'fan': 'Fans',
        'ac': 'Air Conditioners',
        'light': 'Lights',
        'tv': 'Televisions',
        'motor': 'Motors',
        'refrigerator': 'Refrigerators',
        'monitor': 'Monitors'
    }

    # Initialize session state for counts if not already present
    for app_key in app_labels.keys():
        if f"count_{app_key}" not in st.session_state:
            st.session_state[f"count_{app_key}"] = 0

    # Group appliances into columns for a more compact sidebar
    for app_key, label in app_labels.items():
        with st.expander(f"{appliances[app_key]['icon']} {label}", expanded=False):
            st.markdown(f"**{label} Count**")
            # Custom +/- buttons for Count
            btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
            with btn_col1:
                if st.button("➖", key=f"minus_{app_key}", use_container_width=True):
                    if st.session_state[f"count_{app_key}"] > 0:
                        st.session_state[f"count_{app_key}"] -= 1
                        st.rerun()
            with btn_col2:
                st.markdown(f"<h3 style='text-align:center; margin:0; color:#3b82f6;'>{st.session_state[f'count_{app_key}']}</h3>", unsafe_allow_html=True)
            with btn_col3:
                if st.button("➕", key=f"plus_{app_key}", use_container_width=True):
                    st.session_state[f"count_{app_key}"] += 1
                    st.rerun()
            
            # Map count from session state to the dictionary
            appliances[app_key]['count'] = st.session_state[f"count_{app_key}"]
            
            # Usage Hours input
            st.markdown(f"**Daily Usage Hours**")
            appliances[app_key]['hours'] = st.number_input(
                f"Hrs/Day for {label}", 
                min_value=0.0, 
                max_value=24.0, 
                step=0.5, 
                key=f"side_{app_key}_hrs", 
                label_visibility="collapsed"
            )

# --- Main Dashboard ---
st.markdown(f"<h1>Electricity Consumption Analysis <span style='color:#3b82f6;'>{selected_city}</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#94a3b8; font-size:1.1rem; margin-bottom:2rem;'>Estimate your monthly electricity bill using advanced machine learning.</p>", unsafe_allow_html=True)

# Calculation Logic
daily_units = calculate_total_units(appliances)
monthly_units = daily_units * 30
estimated_bill = predict_bill(model, monthly_units, tariff, appliances)

# Key Metrics Row
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Predicted Monthly Bill", value=f"₹{estimated_bill:,.2f}")
with m2:
    st.metric(label="Est. Monthly Units", value=f"{monthly_units:,.1f} kWh")
with m3:
    st.metric(label="City Avg Tariff", value=f"₹{tariff:.2f}/kWh")

st.markdown('<br>', unsafe_allow_html=True)

# Content Tabs
tab_analysis, tab_historical, tab_model = st.tabs(["📊 Your Consumption Analysis", "🏛️ Regional Benchmarks", "🧠 Prediction Engine"])

with tab_analysis:
    st.markdown("### 🏠 Usage Breakdown")
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        contributions = get_appliance_contribution(appliances)
        contrib_df = pd.DataFrame(list(contributions.items()), columns=['Appliance', 'Units'])
        
        # Filter out zero contributions to make the chart cleaner
        active_contrib = contrib_df[contrib_df['Units'] > 0].copy()
        
        if not active_contrib.empty:
            # Capitalize appliance names for better presentation
            active_contrib['Appliance'] = active_contrib['Appliance'].str.capitalize()
            
            fig_pie = px.pie(
                active_contrib, 
                names='Appliance', 
                values='Units',
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel,
                template="plotly_dark"
            )
            
            # Simplified labels: only show percentage and name on the slices
            fig_pie.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                pull=[0.05] * len(active_contrib) # Slightly separate slices
            )
            
            fig_pie.update_layout(
                showlegend=True, 
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(t=20, b=80, l=0, r=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="Consumption Share by Appliance", x=0.5, xanchor='center')
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("💡 Adjust appliance settings in the sidebar to see your usage breakdown.")
            
    with col_right:
        if contrib_df['Units'].sum() > 0:
            st.markdown("#### Top Power Consumers")
            contrib_df = contrib_df.sort_values(by='Units', ascending=False)
            contrib_df['Monthly (kWh)'] = contrib_df['Units'] * 30
            st.dataframe(
                contrib_df.style.background_gradient(subset=['Units'], cmap='Blues'),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.empty()

with tab_historical:
    st.markdown("### 🏙️ How does your city compare?")
    c1, c2 = st.columns(2)
    
    with c1:
        city_avg = df.groupby('city')['units_consumed'].mean().sort_values(ascending=False).reset_index()
        fig_bar = px.bar(
            city_avg, x='city', y='units_consumed',
            title="Avg Monthly Units per City",
            color='units_consumed',
            color_continuous_scale='Blues',
            labels={'units_consumed': 'Units (kWh)', 'city': 'City'},
            template="plotly_dark"
        )
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#334155')
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c2:
        fig_box = px.box(
            df, x='city', y='bill_amount',
            title="Bill Amount Distribution by City",
            color='city',
            labels={'bill_amount': 'Bill (₹)', 'city': 'City'},
            template="plotly_dark"
        )
        fig_box.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=True, gridcolor='#334155')
        )
        st.plotly_chart(fig_box, use_container_width=True)

with tab_model:
    st.markdown("### 🧠 Model Performance & Methodology")
    st.markdown(f"""
    The system utilizes a **Linear Regression** model trained on historical regional data.
    
    - **Model Accuracy (R²):** `{r2_score_val:.4f}`
    - **Features Used:** Monthly Consumption, City Tariff, and Individual Appliance Counts.
    
    This model provides a linear extrapolation based on the provided inputs, ensuring that your estimated bill responds dynamically to every change in usage.
    """)
    
    # Prediction Plot
    try:
        sample_df = df.sample(min(200, len(df)))
        fig_reg = px.scatter(
            sample_df, x='units_consumed', y='bill_amount',
            trendline="ols",
            title="Linear Trend: Units vs. Cost",
            labels={'units_consumed': 'Units (kWh)', 'bill_amount': 'Bill Amount (₹)'},
            opacity=0.6,
            template="plotly_dark"
        )
        fig_reg.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='#334155'),
            yaxis=dict(showgrid=True, gridcolor='#334155')
        )
        st.plotly_chart(fig_reg, use_container_width=True)
    except Exception as e:
        st.warning("Trendline visualization is currently unavailable.")
        # Fallback plot without trendline
        fig_reg = px.scatter(
            sample_df, x='units_consumed', y='bill_amount',
            title="Relationship: Units vs. Cost",
            labels={'units_consumed': 'Units (kWh)', 'bill_amount': 'Bill Amount (₹)'},
            opacity=0.6,
            template="plotly_dark"
        )
        fig_reg.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_reg, use_container_width=True)

# Footer
st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.8rem;'>Electricity Consumption Analysis System &copy; 2024</p>", unsafe_allow_html=True)
