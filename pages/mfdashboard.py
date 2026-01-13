import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
import io

# --- 1. ADVANCED CATEGORIZATION LOGIC ---

def categorize_fund(fund_name):
    """
    Master Categorization Logic.
    """
    name = fund_name.lower()
    
    # --- LEVEL 1: COMMODITIES ---
    if any(x in name for x in ['gold', 'silver', 'commodity', 'bullion']):
        return 'Commodities (Gold/Silver)'
        
    # --- LEVEL 2: INTERNATIONAL & FoF ---
    # As per request: Treat all FoFs as International (unless Gold)
    if 'fof' in name or 'fund of fund' in name:
        return 'International / FoF'
        
    if any(x in name for x in ['global', 'intl', 'international', 'us equity', 'nasdaq', 's&p', 'emerging', 'china', 'taiwan', 'brazil', 'europe', 'world', 'overseas', 'monash', 'hang seng']):
        return 'International / FoF'

    # --- LEVEL 3: HYBRID / BALANCED ---
    if 'arbitrage' in name:
        return 'Hybrid - Arbitrage'
    if 'balanced advantage' in name or 'bal adv' in name or 'baf' in name or 'dynamic asset' in name:
        return 'Hybrid - Balanced Advantage'
    if 'multi asset' in name:
        return 'Hybrid - Multi Asset'
    if 'equity savings' in name:
        return 'Hybrid - Equity Savings'
    if 'hybrid' in name or 'balanced' in name:
        return 'Hybrid - Aggressive/Conservative'
        
    # --- LEVEL 4: PASSIVE / INDEX ---
    if 'index' in name or 'nifty' in name or 'sensex' in name or 'etf' in name or 'passive' in name:
        return 'Index Fund / ETF'

    # --- LEVEL 5: EQUITY - SECTORAL & THEMATIC ---
    if any(x in name for x in ['tech', 'digital', 'technology']):
        return 'Sector - Technology'
    if any(x in name for x in ['pharma', 'health', 'life']):
        return 'Sector - Pharma/Healthcare'
    if any(x in name for x in ['bank', 'finance', 'fin serv']):
        return 'Sector - Banking/Finance'
    if any(x in name for x in ['infra', 'build india', 'construction']):
        return 'Sector - Infrastructure'
    if any(x in name for x in ['consumption', 'consumer']):
        return 'Thematic - Consumption'
    if any(x in name for x in ['psu', 'public sector']):
        return 'Thematic - PSU'
    if any(x in name for x in ['mnc']):
        return 'Thematic - MNC'
    if any(x in name for x in ['esg', 'ethical']):
        return 'Thematic - ESG'
    if any(x in name for x in ['quant', 'special', 'opportunities', 'business cycle', 'manufacturing', 'defence', 'services']):
        return 'Thematic - Other'

    # --- LEVEL 6: EQUITY - DIVERSIFIED ---
    if 'large' in name and 'mid' in name:
        return 'Large & Mid Cap'
    if 'flexi' in name:
        return 'Flexi Cap'
    if 'multi' in name and 'cap' in name:
        return 'Multi Cap'
    if 'small' in name:
        return 'Small Cap'
    if 'mid' in name:
        return 'Mid Cap'
    if 'large' in name or 'bluechip' in name or 'top 100' in name or 'frontline' in name or 'leaders' in name:
        return 'Large Cap'
    if 'focused' in name:
        return 'Focused Fund'
    if 'value' in name or 'contra' in name:
        return 'Value / Contra'
    if 'elss' in name or 'tax' in name or 'long term equity' in name:
        return 'ELSS (Tax Saver)'
    if 'dividend' in name and 'yield' in name:
        return 'Dividend Yield'
        
    # --- LEVEL 7: DEBT & LIQUID ---
    if any(x in name for x in ['liquid', 'overnight', 'bond', 'gilt', 'duration', 'corporate', 'credit', 'money market', 'float', 'income', 'dynamic bond', 'treasury', 'cash']):
        return 'Debt / Liquid'
        
    # --- LEVEL 8: CATCH-ALL ---
    return 'Other Equity'

# --- 2. CALCULATION LOGIC ---

def calculate_returns(df, fund_col, date_col, period_days=None, period_months=None, period_years=None):
    # Sort by date descending (Newest first)
    df = df.sort_values(by=date_col, ascending=False).reset_index(drop=True)
    
    if df.empty: return np.nan
        
    # Get latest valid NAV
    valid_idx = df[fund_col].first_valid_index()
    if valid_idx is None: return np.nan
        
    latest_row = df.iloc[valid_idx]
    latest_date = latest_row[date_col]
    latest_nav = latest_row[fund_col]
    
    # Target Date Calculation
    target_date = latest_date
    if period_days: target_date -= timedelta(days=period_days)
    elif period_months: target_date -= timedelta(days=30*period_months)
    elif period_years: target_date -= timedelta(days=365*period_years)
    else: return np.nan
        
    # Find closest past NAV
    mask = df[date_col] <= target_date
    past_rows = df[mask]
    
    if past_rows.empty: return np.nan
        
    past_nav = past_rows.iloc[0][fund_col]
    if pd.isna(past_nav) or past_nav == 0: return np.nan
        
    return ((latest_nav - past_nav) / past_nav) * 100

