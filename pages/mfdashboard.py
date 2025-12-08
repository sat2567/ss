import streamlit as st
import requests
import pandas as pd
from datetime import timedelta
import time
from typing import Dict, List, Optional
import numpy as np
import difflib
import re

# --- Configuration ---
BASE_URL = "https://api.mfapi.in"

# --- USER DEFINED FUND LIST (STRICT FILTER) ---
# This dictionary contains the exact funds requested.
USER_FUNDS_CONFIG = {
    "LARGE CAP": [
        "Aditya Birla SL Large Cap Fund-Reg(G)", "Axis Large Cap Fund-Reg(G)", "Bajaj Finserv Large Cap Fund-Reg(G)",
        "Bandhan Large Cap Fund-Reg(G)", "Bank of India Large Cap Fund-Reg(G)", "Baroda BNP Paribas Large Cap Fund-Reg(G)",
        "Canara Rob Large Cap Fund-Reg(G)", "DSP Large Cap Fund-Reg(G)", "Edelweiss Large Cap Fund-Reg(G)",
        "Franklin India Large Cap Fund(G)", "Groww Largecap Fund-Reg(G)", "HDFC Large Cap Fund(G)",
        "HSBC Large Cap Fund(G)", "ICICI Pru Large Cap Fund(G)", "ITI Large Cap Fund-Reg(G)",
        "Invesco India Largecap Fund-Reg(G)", "JM Large Cap Fund-Reg(G)", "Kotak Large Cap Fund(IDCW)",
        "LIC MF Large Cap Fund-Reg(G)", "Mahindra Manulife Large Cap Fund-Reg(G)", "Mirae Asset Large Cap Fund-Reg(G)",
        "Motilal Oswal Large Cap Fund-Reg(G)", "Nippon India Large Cap Fund(G)", "PGIM India Large Cap Fund(G)",
        "Qsif Equity Ex-Top 100 Long-Short Fund-Reg(G)", "Quant Large Cap Fund-Reg(G)", "SBI Large Cap Fund-Reg(G)",
        "Samco Large Cap Fund-Reg(G)", "Sundaram Large Cap Fund-Reg(G)", "Tata Large Cap Fund-Reg(G)",
        "Taurus Large Cap Fund-Reg(G)", "UTI Large Cap Fund-Reg(IDCW)", "Union Largecap Fund-Reg(G)",
        "WOC Large Cap Fund-Reg(G)"
    ],
    "SMALL CAP": [
        "Aditya Birla SL Small Cap Fund(G)", "Axis Small Cap Fund-Reg(G)", "Bajaj Finserv Small Cap Fund-Reg(G)",
        "Bandhan Small Cap Fund-Reg(G)", "Bank of India Small Cap Fund-Reg(G)", "Baroda BNP Paribas Small Cap Fund-Reg(G)",
        "Canara Rob Small Cap Fund-Reg(G)", "DSP Small Cap Fund-Reg(G)", "Edelweiss Small Cap Fund-Reg(G)",
        "Franklin India Small Cap Fund(G)", "HDFC Small Cap Fund-Reg(G)", "HSBC Small Cap Fund-Reg(G)",
        "Helios Small Cap Fund-Reg(G)", "ICICI Pru Smallcap Fund(G)", "ITI Small Cap Fund-Reg(G)",
        "Invesco India Smallcap Fund-Reg(G)", "JM Small Cap Fund-Reg(G)", "Kotak Small Cap Fund(G)",
        "LIC MF Small Cap Fund-Reg(G)", "Mahindra Manulife Small Cap Fund-Reg(G)", "Mirae Asset Small Cap Fund-Reg(G)",
        "Motilal Oswal Small Cap Fund-Reg(G)", "Nippon India Small Cap Fund(G)", "PGIM India Small Cap Fund-Reg(G)",
        "Quant Small Cap Fund(G)", "Quantum Small Cap Fund-Reg(G)", "SBI Small Cap Fund-Reg(G)",
        "Sundaram Small Cap Fund(G)", "TRUSTMF Small Cap Fund-Reg(G)", "Tata Small Cap Fund-Reg(G)",
        "UTI Small Cap Fund-Reg(G)", "Union Small Cap Fund-Reg(G)"
    ],
    "MID CAP": [
        "Aditya Birla SL Midcap Fund(G)", "Axis Midcap Fund-Reg(G)", "Bandhan Midcap Fund-Reg(G)",
        "Baroda BNP Paribas Mid Cap Fund-Reg(G)", "DSP Midcap Fund-Reg(G)", "Edelweiss Mid Cap Fund-Reg(G)",
        "Franklin India Mid Cap Fund(G)", "HDFC Mid Cap Fund-Reg(G)", "HSBC Midcap Fund-Reg(G)",
        "ICICI Pru Midcap Fund(G)", "ITI Mid Cap Fund-Reg(G)", "Invesco India Midcap Fund-Reg(G)",
        "Kotak Midcap Fund-Reg(G)", "LIC MF Midcap Fund-Reg(G)", "Mahindra Manulife Mid Cap Fund-Reg(G)",
        "Mirae Asset Midcap Fund-Reg(G)", "Motilal Oswal Midcap Fund-Reg(G)", "Nippon India Growth Mid Cap Fund(G)",
        "PGIM India Midcap Fund-Reg(G)", "Quant Mid Cap Fund(G)", "SBI Midcap Fund-Reg(G)",
        "Sundaram Mid Cap Fund-Reg(G)", "Tata Mid Cap Fund-Reg(G)", "Taurus Mid Cap Fund-Reg(G)",
        "UTI Mid Cap Fund-Reg(G)", "Union Midcap Fund-Reg(G)"
    ],
    "LARGE & MID CAP": [
        "Axis Large & Mid Cap Fund-Reg(G)", "Bajaj Finserv Large and Mid Cap Fund-Reg(G)", "Bandhan Large & Mid Cap Fund-Reg(G)",
        "Bank of India Large & Mid Cap Fund-Reg(G)", "Baroda BNP Paribas Large & Mid Cap Fund-Reg(G)",
        "Canara Rob Large and Mid Cap Fund-Reg(G)", "DSP Large & Mid Cap Fund-Reg(G)", "Edelweiss Large & Mid Cap Fund-Reg(G)",
        "Franklin India Large & Mid Cap Fund(G)", "HDFC Large and Mid Cap Fund-Reg(G)", "HSBC Large & Mid Cap Fund-Reg(G)",
        "Helios Large & Mid Cap Fund-Reg(G)", "ICICI Pru Large & Mid Cap Fund(G)", "ITI Large & Mid Cap Fund-Reg(G)",
        "Invesco India Large & Mid Cap Fund-Reg(G)", "JM Large & Mid Cap Fund-Reg(G)", "Kotak Large & Midcap Fund(G)",
        "LIC MF Large & Midcap Fund-Reg(G)", "Mahindra Manulife Large & Mid Cap Fund-Reg(G)",
        "Mirae Asset Large & Midcap Fund-Reg(G)", "Motilal Oswal Large & Midcap Fund-Reg(G)",
        "Navi Large & Midcap Fund-Reg(G)", "Nippon India Vision Large & Mid Cap Fund(G)", "PGIM India Large and Mid Cap Fund(G)",
        "Quant Large & Mid Cap Fund(G)", "SBI Large & Midcap Fund-Reg(IDCW)", "Samco Large & Mid Cap Fund-Reg(G)",
        "Sundaram Large and Mid Cap Fund(G)", "Tata Large & Mid Cap Fund-Reg(G)", "UTI Large & Mid Cap Fund-Reg(G)",
        "Union Large & Midcap Fund-Reg(G)", "WOC Large & Mid Cap Fund-Reg(G)"
    ],
    "MULTI CAP": [
        "Aditya Birla SL Multi-Cap Fund-Reg(G)", "Axis Multicap Fund-Reg(G)", "Bajaj Finserv Multi Cap Fund-Reg(G)",
        "Bandhan Multi Cap Fund-Reg(G)", "Bank of India Multi Cap Fund-Reg(G)", "Baroda BNP Paribas Multi Cap Fund-Reg(G)",
        "Canara Rob Multi Cap Fund-Reg(G)", "DSP Multicap Fund-Reg(G)", "Diviniti Equity Long Short Fund-Reg(G)",
        "Edelweiss Multi Cap Fund-Reg(G)", "Franklin India Multi Cap Fund-Reg(G)", "Groww Multicap Fund-Reg(G)",
        "HDFC Multi Cap Fund-Reg(G)", "HSBC Multi Cap Fund-Reg(G)", "ICICI Pru Multicap Fund(G)",
        "ITI Multi-Cap Fund-Reg(G)", "Invesco India Multicap Fund-Reg(G)", "Kotak Multicap Fund-Reg(G)",
        "LIC MF Multi Cap Fund-Reg(G)", "Mahindra Manulife Multi Cap Fund-Reg(G)", "Mirae Asset Multicap Fund-Reg(G)",
        "Motilal Oswal Multi Cap Fund-Reg(G)", "Nippon India Multi Cap Fund(G)", "PGIM India Multi Cap Fund-Reg(G)",
        "Qsif Equity Long-Short Fund-Reg(G)", "Quant Multi Cap Fund(G)", "SBI Multicap Fund-Reg(G)",
        "Samco Multi Cap Fund-Reg(G)", "Sundaram Multi Cap Fund(G)", "TRUSTMF Multi Cap Fund-Reg(G)",
        "Tata Multicap Fund-Reg(G)", "UTI Multi Cap Fund-Reg(G)", "Union Multicap Fund-Reg(G)",
        "WOC Multi Cap Fund-Reg(G)"
    ],
    "INTERNATIONAL": [
        "Aditya Birla SL Global Emerging Opp Fund(G)", "Aditya Birla SL Global Excellence Equity FoF(G)",
        "Aditya Birla SL Intl. Equity Fund(G)", "Aditya Birla SL US Equity Passive FOF-Reg(G)",
        "Aditya Birla SL US Treasury 1-3 year Bond ETFs FoF-Reg(G)", "Aditya Birla SL US Treasury 3-10 year Bond ETFs FoF-Reg(G)",
        "Axis Global Equity Alpha FoF-Reg(G)", "Axis Global Innovation FoF-Reg(G)", "Axis Greater China Equity FoF-Reg(G)",
        "Axis US Specific Equity Passive FOF-Reg(G)", "Axis US Specific Treasury Dynamic Debt Passive FoF-Reg(G)",
        "Bandhan US Specific Equity Active FoF-Reg(G)", "Bandhan US Treasury Bond 0-1 year specific Debt Passive FOF-Reg(G)",
        "Baroda BNP Paribas Aqua FoF-Reg(G)", "DSP Global Clean Energy Overseas Equity Omni FoF-Reg(G)",
        "DSP Global Innovation Overseas Equity Omni FoF-Reg(G)", "DSP US Specific Debt Passive FoF-Reg(G)",
        "DSP US Specific Equity Omni FoF-Reg(G)", "DSP World Mining Overseas Equity Omni FoF-Reg(G)",
        "Edelweiss ASEAN Equity Off-Shore Fund-Reg(G)", "Edelweiss Emerging Markets Opp Eq. Offshore Fund-Reg(G)",
        "Edelweiss Europe Dynamic Equity Off-shore Fund-Reg(G)", "Edelweiss Greater China Equity Off-shore Fund-Reg(G)",
        "Edelweiss US Technology Equity FOF-Reg(G)", "Edelweiss US Value Equity Offshore Fund-Reg(G)",
        "Franklin Asian Equity Fund(G)", "Franklin U.S. Opportunities Equity Active FOF(G)",
        "HDFC Developed World Overseas Equity Passive FOF-Reg(G)", "HSBC Asia Pacific (Ex Japan) DYF-Reg(G)",
        "HSBC Brazil Fund(G)", "HSBC Global Emerging Markets Fund(G)", "HSBC Global Equity Climate Change FoF-Reg(G)",
        "ICICI Pru Global Advantage Fund(FOF)(G)", "ICICI Pru Global Stable Equity Fund(FOF)(G)",
        "ICICI Pru Strategic Metal and Energy Equity FoF-Reg(G)", "ICICI Pru US Bluechip Equity Fund(G)",
        "Invesco India - Invesco EQQQ NASDAQ-100 ETF FoF-Reg(G)", "Invesco India - Invesco Global Consumer Trends FoF-Reg(G)",
        "Invesco India - Invesco Global Equity Income FoF-Reg(G)", "Invesco India - Invesco Pan European Equity FoF-Reg(G)",
        "Kotak Global Emerging Market Overseas Equity Omni FOF(G)", "Kotak Global Innovation Overseas Equity Omni FOF-Reg(G)",
        "Kotak International REIT Overseas Equity Omni FOF-Reg(G)", "Kotak US Specific Equity Passive FOF-Reg(G)",
        "Mahindra Manulife Asia Pacific REITs FOF-Reg(G)", "Mirae Asset Global Electric & Autonomous Vehicles Equity Passive FOF-Reg(G)",
        "Mirae Asset Global X Artificial Intelligence & Technology ETF FoF-Reg(G)", "Mirae Asset Hang Seng TECH ETF FoF-Reg(G)",
        "Mirae Asset NYSE FANG+ETF FoF-Reg(G)", "Mirae Asset S&P 500 Top 50 ETF FoF-Reg(G)",
        "Motilal Oswal Developed Market Ex US ETFs Overseas Equity Passive FOF-Reg(G)", "Motilal Oswal Nasdaq 100 FOF-Reg(G)",
        "Navi US Nasdaq100 FOF-Reg(G)", "Navi US Total Stock Market FoF-Reg(G)", "Nippon India Japan Equity Fund(G)",
        "Nippon India Taiwan Equity Fund-Reg(G)", "Nippon India US Equity Opp Fund(G)", "PGIM India Emerging Markets Equity FoF(G)",
        "PGIM India Global Equity Opp FoF(G)", "PGIM India Global Select Real Estate Securities FoF-Reg(G)",
        "SBI US Specific Equity Active FoF-Reg(G)", "Sundaram Global Brand Theme - Equity Active FoF(G)"
    ]
}

