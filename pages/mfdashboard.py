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

# --- USER DEFINED FUND LIST ---
USER_FUNDS_CONFIG = {
    "LARGE CAP": [
        "Aditya Birla SL Large Cap Fund", "Axis Large Cap Fund", "Bajaj Finserv Large Cap Fund",
        "Bandhan Large Cap Fund", "Bank of India Large Cap Fund", "Baroda BNP Paribas Large Cap Fund",
        "Canara Rob Large Cap Fund", "DSP Large Cap Fund", "Edelweiss Large Cap Fund",
        "Franklin India Large Cap Fund", "Groww Largecap Fund", "HDFC Large Cap Fund",
        "HSBC Large Cap Fund", "ICICI Pru Large Cap Fund", "ITI Large Cap Fund",
        "Invesco India Largecap Fund", "JM Large Cap Fund", "Kotak Large Cap Fund",
        "LIC MF Large Cap Fund", "Mahindra Manulife Large Cap Fund", "Mirae Asset Large Cap Fund",
        "Motilal Oswal Large Cap Fund", "Nippon India Large Cap Fund", "PGIM India Large Cap Fund",
        "Quant Large Cap Fund", "SBI Large Cap Fund",
        "Samco Large Cap Fund", "Sundaram Large Cap Fund", "Tata Large Cap Fund",
        "Taurus Large Cap Fund", "UTI Large Cap Fund", "Union Largecap Fund",
        "WhiteOak Large Cap Fund"
    ],
    "MID CAP": [
        "Aditya Birla SL Midcap Fund", "Axis Midcap Fund", "Bandhan Midcap Fund",
        "Baroda BNP Paribas Mid Cap Fund", "DSP Midcap Fund", "Edelweiss Mid Cap Fund",
        "Franklin India Mid Cap Fund", "HDFC Mid Cap Fund", "HSBC Midcap Fund",
        "ICICI Pru Midcap Fund", "ITI Mid Cap Fund", "Invesco India Midcap Fund",
        "Kotak Midcap Fund", "LIC MF Midcap Fund", "Mahindra Manulife Mid Cap Fund",
        "Mirae Asset Midcap Fund", "Motilal Oswal Midcap Fund", "Nippon India Growth Mid Cap Fund",
        "PGIM India Midcap Fund", "Quant Mid Cap Fund", "SBI Midcap Fund",
        "Sundaram Mid Cap Fund", "Tata Mid Cap Fund", "Taurus Mid Cap Fund",
        "UTI Mid Cap Fund", "Union Midcap Fund"
    ],
    "SMALL CAP": [
        "Aditya Birla SL Small Cap Fund", "Axis Small Cap Fund", "Bajaj Finserv Small Cap Fund",
        "Bandhan Small Cap Fund", "Bank of India Small Cap Fund", "Baroda BNP Paribas Small Cap Fund",
        "Canara Rob Small Cap Fund", "DSP Small Cap Fund", "Edelweiss Small Cap Fund",
        "Franklin India Small Cap Fund", "HDFC Small Cap Fund", "HSBC Small Cap Fund",
        "Helios Small Cap Fund", "ICICI Pru Smallcap Fund", "ITI Small Cap Fund",
        "Invesco India Smallcap Fund", "JM Small Cap Fund", "Kotak Small Cap Fund",
        "LIC MF Small Cap Fund", "Mahindra Manulife Small Cap Fund", "Mirae Asset Small Cap Fund",
        "Motilal Oswal Small Cap Fund", "Nippon India Small Cap Fund", "PGIM India Small Cap Fund",
        "Quant Small Cap Fund", "SBI Small Cap Fund",
        "Sundaram Small Cap Fund", "Tata Small Cap Fund",
        "UTI Small Cap Fund", "Union Small Cap Fund"
    ],
    "LARGE & MID CAP": [
        "Axis Large & Mid Cap Fund", "Bandhan Large & Mid Cap Fund",
        "Canara Rob Large and Mid Cap Fund", "DSP Large & Mid Cap Fund", "Edelweiss Large & Mid Cap Fund",
        "Franklin India Large & Mid Cap Fund", "HDFC Large and Mid Cap Fund", "HSBC Large & Mid Cap Fund",
        "ICICI Pru Large & Mid Cap Fund", "Kotak Large & Midcap Fund",
        "LIC MF Large & Midcap Fund", "Mahindra Manulife Large & Mid Cap Fund",
        "Mirae Asset Large & Midcap Fund", "Motilal Oswal Large & Midcap Fund",
        "Nippon India Vision Large & Mid Cap Fund", "PGIM India Large and Mid Cap Fund",
        "Quant Large & Mid Cap Fund", "SBI Large & Midcap Fund",
        "Sundaram Large and Mid Cap Fund", "Tata Large & Mid Cap Fund", "UTI Large & Mid Cap Fund",
        "Union Large & Midcap Fund"
    ]
}

