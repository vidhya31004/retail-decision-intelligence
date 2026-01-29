import streamlit as st
import pandas as pd

st.title("📊 Retail Decision Intelligence Dashboard")

# Load data
df = pd.read_csv("data/retail_sales.csv")
st.subheader("🛒 Select Product")
product = st.selectbox("Choose a product", df["product"].unique())

df = df[df["product"] == product]

# Forecast demand (simple rolling average)
forecast_demand = df["quantity"].rolling(window=3).mean().iloc[-1]
avg_price = df["price"].mean()
cost = df["cost"].iloc[-1]

st.subheader("📈 Forecasted Demand")
st.metric("Next Period Demand", round(forecast_demand, 2))

# --- PRICE SLIDER ---
st.subheader("🎯 Set Product Price")
selected_price = st.slider(
    "Choose Price (₹)",
    min_value=90,
    max_value=120,
    step=5,
    value=100
)

# Demand adjustment logic
if selected_price > avg_price:
    estimated_demand = forecast_demand * 0.95
else:
    estimated_demand = forecast_demand * 1.05

# Profit calculation
revenue = selected_price * estimated_demand
profit = revenue - (cost * estimated_demand)

# --- RESULTS ---
st.subheader("💡 Decision Outcome")

col1, col2 = st.columns(2)
col1.metric("Estimated Demand", round(estimated_demand, 1))
col2.metric("Expected Profit (₹)", round(profit, 2))

# --- AUTO RECOMMENDATION ---
st.subheader("✅ System Recommendation")

price_options = [95, 100, 105, 110]
results = []

for price in price_options:
    if price > avg_price:
        demand = forecast_demand * 0.95
    else:
        demand = forecast_demand * 1.05

    profit_val = (price - cost) * demand
    results.append([price, round(profit_val, 2)])

results_df = pd.DataFrame(results, columns=["Price", "Profit"])

best_price = results_df.loc[results_df["Profit"].idxmax()]

if selected_price == best_price["Price"]:
    st.success(
        f"🎯 Optimal Choice! ₹{int(best_price['Price'])} gives the highest profit."
    )
else:
    st.warning(
        f"⚠️ Better Option Available: "
        f"₹{int(best_price['Price'])} yields higher profit."
    )

# --- SHOW TABLE ---
with st.expander("📊 View All Price Scenarios"):
    st.dataframe(results_df)

st.subheader("🧠 Decision Explanation")

if selected_price > avg_price:
    st.write(
        "The selected price is above the historical average. "
        "This slightly reduces demand but improves margin per unit."
    )
else:
    st.write(
        "The selected price is below or equal to the historical average. "
        "This increases demand but reduces margin per unit."
    )

st.write(
    "The system balances demand and profit to identify the price "
    "that maximizes overall business performance."
)

st.subheader("📈 Profit vs Price")

st.line_chart(
    results_df.set_index("Price")["Profit"]
)

