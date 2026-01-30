import streamlit as st
import pandas as pd
import pyrebase
# ---------- FIREBASE INIT ----------
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
# ---------------------------------

# --- USER ENROLMENT ---
st.sidebar.title("👤 User Enrolment")

if "user" not in st.session_state:
    st.session_state.user = ""

user_name = st.sidebar.text_input("Enter your name")

if user_name:
    st.session_state.user = user_name
    st.sidebar.success(f"Welcome, {user_name} 👋")
else:
    st.sidebar.info("Please enter your name to continue")
    st.stop()
# ---------- AUTH UI ----------
if "user" not in st.session_state:
    st.session_state.user = None

st.sidebar.title("🔐 Account")

choice = st.sidebar.selectbox("Login / Signup", ["Login", "Sign Up"])

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
# --------------------------------

st.title("📊 Retail Decision Intelligence Dashboard")
st.caption(f"Last updated by: {st.session_state.user}")

# Load data
df = pd.read_csv("data/retail_sales.csv")
# ---------------- DATA ENTRY ----------------
st.subheader("✍️ Add New Sales Data")

with st.form("data_entry_form"):
    new_date = st.date_input("Date")
    new_product = st.selectbox("Product", df["product"].unique())
    new_price = st.number_input("Price", min_value=0)
    new_quantity = st.number_input("Quantity Sold", min_value=0)
    new_cost = st.number_input("Unit Cost", min_value=0)

    submitted = st.form_submit_button("Add Data")

    if submitted:
        new_row = {
            "date": new_date,
            "product": new_product,
            "price": new_price,
            "quantity": new_quantity,
            "cost": new_cost
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv("data/retail_sales.csv", index=False)

        st.success("✅ Data added successfully! Please refresh to see updates.")
# --------------------------------------------

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