@st.cache_data
def process_master_file(uploaded_file):
    try:
        # Load File (Skipping first 2 rows of junk)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=2)
        else:
            df = pd.read_excel(uploaded_file, header=2)
            
        # Fix Date Column (Assuming Col 0 is Date)
        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        
        # Identify Funds
        fund_columns = [c for c in df.columns if c != 'Date' and "Unnamed" not in str(c)]
        
        # Convert to Numeric
        for col in fund_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        results_list = []
        
        # Process Funds
        for fund in fund_columns:
            cat = categorize_fund(fund)
            
            # Performance Metrics (ONLY 1W, 2W, 1M, 3M, 6M, 1Y)
            res = {
                "Category": cat,
                "Fund Name": fund,
                "1W (%)": calculate_returns(df, fund, 'Date', period_days=7),
                "2W (%)": calculate_returns(df, fund, 'Date', period_days=14),
                "1M (%)": calculate_returns(df, fund, 'Date', period_months=1),
                "3M (%)": calculate_returns(df, fund, 'Date', period_months=3),
                "6M (%)": calculate_returns(df, fund, 'Date', period_months=6),
                "1Y (%)": calculate_returns(df, fund, 'Date', period_years=1)
            }
            results_list.append(res)
            
        return pd.DataFrame(results_list)

    except Exception as e:
        st.error(f"Error processing file: {e}")
        return pd.DataFrame()

# --- 3. STREAMLIT UI ---

st.set_page_config(page_title="MF Analytics Pro", layout="wide", page_icon="📈")

st.title("📈 Mutual Fund Master Analytics")
st.markdown("Upload your `alldata.xlsx` for 1W to 1Y Return Analysis.")

uploaded_file = st.file_uploader("Upload Master File (Excel/CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    with st.spinner("Calculating Returns..."):
        df_results = process_master_file(uploaded_file)
        
    if not df_results.empty:
        # Layout
        st.sidebar.header("🔍 Filters")
        
        # Category Filter
        cats = sorted(df_results["Category"].unique())
        sel_cats = st.sidebar.multiselect("Select Category", cats, default=cats)
        
        # Search
        search = st.sidebar.text_input("Search Fund")
        
        # Apply Filters
        filtered = df_results[df_results["Category"].isin(sel_cats)]
        if search:
            filtered = filtered[filtered["Fund Name"].str.contains(search, case=False)]
            
        # Top Performers (Dynamic)
        if not filtered.empty:
            st.subheader("🏆 Category Leaders (Filtered)")
            c1, c2, c3 = st.columns(3)
            
            # 1 Month Top
            best_1m = filtered.loc[filtered["1M (%)"].idxmax()] if not filtered["1M (%)"].isna().all() else None
            if best_1m is not None:
                c1.metric("Top Fund (1 Month)", f"{best_1m['1M (%)']:.1f}%", best_1m['Fund Name'])
                
            # 1 Year Top
            best_1y = filtered.loc[filtered["1Y (%)"].idxmax()] if not filtered["1Y (%)"].isna().all() else None
            if best_1y is not None:
                c2.metric("Top Fund (1 Year)", f"{best_1y['1Y (%)']:.1f}%", best_1y['Fund Name'])

            # Count
            c3.metric("Funds in View", len(filtered))

        # Main Table
        st.subheader("Detailed Performance")
        cols = ["1W (%)", "2W (%)", "1M (%)", "3M (%)", "6M (%)", "1Y (%)"]
        
        st.dataframe(
            filtered.style.format({c: "{:.2f}" for c in cols})
            .background_gradient(cmap="RdYlGn", subset=cols, vmin=-2, vmax=15),
            use_container_width=True,
            height=600,
            column_config={
                "Fund Name": st.column_config.TextColumn("Fund Name", width="large"),
                "Category": st.column_config.TextColumn("Category", width="small")
            }
        )
        
        # CSV Download
        st.download_button(
            label="Download Report", 
            data=filtered.to_csv(index=False).encode('utf-8'), 
            file_name="mf_analytics_1w_to_1y.csv", 
            mime="text/csv"
        )
    else:
        st.error("Could not process the file. Ensure headers are correct.")
