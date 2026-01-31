import streamlit as st
import pandas as pd
import pyrebase

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


# ================= AUTH =================
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

user_id = st.session_state.user["localId"]
user_email = st.session_state.user["email"]
st.sidebar.success(f"Logged in as: {user_email}")

# Session flag: insights only after upload
if "data_uploaded" not in st.session_state:
    st.session_state.data_uploaded = False
# ========================================


# ================= DASHBOARD =================
st.title("📊 Decision Intelligence Dashboard")

# -------- LOAD DATA --------
try:
    df = pd.read_csv("data/retail_sales.csv")
except FileNotFoundError:
    df = pd.DataFrame(columns=["user_id", "price", "quantity", "cost"])

if "user_id" not in df.columns:
    df["user_id"] = user_id

df = df[df["user_id"] == user_id]
# -------------------------------------------


# ================= FILE UPLOAD =================
st.subheader("📤 Upload Sales Dataset (CSV)")

uploaded_file = st.file_uploader(
    "Upload a CSV file (multiple uploads supported)",
    type=["csv"]
)

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
    st.write("📄 Preview of uploaded data")
    st.dataframe(raw_df.head())

    # -------- COLUMN DETECTION --------
    def normalize(col):
        return col.lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "")

    price_keywords = ["price", "unitprice", "sellingprice", "mrp", "rate"]
    quantity_keywords = ["quantity", "qty", "units", "volume", "demand"]
    cost_keywords = ["cost", "unitcost", "cogs", "margin"]

    detected_price = None
    detected_quantity = None
    detected_cost = None

    for col in raw_df.columns:
        col_norm = normalize(col)
        if any(k in col_norm for k in price_keywords):
            detected_price = col
        if any(k in col_norm for k in quantity_keywords):
            detected_quantity = col
        if any(k in col_norm for k in cost_keywords):
            detected_cost = col

    if detected_price is None or detected_quantity is None:
        st.error(
            "❌ Could not detect Price or Quantity columns.\n"
            "Ensure your file contains at least one price-related and one quantity-related column."
        )
        st.stop()

    # -------- USER CONFIRMATION --------
    st.subheader("🔎 Confirm Column Mapping")

    price_col = st.selectbox(
        "Select Price column",
        options=raw_df.columns,
        index=list(raw_df.columns).index(detected_price)
    )

    quantity_col = st.selectbox(
        "Select Quantity column",
        options=raw_df.columns,
        index=list(raw_df.columns).index(detected_quantity)
    )

    cost_col = st.selectbox(
        "Select Cost column (optional)",
        options=["None"] + list(raw_df.columns),
        index=0 if detected_cost is None else list(raw_df.columns).index(detected_cost) + 1
    )

    # -------- MISSING VALUE HANDLING --------
    st.subheader("🧹 Missing Value Handling")

    missing_strategy = st.radio(
        "How should missing values be handled?",
        options=[
            "Drop rows with missing values",
            "Fill missing values with mean",
            "Fill missing values with median"
        ]
    )

    confirm = st.button("✅ Confirm and Ingest Data")

    if confirm:
        standardized_df = pd.DataFrame()
        standardized_df["price"] = raw_df[price_col]
        standardized_df["quantity"] = raw_df[quantity_col]
        standardized_df["cost"] = raw_df[cost_col] if cost_col != "None" else 0
        standardized_df["user_id"] = user_id

        # ---- Apply missing value strategy ----
        if missing_strategy == "Drop rows with missing values":
            standardized_df = standardized_df.dropna(subset=["price", "quantity"])

        elif missing_strategy == "Fill missing values with mean":
            for col in ["price", "quantity", "cost"]:
                standardized_df[col] = standardized_df[col].fillna(
                    standardized_df[col].mean()
                )

        elif missing_strategy == "Fill missing values with median":
            for col in ["price", "quantity", "cost"]:
                standardized_df[col] = standardized_df[col].fillna(
                    standardized_df[col].median()
                )

        df = pd.concat([df, standardized_df], ignore_index=True)
        df.to_csv("data/retail_sales.csv", index=False)

        st.session_state.data_uploaded = True
        st.success("✅ Data ingested successfully. Insights generated below.")


# ================= ANALYTICS =================
if not st.session_state.data_uploaded:
    st.info("📤 Upload a dataset to generate insights.")
    st.stop()

if df.empty:
    st.warning("Uploaded data contains no usable rows.")
    st.stop()

df["revenue"] = df["price"] * df["quantity"]
df["profit"] = df["revenue"] - (df["cost"] * df["quantity"])

st.subheader("📌 Key Metrics")
c1, c2 = st.columns(2)
c1.metric("Total Revenue", round(df["revenue"].sum(), 2))
c2.metric("Total Profit", round(df["profit"].sum(), 2))


# ---------------- FORECAST ----------------
forecast_demand = df["quantity"].rolling(window=3).mean().iloc[-1]

st.subheader("📈 Forecasted Demand")
st.metric("Next Period Demand", round(forecast_demand, 2))


# ---------------- DATA-DRIVEN SIMULATION ----------------
st.subheader("🎯 Pricing Scenario Simulation (User-Driven)")

min_price = df["price"].min()
max_price = df["price"].max()
avg_price = df["price"].mean()
avg_quantity = df["quantity"].mean()
avg_cost = df["cost"].mean()

price_range = sorted(set([
    round(min_price * 0.95, 2),
    round(avg_price * 0.95, 2),
    round(avg_price, 2),
    round(avg_price * 1.05, 2),
    round(max_price * 1.05, 2)
]))

results = []

for p in price_range:
    demand = avg_quantity * (0.9 if p > avg_price else 1.1)
    profit_val = (p - avg_cost) * demand
    results.append([p, round(demand, 2), round(profit_val, 2)])

results_df = pd.DataFrame(
    results,
    columns=["Simulated Price", "Estimated Demand", "Estimated Profit"]
)

st.dataframe(results_df)

best = results_df.loc[results_df["Estimated Profit"].idxmax()]
st.success(
    f"✅ Recommended Price: ₹{best['Simulated Price']} "
    f"(Expected Profit: ₹{best['Estimated Profit']})"
)

st.subheader("📊 Profit vs Price")
st.line_chart(results_df.set_index("Simulated Price")["Estimated Profit"])


# ================= FOOTER =================
st.caption(f"User-specific insights for: {user_email}")