class FundNameMatcher:
    """Helper to map user's abbreviated names to API's verbose names."""
    
    ABBREVIATIONS = {
        "SL": "Sun Life",
        "Pru": "Prudential",
        "Rob": "Robeco",
        "WOC": "WhiteOak",
        "Intl": "International",
        "Opp": "Opportunities",
        "Eq": "Equity"
    }

    @staticmethod
    def normalize_user_name(name: str) -> dict:
        """Parses the user provided name into search components."""
        # 1. Detect IDCW vs Growth
        is_idcw = "IDCW" in name or "Dividend" in name
        
        # 2. Handle Abbreviations
        clean_name = name
        # Remove suffixes like -Reg(G), (G), etc.
        clean_name = re.sub(r'[-\s]*Reg(\(G\))?', '', clean_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'[-\s]*\(G\)', '', clean_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'[-\s]*\(IDCW\)', '', clean_name, flags=re.IGNORECASE)
        
        # Expand common abbreviations
        parts = clean_name.split()
        expanded_parts = [FundNameMatcher.ABBREVIATIONS.get(p, p) for p in parts]
        
        return {
            "search_terms": expanded_parts,
            "is_idcw": is_idcw,
            "original": name
        }

    @staticmethod
    def is_match(api_scheme: dict, search_criteria: dict) -> float:
        """Scores how well an API scheme matches the user criteria."""
        api_name = api_scheme.get("schemeName", "").lower()
        
        # 1. Filter Direct Plans (User requested Reg)
        if "direct" in api_name:
            return 0.0
            
        # 2. Filter Growth vs IDCW
        has_idcw = "idcw" in api_name or "dividend" in api_name
        if search_criteria["is_idcw"] != has_idcw:
            # User wanted IDCW but this is Growth (or vice versa)
            return 0.0
            
        # 3. Keyword Matching
        match_score = 0
        search_terms = [t.lower() for t in search_criteria["search_terms"]]
        
        # Check if all key terms are present (AMC Name, Type)
        # We give higher weight to the first word (AMC name)
        if search_terms[0] not in api_name:
            return 0.0
            
        # Calculate fuzzy similarity
        clean_api_name = api_name.replace(" - ", " ").replace(" regular plan ", "")
        search_string = " ".join(search_terms)
        
        # Use SequenceMatcher for similarity
        score = difflib.SequenceMatcher(None, search_string, clean_api_name).ratio()
        return score