# --- STRICT CATEGORY RULES ---
CATEGORY_RULES = {
    "LARGE CAP": {
        "required": ["large cap", "largecap", "bluechip", "frontline", "top 100"],
        "forbidden": ["mid", "small", "flexi", "multi", "focused", "opportunities", "active", "advantage", "balanced", "hybrid", "tax", "elss", "index", "etf", "nifty", "sensex", "passive", "overseas", "global", "quant"]
    },
    "MID CAP": {
        "required": ["mid cap", "midcap", "emerging", "growth", "prima"],
        "forbidden": ["large", "small", "bluechip", "frontline", "flexi", "multi", "focused", "opportunities", "index", "etf", "hybrid", "balanced"]
    },
    "SMALL CAP": {
        "required": ["small cap", "smallcap", "emerging", "discovery"],
        "forbidden": ["large", "mid", "bluechip", "frontline", "flexi", "multi", "focused", "index", "etf", "hybrid"]
    },
    "LARGE & MID CAP": {
        "required": ["large & mid", "large and mid", "large & midcap", "large and midcap"],
        "forbidden": ["small", "flexi", "multi", "bluechip", "focused", "index", "etf"]
    }
}

class FundNameMatcher:
    @staticmethod
    def clean_name(name: str) -> str:
        name = name.lower()
        name = re.sub(r'[-\s]*regular\s*plan', '', name)
        name = re.sub(r'[-\s]*direct\s*plan', '', name)
        name = re.sub(r'[-\s]*growth\s*option', '', name)
        name = re.sub(r'\((g|idcw|d)\)', '', name)
        name = name.replace("aditya birla sl", "aditya birla sun life")
        name = name.replace("canara rob", "canara robeco")
        name = name.replace("woc", "whiteoak")
        return name.strip()

    @staticmethod
    def check_category_constraints(api_name_clean: str, category: str, amc_name: str) -> bool:
        rules = CATEGORY_RULES.get(category, {})
        required = rules.get("required", [])
        forbidden = rules.get("forbidden", [])
        
        has_required = any(req in api_name_clean for req in required)
        if not has_required: return False

        for bad_word in forbidden:
            if bad_word == "quant" and "quant" in amc_name: continue
            if bad_word in api_name_clean: return False 
        return True

    @staticmethod
    def get_best_match(user_fund_name: str, all_schemes: List[Dict], category: str) -> Optional[Dict]:
        clean_user = FundNameMatcher.clean_name(user_fund_name)
        user_tokens = clean_user.split()
        amc_token = user_tokens[0] if user_tokens else ""

        best_match = None
        best_score = 0.0

        for scheme in all_schemes:
            api_name_raw = scheme["schemeName"]
            if "Direct" in api_name_raw: continue
            if "IDCW" in api_name_raw or "Dividend" in api_name_raw: continue
            
            clean_api = FundNameMatcher.clean_name(api_name_raw)

            if amc_token not in clean_api: continue
            if not FundNameMatcher.check_category_constraints(clean_api, category, amc_token): continue

            score = difflib.SequenceMatcher(None, clean_user, clean_api).ratio()
            if score > best_score:
                best_score = score
                best_match = scheme

        if best_score > 0.50: return best_match
        return None

