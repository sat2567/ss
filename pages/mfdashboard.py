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
# 1. REQUIRED: The matched name MUST contain at least one of these.
# 2. FORBIDDEN: The matched name MUST NOT contain any of these.
CATEGORY_RULES = {
    "LARGE CAP": {
        "required": ["large cap", "largecap", "bluechip", "frontline", "top 100"],
        "forbidden": [
            "mid", "small", "flexi", "multi", "focused", "opportunities", 
            "active", "advantage", "balanced", "hybrid", "tax", "elss", 
            "index", "etf", "nifty", "sensex", "passive", "overseas", "global", "quant"
            # Note: 'quant' matches the AMC, so be careful. Handled in code by checking if it's the AMC name or category.
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
        """Standardizes name for comparison."""
        name = name.lower()
        # Remove standard noise
        name = re.sub(r'[-\s]*regular\s*plan', '', name)
        name = re.sub(r'[-\s]*direct\s*plan', '', name)
        name = re.sub(r'[-\s]*growth\s*option', '', name)
        name = re.sub(r'\((g|idcw|d)\)', '', name)
        
        # Standardize AMC names
        name = name.replace("aditya birla sl", "aditya birla sun life")
        name = name.replace("canara rob", "canara robeco")
        name = name.replace("woc", "whiteoak")
        return name.strip()

    @staticmethod
    def check_category_constraints(api_name_clean: str, category: str, amc_name: str) -> bool:
        """
        Returns False if the fund violates strict category rules.
        """
        rules = CATEGORY_RULES.get(category, {})
        required = rules.get("required", [])
        forbidden = rules.get("forbidden", [])
        
        # 1. MUST HAVE Requirement (The "Positive" Filter)
        # The fund name matches MUST contain at least one required token
        has_required = any(req in api_name_clean for req in required)
        if not has_required:
            return False

        # 2. MUST NOT HAVE Requirement (The "Negative" Filter)
        for bad_word in forbidden:
            # Special case: 'quant' is an AMC name but also a strategy. 
            # If the user is looking for "Quant Large Cap", we shouldn't ban "Quant" the word.
            if bad_word == "quant" and "quant" in amc_name:
                continue
                
            # Use word boundary check to avoid partial matches if needed, 
            # but simple containment is safer for things like "midcap" vs "mid"
            if bad_word in api_name_clean:
                return False 
                
        return True

    @staticmethod
    def get_best_match(user_fund_name: str, all_schemes: List[Dict], category: str) -> Optional[Dict]:
        """Finds best match using strict category enforcement."""
        
        clean_user = FundNameMatcher.clean_name(user_fund_name)
        # Extract implied AMC name for safety check (first 2 words usually)
        user_tokens = clean_user.split()
        amc_token = user_tokens[0] if user_tokens else ""

        best_match = None
        best_score = 0.0

        for scheme in all_schemes:
            api_name_raw = scheme["schemeName"]
            
            # Fast Filters (Basic)
            if "Direct" in api_name_raw: continue
            if "IDCW" in api_name_raw or "Dividend" in api_name_raw: continue
            
            clean_api = FundNameMatcher.clean_name(api_name_raw)

            # 1. AMC MATCH CHECK (Critical)
            # If user asks for "SBI", the result MUST have "SBI"
            if amc_token not in clean_api:
                continue

            # 2. STRICT CATEGORY FILTER
            # Pass the AMC name to allow exceptions (like 'Quant' AMC)
            if not FundNameMatcher.check_category_constraints(clean_api, category, amc_token):
                continue

            # 3. Fuzzy Scoring
            # We score the match. Since we have already filtered strictly, 
            # we can trust high scores more.
            score = difflib.SequenceMatcher(None, clean_user, clean_api).ratio()
            
            if score > best_score:
                best_score = score
                best_match = scheme

        # Threshold
        if best_score > 0.50:
            # Final sanity check: Print if the match seems weird during debug
            # print(f"Matched: {clean_user} -> {best_match['schemeName']} ({best_score})")
            return best_match
            
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
            
            # Remove Spikes (>20% daily change)
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
        
        periods = {
            '1Y': 365, '3Y': 365*3, '5Y': 365*5
        }
        
        for lbl, days in periods.items():
            target_date = last_date - timedelta(days=days)
            idx = df.index.get_indexer([target_date], method='nearest')[0]
            if idx != -1 and abs((df.index[idx] - target_date).days) < 20:
                start_nav = df['nav'].iloc[idx]
                years = days/365
                cagr = ((latest_nav/start_nav)**(1/years) - 1)*100
                metrics[lbl] = cagr
            else:
                metrics[lbl] = np.nan
        return metrics

def main():
    st.set_page_config(layout="wide", page_title="Smart Fund Analyzer")
    st.sidebar.title("Fund Analyzer")
    
    category = st.sidebar.selectbox("Select Category", list(USER_FUNDS_CONFIG.keys()))
    
    st.title(f"Strict Analysis: {category}")
    st.info("Strict Mode Active: Funds must contain exact category keywords (e.g. 'Bluechip', 'Large Cap') and exclude 'Focused'/'Flexi'.")

    with st.spinner("Fetching Master Data..."):
        all_schemes = MutualFundAnalyzer.get_all_schemes()

    if not all_schemes:
        st.error("API Down.")
        return

    # Process
    target_funds = USER_FUNDS_CONFIG[category]
    results = []
    
    progress = st.progress(0)
    status_text = st.empty()
    
    for i, user_fund in enumerate(target_funds):
        progress.progress((i+1)/len(target_funds))
        status_text.text(f"Processing: {user_fund}")
        
        # INTELLIGENT MATCHING
        match = FundNameMatcher.get_best_match(user_fund, all_schemes, category)
        
        if match:
            df = MutualFundAnalyzer.get_scheme_data_clean(match['schemeCode'])
            if not df.empty:
                mets = MutualFundAnalyzer.calculate_metrics(df)
                row = {
                    "User Name": user_fund,
                    "Matched API Name": match['schemeName'],
                    "Latest NAV": mets.get('Latest NAV'),
                    "1Y (%)": mets.get('1Y'),
                    "3Y (%)": mets.get('3Y'),
                    "5Y (%)": mets.get('5Y')
                }
                results.append(row)
        
        time.sleep(0.01)

    status_text.empty()
    
    if results:
        df_res = pd.DataFrame(results)
        st.dataframe(
            df_res.style.format("{:.2f}", subset=["Latest NAV", "1Y (%)", "3Y (%)", "5Y (%)"])
            .background_gradient(subset=["1Y (%)", "3Y (%)"], cmap="RdYlGn"),
            use_container_width=True,
            height=600
        )
    else:
        st.warning("No valid data found. Try verifying fund names.")

if __name__ == "__main__":
    main()