class MutualFundAnalyzer:
    
    @staticmethod
    @st.cache_data(ttl=86400, show_spinner=False)
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
    @st.cache_data(ttl=3600)
    def match_schemes(user_category_funds: List[str], all_schemes: List[Dict]) -> List[Dict]:
        """Maps user specific names to API scheme codes."""
        matched_schemes = []
        
        for user_fund_name in user_category_funds:
            criteria = FundNameMatcher.normalize_user_name(user_fund_name)
            
            best_match = None
            best_score = 0.0
            
            # Search through master list
            for scheme in all_schemes:
                score = FundNameMatcher.is_match(scheme, criteria)
                if score > best_score:
                    best_score = score
                    best_match = scheme
            
            # Threshold for accepting a match (0.4 is lenient but safe given the strict filtering steps)
            if best_match and best_score > 0.4:
                # Inject the user's preferred name for display consistency
                best_match['displayName'] = user_fund_name 
                matched_schemes.append(best_match)
            # Optional: Else log missing fund
            
        return matched_schemes

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
            
            # Data Cleaning: Remove non-positive NAVs which cause calculation errors
            df = df[df['nav'] > 0]
            
            # Sort by date ascending
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
        if df.empty or len(df) < 2:
            return {k: np.nan for k in ["1W", "1M", "3M", "6M", "1Y", "3Y_CAGR", "5Y_CAGR"]}
            
        latest_date = df.index.max()
        latest_nav = df.loc[latest_date, 'nav']
        
        periods = {
            "1W": timedelta(weeks=1),
            "1M": timedelta(days=30),
            "3M": timedelta(days=90),
            "6M": timedelta(days=180),
            "1Y": timedelta(days=365),
            "3Y_CAGR": timedelta(days=365*3),
            "5Y_CAGR": timedelta(days=365*5)
        }
        
        returns = {}
        for label, delta in periods.items():
            target_date = latest_date - delta
            
            # Find closest date
            idx_loc = df.index.get_indexer([target_date], method='pad')[0]
            
            if idx_loc != -1:
                past_date = df.index[idx_loc]
                past_nav = df.loc[past_date, 'nav']
                days_diff = (latest_date - past_date).days
                
                # Check if data point is relevant (within 7 days margin)
                if days_diff >= (delta.days - 10): 
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
        if len(df) < 2: return np.nan
        returns = df['nav'].pct_change().dropna()
        return returns.std() * np.sqrt(252) * 100

    @staticmethod
    def calculate_sharpe_ratio(df: pd.DataFrame, rf_percent: float) -> float:
        if len(df) < 252: return np.nan 
        
        start_nav = df['nav'].iloc[0]
        end_nav = df['nav'].iloc[-1]
        days = (df.index[-1] - df.index[0]).days
        
        if days <= 0: return np.nan
        ann_return_decimal = (end_nav / start_nav) ** (365.25 / days) - 1
        rf_decimal = rf_percent / 100
        
        returns = df['nav'].pct_change().dropna()
        vol_decimal = returns.std() * np.sqrt(252)
        
        if vol_decimal == 0: return np.nan
        return (ann_return_decimal - rf_decimal) / vol_decimal

    @staticmethod
    def calculate_sortino_ratio(df: pd.DataFrame, rf_percent: float) -> float:
        if len(df) < 252: return np.nan
        
        start_nav = df['nav'].iloc[0]
        end_nav = df['nav'].iloc[-1]
        days = (df.index[-1] - df.index[0]).days
        ann_return_decimal = (end_nav / start_nav) ** (365.25 / days) - 1
        rf_decimal = rf_percent / 100
        
        returns = df['nav'].pct_change().dropna()
        daily_rf = (1 + rf_decimal) ** (1/252) - 1
        excess_returns = returns - daily_rf
        negative_returns = excess_returns[excess_returns < 0]
        
        if len(negative_returns) == 0: return np.nan
            
        downside_variance = (negative_returns ** 2).sum() / len(returns)
        downside_dev_ann = np.sqrt(downside_variance) * np.sqrt(252)
        
        if downside_dev_ann == 0: return np.nan
        
        return (ann_return_decimal - rf_decimal) / downside_dev_ann

    @staticmethod
    def calculate_max_drawdown(df: pd.DataFrame) -> float:
        if df.empty: return np.nan
        nav = df['nav']
        peak = nav.expanding().max()
        drawdown = (nav - peak) / peak
        return drawdown.min() * 100

