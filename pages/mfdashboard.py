import streamlit as st
import requests
import pandas as pd
from datetime import timedelta
import time
from typing import Dict, List
import numpy as np

# --- Configuration ---
BASE_URL = "https://api.mfapi.in"

class MutualFundAnalyzer:
    
    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_schemes() -> List[Dict]:
        """Fetch list of all mutual fund schemes."""
        try:
            response = requests.get(f"{BASE_URL}/mf", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching schemes list: {e}")
            return []

    @staticmethod
    def filter_schemes_by_category(schemes: List[Dict], category: str) -> List[Dict]:
        """Filter schemes based on category keywords and Regular/Growth plans."""
        filtered = []
        category_lower = category.lower()
        
        if category_lower == 'all funds':
            # For All Funds, collect schemes that match any category
            for scheme in schemes:
                name = scheme.get('schemeName', '').lower()
                
                # 2. Strict Filter: Regular Plan + Growth Option only
                if 'regular' not in name or 'growth' not in name:
                    continue
                    
                # 3. Exclude IDCW/Dividend/Direct
                if any(kw in name for kw in ['idcw', 'dividend', 'income distribution', 'direct']):
                    continue
                    
                # 1. Category Matching Logic - check if matches any category
                match = False
                for cat in ['Large Cap', 'Mid Cap', 'Small Cap', 'Large & Mid Cap', 'Multi Cap', 'International']:
                    cat_lower_check = cat.lower()
                    if cat_lower_check == 'international':
                        if any(kw in name for kw in ['international', 'global', 'overseas']):
                            match = True
                    elif cat_lower_check == 'large & mid cap':
                        if any(v in name for v in ['large & mid cap', 'large and mid cap', 'large and midcap']):
                            match = True
                    elif cat_lower_check == 'large cap':
                        # Exclude Large & Mid Cap from Large Cap
                        if 'large cap' in name and not any(v in name for v in ['large & mid cap', 'large and mid cap', 'large and midcap']):
                            match = True
                    elif cat_lower_check == 'mid cap':
                         # Exclude Large & Mid Cap from Mid Cap
                        if 'mid cap' in name and not any(v in name for v in ['large & mid cap', 'large and mid cap', 'large and midcap']):
                            match = True
                    else:
                        if cat_lower_check in name:
                            match = True
                
                if match:
                    filtered.append(scheme)
        else:
            # Original logic for specific categories
            for scheme in schemes:
                name = scheme.get('schemeName', '').lower()
                
                # 1. Category Matching Logic
                match = False
                if category_lower == 'international':
                    if any(kw in name for kw in ['international', 'global', 'overseas']):
                        match = True
                elif category_lower == 'large & mid cap':
                    if any(v in name for v in ['large & mid cap', 'large and mid cap', 'large and midcap']):
                        match = True
                elif category_lower == 'large cap':
                    # Exclude Large & Mid Cap from Large Cap
                    if 'large cap' in name and not any(v in name for v in ['large & mid cap', 'large and mid cap', 'large and midcap']):
                        match = True
                elif category_lower == 'mid cap':
                     # Exclude Large & Mid Cap from Mid Cap
                    if 'mid cap' in name and not any(v in name for v in ['large & mid cap', 'large and mid cap', 'large and midcap']):
                        match = True
                else:
                    if category_lower in name:
                        match = True
                
                if not match:
                    continue

                # 2. Strict Filter: Regular Plan + Growth Option only
                if 'regular' not in name or 'growth' not in name:
                    continue
                    
                # 3. Exclude IDCW/Dividend/Direct
                if any(kw in name for kw in ['idcw', 'dividend', 'income distribution', 'direct']):
                    continue
                    
                filtered.append(scheme)
                
        return filtered

    @staticmethod
    @st.cache_data(ttl=86400, show_spinner=False)
    def get_scheme_data(scheme_code: str) -> pd.DataFrame:
        """Fetch historical NAV data for a single scheme."""
        try:
            response = requests.get(f"{BASE_URL}/mf/{scheme_code}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data or 'data' not in data:
                return pd.DataFrame()
                
            df = pd.DataFrame(data['data'])
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
            
            # Sort by date ascending (oldest to newest)
            df = df.dropna().sort_values('date').set_index('date')
            return df
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def calculate_cagr(start: float, end: float, days: int) -> float:
        if start <= 0 or days <= 0:
            return np.nan
        years = days / 365.25
        return ((end / start) ** (1 / years) - 1) * 100

    @staticmethod
    def calculate_absolute_return(start: float, end: float) -> float:
        if start <= 0: return np.nan
        return (end / start - 1) * 100

    @staticmethod
    def get_return_metrics(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate 1W, 1M, 3M, 6M, 1Y, 3Y returns."""
        if df.empty or len(df) < 2:
            return {k: np.nan for k in ["1W", "1M", "3M", "6M", "1Y", "3Y_CAGR"]}
            
        latest_date = df.index.max()
        latest_nav = df.loc[latest_date, 'nav']
        
        periods = {
            "1W": timedelta(weeks=1),
            "1M": timedelta(days=30),
            "3M": timedelta(days=90),
            "6M": timedelta(days=180),
            "1Y": timedelta(days=365),
            "3Y_CAGR": timedelta(days=365*3)
        }
        
        returns = {}
        for label, delta in periods.items():
            target_date = latest_date - delta
            
            # Find the closest date before or on the target date (handling weekends)
            # method='pad' finds the nearest previous valid index
            idx_loc = df.index.get_indexer([target_date], method='pad')[0]
            
            if idx_loc != -1:
                past_date = df.index[idx_loc]
                past_nav = df.loc[past_date, 'nav']
                days_diff = (latest_date - past_date).days
                
                # Only calculate if we actually went back enough time (approx)
                if days_diff >= (delta.days - 7): 
                    if "CAGR" in label:
                        returns[label] = MutualFundAnalyzer.calculate_cagr(past_nav, latest_nav, days_diff)
                    else:
                        returns[label] = MutualFundAnalyzer.calculate_absolute_return(past_nav, latest_nav)
                else:
                    returns[label] = np.nan
            else:
                returns[label] = np.nan
                
        return returns

    # --- Risk Metrics ---

    @staticmethod
    def calculate_volatility(df: pd.DataFrame) -> float:
        """Annualized Volatility (Standard Deviation of returns)."""
        if len(df) < 2: return np.nan
        returns = df['nav'].pct_change().dropna()
        return returns.std() * np.sqrt(252) * 100

    @staticmethod
    def calculate_sharpe_ratio(df: pd.DataFrame, rf_percent: float) -> float:
        """Sharpe Ratio = (Ann. Return - Risk Free Rate) / Ann. Volatility"""
        if len(df) < 252: return np.nan # Need at least 1 year for valid Sharpe
        
        # Calculate Annualized Return (CAGR for the whole period)
        start_nav = df['nav'].iloc[0]
        end_nav = df['nav'].iloc[-1]
        days = (df.index[-1] - df.index[0]).days
        
        if days <= 0: return np.nan
        ann_return_decimal = (end_nav / start_nav) ** (365.25 / days) - 1
        
        rf_decimal = rf_percent / 100
        
        # Annualized Volatility (decimal)
        returns = df['nav'].pct_change().dropna()
        vol_decimal = returns.std() * np.sqrt(252)
        
        if vol_decimal == 0: return np.nan
        return (ann_return_decimal - rf_decimal) / vol_decimal

    @staticmethod
    def calculate_sortino_ratio(df: pd.DataFrame, rf_percent: float) -> float:
        """Sortino Ratio = (Ann. Return - Risk Free Rate) / Downside Deviation"""
        if len(df) < 252: return np.nan
        
        # 1. Annualized Return
        start_nav = df['nav'].iloc[0]
        end_nav = df['nav'].iloc[-1]
        days = (df.index[-1] - df.index[0]).days
        ann_return_decimal = (end_nav / start_nav) ** (365.25 / days) - 1
        
        rf_decimal = rf_percent / 100
        
        # 2. Downside Deviation (Target = Risk Free Rate)
        # We calculate the Root Mean Square of negative excess returns
        returns = df['nav'].pct_change().dropna()
        
        # Daily Risk Free Rate approx
        daily_rf = (1 + rf_decimal) ** (1/252) - 1
        
        # Excess returns
        excess_returns = returns - daily_rf
        
        # Keep only negative excess returns
        negative_returns = excess_returns[excess_returns < 0]
        
        if len(negative_returns) == 0:
            return np.nan
            
        # Root Mean Square of Downside
        downside_variance = (negative_returns ** 2).sum() / len(returns) # Divide by total N, not just negative N
        downside_dev_daily = np.sqrt(downside_variance)
        downside_dev_ann = downside_dev_daily * np.sqrt(252)
        
        if downside_dev_ann == 0: return np.nan
        
        return (ann_return_decimal - rf_decimal) / downside_dev_ann

    @staticmethod
    def calculate_max_drawdown(df: pd.DataFrame) -> float:
        """Maximum loss from a peak to a trough."""
        if df.empty: return np.nan
        nav = df['nav']
        peak = nav.expanding().max()
        drawdown = (nav - peak) / peak
        return drawdown.min() * 100

def process_funds_batch(schemes_list: List[Dict], rf_rate: float) -> pd.DataFrame:
    """Process a list of schemes and return a DataFrame of metrics."""
    results = []
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(schemes_list)
    
    for i, scheme in enumerate(schemes_list):
        # Update progress
        progress = (i + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"Fetching data for: {scheme['schemeName'][:40]}...")
        
        code = scheme['schemeCode']
        df = MutualFundAnalyzer.get_scheme_data(code)
        
        if not df.empty and len(df) > 30: # Only process if valid data exists
            metrics = MutualFundAnalyzer.get_return_metrics(df)
            vol = MutualFundAnalyzer.calculate_volatility(df)
            sharpe = MutualFundAnalyzer.calculate_sharpe_ratio(df, rf_rate)
            sortino = MutualFundAnalyzer.calculate_sortino_ratio(df, rf_rate)
            mdd = MutualFundAnalyzer.calculate_max_drawdown(df)
            
            row = {
                'Scheme Name': scheme['schemeName'],
                'Latest NAV': df['nav'].iloc[-1],
                '1W (%)': metrics['1W'],
                '1M (%)': metrics['1M'],
                '3M (%)': metrics['3M'],
                '1Y (%)': metrics['1Y'],
                '3Y CAGR (%)': metrics['3Y_CAGR'],
                'Vol (%)': vol,
                'Sharpe': sharpe,
                'Sortino': sortino,
                'Max DD (%)': mdd
            }
            results.append(row)
        
        # Rate limiting to be polite to the API
        time.sleep(0.1)
        
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(results)

def main():
    st.set_page_config(layout="wide", page_title="MF Analyzer Pro")
    
    # --- Sidebar Controls ---
    st.sidebar.title("⚙️ Settings")
    
    # Risk Free Rate Input
    rf_rate = st.sidebar.number_input(
        "Risk Free Rate (%)", 
        min_value=0.0, max_value=15.0, value=7.0, step=0.5,
        help="Used for Sharpe & Sortino Ratio calculations. Default 7.0% (approx G-Sec yield)."
    )
    
    # Category Selection
    categories = ['All Funds', 'Large Cap', 'Mid Cap', 'Small Cap', 'Large & Mid Cap', 'Multi Cap', 'International']
    selected_category = st.sidebar.selectbox("Select Category", categories)

    # --- Main Content ---
    st.title(f"📊 {selected_category} Fund Analyzer")
    st.markdown("""
    All funds in the selected category will be analyzed automatically.
    **Note:** Fetching data takes time (approx 0.5s per fund).
    """)
    
    # 1. Fetch Master List
    with st.spinner("Fetching Scheme Master List..."):
        all_schemes = MutualFundAnalyzer.get_all_schemes()
        
    if not all_schemes:
        st.error("Failed to connect to API. Please try again later.")
        return

    # 2. Filter List
    cat_schemes = MutualFundAnalyzer.filter_schemes_by_category(all_schemes, selected_category)
    st.info(f"Found **{len(cat_schemes)}** Regular Growth schemes in {selected_category}.")
    
    # 3. Automatically Process All Funds
    if cat_schemes:
        with st.container():
            df_results = process_funds_batch(cat_schemes, rf_rate)
            
            if not df_results.empty:
                # Formatting and Display
                st.subheader("Performance Metrics")
                
                # Apply styling to highlight good/bad numbers
                st.dataframe(
                    df_results.style.format({
                        'Latest NAV': '₹{:.2f}',
                        '1W (%)': '{:.2f}%',
                        '1M (%)': '{:.2f}%',
                        '3M (%)': '{:.2f}%',
                        '1Y (%)': '{:.2f}%',
                        '3Y CAGR (%)': '{:.2f}%',
                        'Vol (%)': '{:.2f}%',
                        'Sharpe': '{:.2f}',
                        'Sortino': '{:.2f}',
                        'Max DD (%)': '{:.2f}%'
                    }).background_gradient(subset=['1W (%)', '1M (%)', '3M (%)', '1Y (%)', '3Y CAGR (%)', 'Sharpe', 'Sortino'], cmap='Greens'),
                    use_container_width=True,
                    height=400
                )
                
                # Simple Correlation Matrix if enough data
                #  
                    
            else:
                st.warning("No data could be fetched for the selected funds.")

if __name__ == "__main__":
    main()
