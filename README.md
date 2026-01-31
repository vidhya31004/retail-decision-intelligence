DECISION INTELLIGENCE PLATFORM 

A public intelligence platform that enables users to securly upload real-world sales datasets, cleana nd standradize messy data and generates data-driven insights such as demand forecasts, revenue metrices and pricing simulations. 
This system is designed with a motive of reflecting real BI workflows, including user specific analytics and explicit data-cleaning assumptions.

KEY FEATURES
------------
- User autentication - firebase(email/password)
- User specific data 
- File based data ingestion 
- Schema-flexible ingestion
- User confirmed column mappings
- Missing value handling
- Decision Intelligence outputs 

LIVE DEMO
---------
https://retail-decision-intelligence-23jgtiommvymhzb2uv6zms.streamlit.app

EXPECTED DATASET FORMAT
-----------------------
File type : CSV 
Column names are also flexible
Dataset must contain at least:
- one price-related column
- one quantity-related column

DATA ASSUMPTIONS 
----------------
Users explicitly choose how missing values are handled:
- Row exclusion 
- Mean imputation
- Median imputation
Aggrtegations and forecasts are based on user-uploaded data 

TECH STACK
----------
-Streamlit 
-Python 
-Pandas 
-Firecase 
-Streamlit Community Cloud 

