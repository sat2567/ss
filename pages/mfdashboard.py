import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta

# --- 1. STRICT 6-CATEGORY LOGIC ---
def categorize_fund(fund_name):
    """
    Categorizes ALL funds into exactly 6 buckets.
    Hierarchy is critical here to catch specific types before general ones.
    """
    name = fund_name.lower()
    
    # 1. INTERNATIONAL FUNDS (Highest Priority)
    # Catches 'US', 'Global', 'China', 'Nasdaq', etc.
    intl_keywords = [
        'intl', 'international', 'global', 'overseas', 'world', 'fof', 
        'us ', 'u.s.', 'usa', 'america', 'nasdaq', 's&p', 
        'china', 'japan', 'europe', 'brazil', 'taiwan', 'hong kong', 
        'asia', 'emerging', 'monash', 'greater china', 'asean', 'deutschland'
    ]
    if any(x in name for x in intl_keywords):
        return 'International Funds'

    # 2. LARGE & MID CAP (Specific 'And' Logic)
    # "Bank of India Large & Mid Cap" will be caught here first
    if 'large' in name and 'mid' in name:
        return 'Large & Mid Cap'

    # 3. SMALL CAP
    if 'small' in name:
        return 'Small Cap'

    # 4. MID CAP (Must check after Large & Mid to avoid double counting)
    if 'mid' in name:
        return 'Mid Cap'

    # 5. LARGE CAP
    if 'large' in name or 'bluechip' in name or 'top 100' in name or 'frontline' in name or 'nifty' in name or 'sensex' in name:
        return 'Large Cap'

    # 6. MULTI CAP (The Catch-All)
    # If it's a "Flexi Cap", "Multi Cap", "Value", "Contra", or any random sector fund, 
    # we group it here to strictly maintain only 6 categories.
    return 'Multi Cap'

# --- 2. RETURN CALCULATION LOGIC ---
def calculate_returns(df, fund_col, date_col, period_days=None, period_months=None, period_years=None):
    """
    Calculates absolute return % between Latest Date and (Latest Date - Period).
    """
    # Sort Descending (Newest date first)
    df = df.sort_values(by=date_col, ascending=False).reset_index(drop=True)
    
    if df.empty: return np.nan
        
    # Find latest valid data point
    valid_idx = df[fund_col].first_valid_index()
    if valid_idx is None: return np.nan
        
    latest_row = df.iloc[valid_idx]
    latest_date = latest_row[date_col]
    latest_nav = latest_row[fund_col]
    
    # Calculate Target Date
    target_date = latest_date
    if period_days: target_date -= timedelta(days=period_days)
    elif period_months: target_date -= timedelta(days=30*period_months)
    elif period_years: target_date -= timedelta(days=365*period_years)
    else: return np.nan
        
    # Find row on or immediately before target date
    mask = df[date_col] <= target_date
    past_rows = df[mask]
    
    if past_rows.empty: return np.nan
        
    past_nav = past_rows.iloc[0][fund_col]
    
    if pd.isna(past_nav) or past_nav == 0: return np.nan
        
    return ((latest_nav - past_nav) / past_nav) * 100

# --- 3. FILE PROCESSOR ---
@st.cache_data
def process_alldata(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=2)
        else:
            df = pd.read_excel(uploaded_file, header=2)
            
        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        
        fund_columns = [c for c in df.columns if c != 'Date' and "Unnamed" not in str(c)]
        
        for col in fund_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        results = []
        for fund in fund_columns:
            cat = categorize_fund(fund)
            
            row = {
                "Category": cat,
                "Fund Name": fund,
                "1W (%)": calculate_returns(df, fund, 'Date', period_days=7),
                "2W (%)": calculate_returns(df, fund, 'Date', period_days=14),
                "1M (%)": calculate_returns(df, fund, 'Date', period_months=1),
                "3M (%)": calculate_returns(df, fund, 'Date', period_months=3),
                "6M (%)": calculate_returns(df, fund, 'Date', period_months=6),
                "1Y (%)": calculate_returns(df, fund, 'Date', period_years=1)
            }
            results.append(row)
            
        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"Error processing file: {e}")
        return pd.DataFrame()

# --- 4. DASHBOARD UI ---
st.set_page_config(page_title="Mutual Fund Analytics", layout="wide", page_icon="📈")

st.title("📈 Mutual Fund Returns Dashboard")
st.markdown("Upload **`alldata.xlsx`** to categorize funds into exactly 6 buckets.")

uploaded_file = st.file_uploader("Upload alldata.xlsx", type=['xlsx', 'csv'])

if uploaded_file:
    with st.spinner("Processing & Categorizing..."):
        df_results = process_alldata(uploaded_file)
        
    if not df_results.empty:
        # --- FILTERS ---
        st.sidebar.header("🔍 Filter Options")
        
        # Enforce strict order in sidebar
        strict_order = ['International Funds', 'Large & Mid Cap', 'Large Cap', 'Mid Cap', 'Small Cap', 'Multi Cap']
        available_cats = [c for c in strict_order if c in df_results["Category"].unique()]
        
        selected_cats = st.sidebar.multiselect(
            "Select Category", 
            available_cats, 
            default=available_cats
        )
        
        search_query = st.sidebar.text_input("Search Fund Name")
        
        filtered_df = df_results[df_results["Category"].isin(selected_cats)]
        if search_query:
            filtered_df = filtered_df[filtered_df["Fund Name"].str.contains(search_query, case=False)]
            
        # --- HIGHLIGHTS ---
        if not filtered_df.empty:
            st.subheader("🏆 Performance Highlights")
            col1, col2, col3 = st.columns(3)
            
            # Top 1 Month
            top_1m = filtered_df.loc[filtered_df["1M (%)"].idxmax()] if not filtered_df["1M (%)"].isna().all() else None
            if top_1m is not None:
                col1.metric("Top Fund (1 Month)", f"{top_1m['1M (%)']:.2f}%", top_1m['Fund Name'])
                
            # Top 1 Year
            top_1y = filtered_df.loc[filtered_df["1Y (%)"].idxmax()] if not filtered_df["1Y (%)"].isna().all() else None
            if top_1y is not None:
                col2.metric("Top Fund (1 Year)", f"{top_1y['1Y (%)']:.2f}%", top_1y['Fund Name'])
                
            col3.metric("Funds Visible", len(filtered_df))

        # --- MAIN TABLE ---
        st.subheader("Detailed Returns Table")
        
        display_cols = ["1W (%)", "2W (%)", "1M (%)", "3M (%)", "6M (%)", "1Y (%)"]
        
        st.dataframe(
            filtered_df.style.format({c: "{:.2f}" for c in display_cols})
            .background_gradient(cmap="RdYlGn", subset=display_cols, vmin=-2, vmax=15),
            use_container_width=True,
            height=600,
            column_config={
                "Fund Name": st.column_config.TextColumn("Fund Name", width="large"),
                "Category": st.column_config.TextColumn("Category", width="medium")
            }
        )
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Analysis as CSV", csv, "mf_returns_analysis.csv", "text/csv")
        
    else:
        st.error("Could not process data. Ensure file format is correct.")
