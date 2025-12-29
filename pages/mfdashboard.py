import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta

# --- Configuration ---
# Base URL for the raw content from your GitHub branch
BASE_URL = "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/"

# Updated to use the clean Excel filenames provided
FILES = {
    "Large Cap": "LARGECAP1YEAR.xlsx",
    "Mid Cap": "MIDCAP1Y.xlsx",
    "Multi Cap": "MULTICAP1Y.xlsx",
    "Small Cap": "SMALLCAP1YEAR.xlsx",
    "Large & Mid Cap": "LARGEANDMIDCAP_2.xlsx"
}

# --- Helper Functions ---

def calculate_returns(df, fund_col, date_col, period_days=None, period_months=None, period_years=None):
    """
    Calculates the percentage return for a given period.
    """
    # Sort by date descending (newest first)
    df = df.sort_values(by=date_col, ascending=False).reset_index(drop=True)
    
    if df.empty:
        return np.nan
        
    # Get latest valid NAV
    valid_idx = df[fund_col].first_valid_index()
    if valid_idx is None:
        return np.nan
        
    latest_row = df.iloc[valid_idx]
    latest_date = latest_row[date_col]
    latest_nav = latest_row[fund_col]
    
    # Determine target date
    if period_days:
        target_date = latest_date - timedelta(days=period_days)
    elif period_months:
        # Approximation: 1 month = 30 days
        target_date = latest_date - timedelta(days=30*period_months)
    elif period_years:
        # Approximation: 1 year = 365 days
        target_date = latest_date - timedelta(days=365*period_years)
    else:
        return np.nan
        
    # Find the row on or closest (before) the target date
    mask = df[date_col] <= target_date
    past_rows = df[mask]
    
    if past_rows.empty:
        return np.nan
        
    past_row = past_rows.iloc[0]
    past_nav = past_row[fund_col]
    
    if pd.isna(past_nav) or past_nav == 0:
        return np.nan
        
    return ((latest_nav - past_nav) / past_nav) * 100

@st.cache_data
def load_and_process_data():
    all_results = []
    
    for category, filename in FILES.items():
        # Construct the URL
        url = BASE_URL + filename
        
        try:
            if category == "Large Cap":
                # Large Cap Logic:
                # 1. Read metadata (Row 1, Col 1) for Fund Name
                meta = pd.read_excel(url, header=None, nrows=1, engine='openpyxl')
                fund_name = meta.iloc[0, 0].split(">>")[0].strip()
                
                # 2. Read Data (Header is at row 4, index 3)
                df = pd.read_excel(url, header=3, engine='openpyxl')
                
                # Identify NAV column
                nav_col = 'Adjusted NAV NonCorporate(Rs)'
                if nav_col not in df.columns:
                     nav_col = 'NAV (Rs)'
                
                df.rename(columns={'NAV Date': 'Date', nav_col: fund_name}, inplace=True)
                fund_columns = [fund_name]
                
            else:
                # Standard Logic (Mid, Small, Multi, Large&Mid):
                # Header is at row 3 (index 2)
                df = pd.read_excel(url, header=2, engine='openpyxl')
                
                # Rename first column to Date
                df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
                
                # Drop the first row (which usually contains units like "Rs")
                df = df.drop(0).reset_index(drop=True)
                
                # Identify fund columns (all except Date)
                fund_columns = [c for c in df.columns if c != 'Date']

            # --- Common Cleaning ---
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])
            
            # Convert fund columns to numeric
            for col in fund_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Calculate Returns for each fund
            for fund in fund_columns:
                r_1w = calculate_returns(df, fund, 'Date', period_days=7)
                r_2w = calculate_returns(df, fund, 'Date', period_days=14)
                r_3w = calculate_returns(df, fund, 'Date', period_days=21)
                r_1m = calculate_returns(df, fund, 'Date', period_months=1)
                r_1y = calculate_returns(df, fund, 'Date', period_years=1)
                
                all_results.append({
                    "Category": category,
                    "Fund Name": fund,
                    "1 Week (%)": r_1w,
                    "2 Weeks (%)": r_2w,
                    "3 Weeks (%)": r_3w,
                    "1 Month (%)": r_1m,
                    "1 Year (%)": r_1y
                })
                
        except Exception as e:
            st.error(f"Error processing {category} ({filename}): {e}")
            
    return pd.DataFrame(all_results)

# --- Streamlit UI ---

st.set_page_config(page_title="Mutual Fund Returns Dashboard", layout="wide")

st.title("📊 Mutual Fund Returns Analysis")
st.markdown(f"Data Source: [GitHub Repository]({BASE_URL})")

with st.spinner('Fetching and processing Excel files from GitHub...'):
    df_results = load_and_process_data()

if not df_results.empty:
    # Formatting columns
    numeric_cols = ["1 Week (%)", "2 Weeks (%)", "3 Weeks (%)", "1 Month (%)", "1 Year (%)"]
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    selected_categories = st.sidebar.multiselect(
        "Select Category",
        options=df_results["Category"].unique(),
        default=df_results["Category"].unique()
    )
    
    # Filter Data
    filtered_df = df_results[df_results["Category"].isin(selected_categories)]
    
    # Display Summary Metrics
    if not filtered_df.empty:
        top_performer = filtered_df.loc[filtered_df["1 Month (%)"].idxmax()]
        st.info(f"🏆 **Top Performer (1 Month):** {top_performer['Fund Name']} ({top_performer['1 Month (%)']:.2f}%)")

    # Display Data Table
    st.subheader("Fund Performance Summary")
    
    # Apply color formatting to returns
    st.dataframe(
        filtered_df.style.format({col: "{:.2f}" for col in numeric_cols})
        .background_gradient(cmap="RdYlGn", subset=numeric_cols),
        use_container_width=True,
        height=600
    )
    
    # Download Button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Report as CSV",
        data=csv,
        file_name='mutual_fund_returns.csv',
        mime='text/csv',
    )

else:
    st.warning("No data found. Please check that the .xlsx files are in your GitHub branch.")