def process_funds_batch(matched_schemes: List[Dict], rf_rate: float) -> pd.DataFrame:
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(matched_schemes)
    
    for i, scheme in enumerate(matched_schemes):
        progress = (i + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"Analyzing {i+1}/{total}: {scheme.get('displayName', scheme['schemeName'])}...")
        
        code = scheme['schemeCode']
        df = MutualFundAnalyzer.get_scheme_data(code)
        
        if not df.empty and len(df) > 30:
            metrics = MutualFundAnalyzer.get_return_metrics(df)
            vol = MutualFundAnalyzer.calculate_volatility(df)
            sharpe = MutualFundAnalyzer.calculate_sharpe_ratio(df, rf_rate)
            sortino = MutualFundAnalyzer.calculate_sortino_ratio(df, rf_rate)
            mdd = MutualFundAnalyzer.calculate_max_drawdown(df)
            
            row = {
                'Fund Name': scheme.get('displayName', scheme['schemeName']), # Use user name preference
                'Latest NAV': df['nav'].iloc[-1],
                '1W (%)': metrics['1W'],
                '1M (%)': metrics['1M'],
                '3M (%)': metrics['3M'],
                '1Y (%)': metrics['1Y'],
                '3Y CAGR (%)': metrics['3Y_CAGR'],
                '5Y CAGR (%)': metrics['5Y_CAGR'],
                'Vol (%)': vol,
                'Sharpe': sharpe,
                'Sortino': sortino,
                'Max DD (%)': mdd
            }
            results.append(row)
        
        time.sleep(0.05) 
        
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(results)

