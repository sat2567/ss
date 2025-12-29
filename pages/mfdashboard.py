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
        "forbidden": [
            "mid", "small", "flexi", "multi", "focused", "opportunities", 
            "active", "advantage", "balanced", "hybrid", "tax", "elss", 
            "index", "etf", "nifty", "sensex", "passive", "overseas", "global", "quant"
        ]
    },
    "MID CAP": {
        "required": ["mid cap", "midcap", "emerging", "growth", "prima"],
        "forbidden": [
            "large", "small", "bluechip", "frontline", "flexi", "multi", 
            "focused", "opportunities", "index", "etf", "hybrid", "balanced"
        ]
    },
    "SMALL CAP": {
        "required": ["small cap", "smallcap", "emerging", "discovery"],
        "forbidden": [
            "large", "mid", "bluechip", "frontline", "flexi", "multi", 
            "focused", "index", "etf", "hybrid"
        ]
    },
    "LARGE & MID CAP": {
        "required": ["large & mid", "large and mid", "large & midcap", "large and midcap"],
        "forbidden": [
            "small", "flexi", "multi", "bluechip", "focused", "index", "etf"
        ]
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
    @st.cache_data(ttl=86400, show_spinner=False)
    def get_all_schemes() -> List[Dict]:
        try:
            response = requests.get(f"{BASE_URL}/mf", timeout=30)
            response.raise_for_status()
            return response.json()
        except: return []

    @staticmethod
    @st.cache_data(ttl=86400)
    def get_scheme_data_clean(scheme_code: str) -> pd.DataFrame:
        try:
            response = requests.get(f"{BASE_URL}/mf/{scheme_code}", timeout=10)
            data = response.json()
            if not data or 'data' not in data: return pd.DataFrame()
            
            df = pd.DataFrame(data['data'])
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
            df = df[df['nav'] > 0].dropna().sort_values('date').set_index('date')
            
            pct = df['nav'].pct_change()
            mask = (pct.abs() < 0.20)
            mask.iloc[0] = True
            df = df[mask]
            
            return df
        except: return pd.DataFrame()

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> Dict:
        if len(df) < 30: return {}
        
        latest_nav = df['nav'].iloc[-1]
        last_date = df.index[-1]
        
        metrics = {'Latest NAV': latest_nav}
        
        # ADDED SHORT TERM PERIODS HERE
        periods = {
            '1W': 7, 
            '2W': 14, 
            '3W': 21, 
            '1M': 30,
            '1Y': 365, 
            '3Y': 365*3, 
            '5Y': 365*5
        }
        
        for lbl, days in periods.items():
            target_date = last_date - timedelta(days=days)
            # Find nearest available date within a tolerance
            idx = df.index.get_indexer([target_date], method='nearest')[0]
            
            # Tolerance for missing data: 5 days for short term, 20 days for long term
            tolerance = 5 if days < 60 else 20
            
            if idx != -1 and abs((df.index[idx] - target_date).days) < tolerance:
                start_nav = df['nav'].iloc[idx]
                
                if days < 365:
                    # ABSOLUTE RETURN for < 1 Year
                    ret = ((latest_nav - start_nav) / start_nav) * 100
                else:
                    # CAGR for >= 1 Year
                    years = days/365
                    ret = ((latest_nav/start_nav)**(1/years) - 1)*100
                    
                metrics[lbl] = ret
            else:
                metrics[lbl] = np.nan
        return metrics

def main():
    st.set_page_config(layout="wide", page_title="Smart Fund Analyzer")
    st.sidebar.title("Fund Analyzer")
    
    category = st.sidebar.selectbox("Select Category", list(USER_FUNDS_CONFIG.keys()))
    
    st.title(f"Detailed Analysis: {category}")
    st.info("Showing Absolute Returns for <1Y and CAGR for >1Y.")

    with st.spinner("Fetching Master Data..."):
        all_schemes = MutualFundAnalyzer.get_all_schemes()

    if not all_schemes:
        st.error("API Down.")
        return

    target_funds = USER_FUNDS_CONFIG[category]
    results = []
    
    progress = st.progress(0)
    status_text = st.empty()
    
    for i, user_fund in enumerate(target_funds):
        progress.progress((i+1)/len(target_funds))
        status_text.text(f"Processing: {user_fund}")
        
        match = FundNameMatcher.get_best_match(user_fund, all_schemes, category)
        
        if match:
            df = MutualFundAnalyzer.get_scheme_data_clean(match['schemeCode'])
            if not df.empty:
                mets = MutualFundAnalyzer.calculate_metrics(df)
                row = {
                    "User Name": user_fund,
                    "Matched API Name": match['schemeName'],
                    "Latest NAV": mets.get('Latest NAV'),
                    "1W (%)": mets.get('1W'),
                    "2W (%)": mets.get('2W'),
                    "3W (%)": mets.get('3W'),
                    "1M (%)": mets.get('1M'),
                    "1Y (%)": mets.get('1Y'),
                    "3Y (%)": mets.get('3Y'),
                    "5Y (%)": mets.get('5Y')
                }
                results.append(row)
        
        time.sleep(0.01)

    status_text.empty()
    
    if results:
        df_res = pd.DataFrame(results)
        
        # Setup columns for formatting
        cols_to_format = ["Latest NAV", "1W (%)", "2W (%)", "3W (%)", "1M (%)", "1Y (%)", "3Y (%)", "5Y (%)"]
        
        st.dataframe(
            df_res.style.format("{:.2f}", subset=cols_to_format)
            .background_gradient(subset=["1W (%)", "1M (%)", "1Y (%)"], cmap="RdYlGn"),
            use_container_width=True,
            height=600
        )
    else:
        st.warning("No valid data found.")

if __name__ == "__main__":
    main()