class MutualFundAnalyzer:
    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_schemes() -> List[Dict]:
        try:
            response = requests.get(f"{BASE_URL}/mf", timeout=30)
            response.raise_for_status()
            return response.json()
        except: return []

    @staticmethod
    # Lowered TTL to ensure we don't hold bad data
    @st.cache_data(ttl=600)
    def get_scheme_data_clean(scheme_code: str) -> pd.DataFrame:
        try:
            response = requests.get(f"{BASE_URL}/mf/{scheme_code}", timeout=10)
            data = response.json()
            if not data or 'data' not in data: return pd.DataFrame()
            
            df = pd.DataFrame(data['data'])
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
            
            # Remove 0 or negative NAVs
            df = df[df['nav'] > 0].dropna()
            
            # Sort is CRITICAL for asof()
            df = df.sort_values('date')
            
            # Set index and remove duplicates
            df = df.set_index('date')
            df = df[~df.index.duplicated(keep='last')]
            
            return df
        except: return pd.DataFrame()

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> Dict:
        """
        Robust metric calculation using 'asof' to find nearest past date.
        """
        # Define exact output keys
        metrics = {
            'Latest NAV': np.nan,
            '1-Week': np.nan, '2-Weeks': np.nan, '3-Weeks': np.nan, '1-Month': np.nan,
            '1-Year': np.nan, '3-Year': np.nan, '5-Year': np.nan
        }

        if len(df) < 7: return metrics # Not enough data
        
        latest_nav = df['nav'].iloc[-1]
        last_date = df.index[-1]
        
        metrics['Latest NAV'] = latest_nav
        
        # Configuration for periods
        period_days = {
            '1-Week': 7,
            '2-Weeks': 14,
            '3-Weeks': 21,
            '1-Month': 30,
            '1-Year': 365,
            '3-Year': 365*3,
            '5-Year': 365*5
        }
        
        for key, days in period_days.items():
            target_date = last_date - timedelta(days=days)
            
            # .asof() finds the NAV at target_date, or the most recent one before it.
            # This handles weekends/holidays automatically.
            try:
                # We slice the dataframe to ensure we are looking at valid history
                if target_date < df.index[0]:
                    metrics[key] = np.nan
                    continue
                    
                start_nav = df['nav'].asof(target_date)
                
                if pd.isna(start_nav):
                    metrics[key] = np.nan
                    continue

                # Calculation
                if days < 365:
                    # Absolute Return
                    ret = ((latest_nav - start_nav) / start_nav) * 100
                else:
                    # CAGR
                    years = days/365
                    ret = ((latest_nav/start_nav)**(1/years) - 1)*100
                
                metrics[key] = ret
            except:
                metrics[key] = np.nan

        return metrics

def main():
    st.set_page_config(layout="wide", page_title="Smart Fund Analyzer")
    st.sidebar.title("Fund Analyzer")
    
    # 1. Force Cache Clear Button
    if st.sidebar.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    category = st.sidebar.selectbox("Select Category", list(USER_FUNDS_CONFIG.keys()))
    
    st.title(f"Analysis: {category}")
    st.info("✅ Short Term (<1Y): Absolute Returns | Long Term (>1Y): CAGR")

    with st.spinner("Connecting to API..."):
        all_schemes = MutualFundAnalyzer.get_all_schemes()

    if not all_schemes:
        st.error("API Error. Please try again later.")
        return

    target_funds = USER_FUNDS_CONFIG[category]
    results = []
    
    progress = st.progress(0)
    status_text = st.empty()
    
    # Debug container
    with st.expander("Show Calculation Debugger (Click if data looks missing)", expanded=False):
        debug_container = st.container()
    
    for i, user_fund in enumerate(target_funds):
        progress.progress((i+1)/len(target_funds))
        status_text.text(f"Fetching: {user_fund}")
        
        match = FundNameMatcher.get_best_match(user_fund, all_schemes, category)
        
        if match:
            df = MutualFundAnalyzer.get_scheme_data_clean(match['schemeCode'])
            if not df.empty:
                mets = MutualFundAnalyzer.calculate_metrics(df)
                
                # Direct mapping - Keys match calculate_metrics output exactly
                row = {
                    "Fund Name": user_fund,
                    "API Name": match['schemeName'],
                    "Latest NAV": mets['Latest NAV'],
                    "1-Week": mets['1-Week'],
                    "2-Weeks": mets['2-Weeks'],
                    "3-Weeks": mets['3-Weeks'],
                    "1-Month": mets['1-Month'],
                    "1-Year": mets['1-Year'],
                    "3-Year": mets['3-Year'],
                    "5-Year": mets['5-Year']
                }
                results.append(row)
                
                # Print the first successful calculation to debug area
                if len(results) == 1:
                    debug_container.write(f"Debug First Fund ({user_fund}):")
                    debug_container.write(mets)
        
        time.sleep(0.01)

    status_text.empty()
    
    if results:
        df_res = pd.DataFrame(results)
        
        # Explicit Column Order
        cols = [
            "Fund Name", "Latest NAV", 
            "1-Week", "2-Weeks", "3-Weeks", "1-Month", 
            "1-Year", "3-Year", "5-Year"
        ]
        
        # Filter existing columns
        final_cols = [c for c in cols if c in df_res.columns]
        
        st.dataframe(
            df_res[final_cols].style.format("{:.2f}", subset=[c for c in final_cols if c != "Fund Name"])
            .background_gradient(subset=["1-Week", "1-Month", "1-Year"], cmap="RdYlGn"),
            use_container_width=True,
            height=600,
            key=f"df_{category}_final" # Unique key per category prevents ghost columns
        )
    else:
        st.warning("No data found. The API might be rate-limiting or down.")

if __name__ == "__main__":
    main()
