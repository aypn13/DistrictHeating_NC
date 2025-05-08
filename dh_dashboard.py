# district_heating_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----- Sidebar Inputs -----
st.sidebar.title("Production Planner")

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# User selects active production months
default_active = [True if i != 6 else False for i in range(12)]  # default shutdown in July
active_months = [st.sidebar.checkbox(month, value=default_active[i]) for i, month in enumerate(months)]

# Daily production input
daily_heat = st.sidebar.slider("Daily Waste Heat (MWh)", min_value=1.0, max_value=20.0, value=7.5, step=0.5)

# Contract simulation mode
contract_type = st.sidebar.selectbox("Contract Type", ["Fixed Price", "Seasonal Price", "Capacity + Energy Payment"])

# Pricing logic
if contract_type == "Fixed Price":
    price_per_mwh = st.sidebar.slider("Selling Price (€/MWh)", min_value=20, max_value=100, value=50, step=5)
    seasonal_prices = [price_per_mwh] * 12
elif contract_type == "Seasonal Price":
    seasonal_prices = [70, 65, 60, 55, 40, 30, 25, 25, 35, 50, 60, 65]  # example price curve
    price_per_mwh = 0  # Not used in calc
elif contract_type == "Capacity + Energy Payment":
    capacity_payment = st.sidebar.slider("Annual Capacity Payment (€)", 1000, 50000, 10000, step=1000)
    energy_payment = st.sidebar.slider("Energy Payment (€/MWh)", 20, 60, 35, step=5)
    seasonal_prices = [energy_payment] * 12
else:
    seasonal_prices = [0] * 12

# Optional: add storage
use_storage = st.sidebar.checkbox("Enable Thermal Storage", value=True)
storage_capacity = st.sidebar.slider("Storage Capacity (MWh)", 0, 200, 50, step=10) if use_storage else 0

# Emission factor selection based on displaced fuel type
fuel_type = st.sidebar.selectbox("Displaced Fuel Type", ["Natural Gas", "Light Oil", "Biomass"])
fuel_emission_factors = {
    "Natural Gas": 0.2,
    "Light Oil": 0.27,
    "Biomass": 0.05
}
emission_factor = fuel_emission_factors[fuel_type]

# ----- Backend Calculation -----
production = np.array([daily_heat * 30 if active else 0 for active in active_months])

# Handle storage buffer (simple logic: store 25% of previous month's output if shutdown)
delivery = production.copy()
for i in range(12):
    if production[i] == 0 and use_storage:
        previous_month = (i - 1) % 12
        delivery[i] = min(storage_capacity, 0.25 * production[previous_month])

# Simulated Vattenfall demand curve (in MWh per month)
dh_demand = np.array([400, 380, 350, 300, 200, 150, 100, 120, 200, 300, 350, 380])

# Revenue and CO2 savings
monthly_revenue = delivery * seasonal_prices
annual_revenue = np.sum(monthly_revenue)
if contract_type == "Capacity + Energy Payment":
    annual_revenue += capacity_payment

co2_saved = np.sum(delivery) * emission_factor  # based on selected fuel type

# ----- Streamlit Layout -----
st.title("Nitrocapt District Heating Dashboard")

st.subheader("1. Monthly Heat Delivery Plan")
df = pd.DataFrame({
    'Month': months,
    'Planned Production (MWh)': production,
    'Delivered to DH Network (MWh)': delivery,
    'DH Demand (MWh)': dh_demand,
    'Price (€/MWh)': seasonal_prices,
    'Monthly Revenue (€)': monthly_revenue
})
st.dataframe(df)

st.subheader("2. Revenue & Environmental Impact")
st.markdown(f"**Annual Revenue:** €{annual_revenue:,.0f}")
st.markdown(f"**CO₂ Emissions Avoided:** {co2_saved:,.0f} tonnes/year")
st.markdown(f"**Assumed Displaced Fuel:** {fuel_type} (Emission Factor: {emission_factor} tCO₂/MWh)")

# Plotting
fig, ax = plt.subplots()
ax.plot(months, production, label='Planned Production', linestyle='--', marker='o')
ax.plot(months, delivery, label='Delivered Heat', linestyle='-', marker='s')
ax.plot(months, dh_demand, label='Vattenfall DH Demand', linestyle=':', marker='^')
ax.set_ylabel("Monthly Heat (MWh)")
ax.set_title("Heat Production vs Delivery vs Demand")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Contract comparison summary
st.subheader("3. Contract Revenue Comparison")
contract_scenarios = {
    "Fixed Price": np.sum(delivery) * 50,  # reference value
    "Seasonal Price": np.sum(delivery * np.array([70, 65, 60, 55, 40, 30, 25, 25, 35, 50, 60, 65])),
    "Capacity + Energy": np.sum(delivery) * 35 + 10000  # reference values
}
st.dataframe(pd.DataFrame.from_dict(contract_scenarios, orient='index', columns=["Simulated Annual Revenue (€)"]))

st.markdown("---")
st.caption("Developed for Nitrocapt — Waste Heat Valorization Dashboard")
    
