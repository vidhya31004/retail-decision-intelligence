import streamlit as st
import pandas as pd
import pyrebase
from datetime import date

# ================= FIREBASE INIT =================
firebase_config = {
    "apiKey": st.secrets["firebase"]["apiKey"],
    "authDomain": st.secrets["firebase"]["authDomain"],
    "projectId": st.secrets["firebase"]["projectId"],
    "storageBucket": st.secrets["firebase"]["storageBucket"],
    "messagingSenderId": st.secrets["firebase"]["messagingSenderId"],
    "appId": st.secrets["firebase"]["appId"],
    "databaseURL": ""
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
# =================================================


# ================= AUTH UI =================
st.sidebar.title("🔐 Account")

if "user" not in st.session_state:
    st.session_state.user = None

choice = st.sidebar.selectbox("Login / Sign Up", ["Login", "Sign Up"])

email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if choice == "Sign Up":
    if st.sidebar.button("Create Account"):
        try:
            auth.create_user_with_email_and_password(email, password)
            st.sidebar.success("Account created! Please log in.")
        except:
            st.sidebar.error("Signup failed")

if choice == "Login":
    if st.sidebar.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.sidebar.success("Logged in successfully")
        except:
            st.sidebar.error("Login failed")

if st.session_state.user is None:
    st.warning("Please log in to continue")
    st.stop()

# Logged-in user identity
user_id = st.session_state.user["localId"]
user_email = st.session_state.user["email"]
st.sidebar.success(f"Logged in as: {user_email}")
# ============================================


# ================= DASHBOARD =================
st.title("📊 Retail Decision Intelligence Dashboard")

# -------- LOAD DATA (SAFE + BACKWARD COMPATIBLE) --------
try:
    df = pd.read_csv("data/retail_sales.csv")
except FileNotFoundError:
    df = pd.DataFrame(
        columns=["user_id", "date", "product", "price", "quantity", "cost"]
    )

# Ensure user_id column exists (for old CSVs)
if "user_id" not in df.columns:
    df["user_id"] = user_id

# Filter data for current user only
df = df[df["user_id"] == user_id]
# -------------------------------------------------------


# ---------------- ADD DATA ----------------
st.subheader("✍️ Add Sales Data")

with st.form("add_data"):
    new_date = st.date_input("Date", value=date.today())
    product = st.text_input("Product")
    price = st.number_input("Price", min_value=0.0)
    quantity = st.number_input("Quantity Sold", min_value=0.0)
    cost = st.number_input("Unit Cost", min_value=0.0)

    submitted = st.form_submit_button("Add Data")

    if submitted:
        new_row = {
            "user_id": user_id,
            "date": new_date,
            "product": product,
            "price": price,
            "quantity": quantity,
            "cost": cost
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv("data/retail_sales.csv", index=False)
        st.success("✅ Data added successfully. Refresh to see updates.")


# ---------------- NO DATA CASE ----------------
if df.empty:
    st.info("No data yet. Add sales data to see insights.")
    st.stop()


# ---------------- KPI CALCULATIONS ----------------
df["revenue"] = df["price"] * df["quantity"]
df["profit"] = df["revenue"] - (df["cost"] * df["quantity"])

st.subheader("📌 Key Metrics")
col1, col2 = st.columns(2)
col1.metric("Total Revenue", round(df["revenue"].sum(), 2))
col2.metric("Total Profit", round(df["profit"].sum(), 2))


# ---------------- FORECAST ----------------
forecast_demand = df["quantity"].rolling(window=3).mean().iloc[-1]

st.subheader("📈 Forecasted Demand")
st.metric("Next Period Demand", round(forecast_demand, 2))


# ---------------- PRICE SIMULATION ----------------
st.subheader("🎯 Price Simulation")

avg_price = df["price"].mean()
unit_cost = df["cost"].iloc[-1]

price_options = [95, 100, 105, 110]
results = []

for p in price_options:
    if p > avg_price:
        demand = forecast_demand * 0.95
    else:
        demand = forecast_demand * 1.05

    profit_val = (p - unit_cost) * demand
    results.append([p, round(demand, 1), round(profit_val, 2)])

results_df = pd.DataFrame(
    results, columns=["Price", "Estimated Demand", "Estimated Profit"]
)

st.dataframe(results_df)

best = results_df.loc[results_df["Estimated Profit"].idxmax()]

st.success(
    f"✅ Recommended Price: ₹{int(best['Price'])} "
    f"(Expected Profit: ₹{best['Estimated Profit']})"
)


# ---------------- CHART ----------------
st.subheader("📊 Profit vs Price")
st.line_chart(results_df.set_index("Price")["Estimated Profit"])


# ---------------- GOVERNANCE ----------------
st.caption(f"User-specific insights for: {user_email}")
# ============================================