def main():
    st.set_page_config(layout="wide", page_title="Strict Fund Analyzer")
    
    # --- Sidebar ---
    st.sidebar.title("⚙️ Settings")
    rf_rate = st.sidebar.number_input("Risk Free Rate (%)", 5.0, 15.0, 7.0, 0.5)
    
    # Categories strictly from user list
    categories = list(USER_FUNDS_CONFIG.keys())
    selected_category = st.sidebar.selectbox("Select Category", categories)
    
    st.title(f"📊 {selected_category} Fund Analysis")
    st.markdown("Fetching data strictly for the requested fund list.")

    # 1. Fetch Master List (Once)
    with st.spinner("Connecting to AMFI/MFAPI..."):
        all_schemes = MutualFundAnalyzer.get_all_schemes()
        
    if not all_schemes:
        st.error("Could not fetch scheme master list.")
        return

    # 2. Match User Funds to API Codes
    target_list = USER_FUNDS_CONFIG[selected_category]
    matched = MutualFundAnalyzer.match_schemes(target_list, all_schemes)
    
    st.info(f"Identified data for **{len(matched)}** out of **{len(target_list)}** requested funds.")
    
    # Debug info for missing funds (optional)
    if len(matched) < len(target_list):
        found_names = [m.get('displayName') for m in matched]
        missing = [f for f in target_list if f not in found_names]
        with st.expander("See funds with no matching data (likely new or name mismatch)"):
            st.write(missing)

    # 3. Process Data
    if matched:
        df_results = process_funds_batch(matched, rf_rate)
        
        if not df_results.empty:
            # Display
            st.subheader("Performance Matrix")
            
            format_dict = {
                'Latest NAV': '₹{:.2f}',
                '1W (%)': '{:.2f}%', '1M (%)': '{:.2f}%', '3M (%)': '{:.2f}%',
                '1Y (%)': '{:.2f}%', '3Y CAGR (%)': '{:.2f}%', '5Y CAGR (%)': '{:.2f}%',
                'Vol (%)': '{:.2f}%', 'Sharpe': '{:.2f}', 'Sortino': '{:.2f}',
                'Max DD (%)': '{:.2f}%'
            }
            
            st.dataframe(
                df_results.style.format(format_dict)
                .background_gradient(subset=['1Y (%)', '3Y CAGR (%)', 'Sharpe', 'Sortino'], cmap='RdYlGn'),
                use_container_width=True,
                height=600
            )
        else:
            st.warning("No historical data available for these funds.")
    else:
        st.warning("No matching funds found in the API database.")

if __name__ == "__main__":
    main()
