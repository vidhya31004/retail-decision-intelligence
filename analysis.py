import pandas as pd

# Load data
df = pd.read_csv("data/retail_sales.csv")

# KPIs
df["revenue"] = df["price"] * df["quantity"]
df["profit"] = df["revenue"] - (df["cost"] * df["quantity"])

# Forecast demand (simple rolling average)
forecast_demand = df["quantity"].rolling(window=3).mean().iloc[-1]

# Price simulation
price_options = [95, 100, 105, 110]
cost = df["cost"].iloc[-1]

results = []

for price in price_options:
    # simple demand adjustment rule
    if price > df["price"].mean():
        estimated_demand = forecast_demand * 0.95
    else:
        estimated_demand = forecast_demand * 1.05

    revenue = price * estimated_demand
    profit = revenue - (cost * estimated_demand)

    results.append([price, round(estimated_demand, 1), round(profit, 2)])

# Results table
results_df = pd.DataFrame(
    results,
    columns=["Price", "Estimated Demand", "Estimated Profit"]
)

print("\nPrice Simulation Results:")
print(results_df)

# Recommendation
best_price = results_df.loc[results_df["Estimated Profit"].idxmax()]

print("\n✅ Recommended Decision:")
print("Set Price to ₹", best_price["Price"])
print("Expected Profit:", best_price["Estimated Profit"])

