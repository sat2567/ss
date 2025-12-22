import streamlit as st
import requests
import pandas as pd
from datetime import timedelta
import time
from typing import Dict, List
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
# "Forbidden": If these words appear in the API result, REJECT IT.
# "Synonyms": If the user says "Large Cap", also accept "Bluechip" or "Frontline"
CATEGORY_RULES = {
    "LARGE CAP": {
        "forbidden": ["Mid", "Small", "Flexi", "Multi", "Silver", "Gold", "ETF", "Index", "Nifty", "Sensex", "Passive", "Overseas", "Global"],
        "synonyms": ["Bluechip", "Frontline", "Top 100", "Focused", "Leaders", "Equity"]
    },
    "MID CAP": {
        "forbidden": ["Large", "Small", "Bluechip", "Frontline", "Flexi", "Multi", "Silver", "Gold", "ETF", "Index"],
        "synonyms": ["Emerging", "Growth", "Prima"]
    },
    "SMALL CAP": {
        "forbidden": ["Large", "Mid", "Bluechip", "Frontline", "Flexi", "Multi", "Silver", "Gold", "ETF"],
        "synonyms": ["Emerging", "Discovery"]
    },
    "LARGE & MID CAP": {
        "forbidden": ["Small", "Flexi", "Multi", "Silver", "Gold", "ETF", "Bluechip"], 
        "synonyms": ["Equity"] 
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
        name = name.replace("aditya birla sl", "aditya birla sun life")
        name = name.replace("canara rob", "canara robeco")
        name = name.replace("woc", "whiteoak")
        return name.strip()

    @staticmethod
    def check_category_constraints(api_name_clean: str, category: str) -> bool:
        """Returns False if the fund violates strict category rules."""
        rules = CATEGORY_RULES.get(category, {})
        forbidden = rules.get("forbidden", [])
        
        # Check forbidden words
        for bad_word in forbidden:
            # We look for bad words as distinct tokens (e.g. avoid banning "Middle" if looking for "Mid")
            # But simple containment is usually safer for these specific keywords
            if bad_word.lower() in api_name_clean:
                return False # VIOLATION
        return True

    @staticmethod
    def get_best_match(user_fund_name: str, all_schemes: List[Dict], category: str) -> Dict:
        """Finds best match while respecting category constraints."""
        
        clean_user = FundNameMatcher.clean_name(user_fund_name)
        
        # 1. Expand User Query with Synonyms
        # If user says "SBI Large Cap", we also want to look for "SBI Bluechip"
        search_candidates = [clean_user]
        rules = CATEGORY_RULES.get(category, {})
        
        # Try swapping "Large Cap" with "Bluechip" etc.
        base_amc = clean_user.replace("large cap", "").replace("mid cap", "").replace("small cap", "").replace("fund", "").strip()
        
        if category == "LARGE CAP":
            for syn in rules.get("synonyms", []):
                search_candidates.append(f"{base_amc} {syn.lower()}")

        best_match = None
        best_score = 0.0

        for scheme in all_schemes:
            api_name_raw = scheme["schemeName"]
            
            # Fast Filters
            if "Direct" in api_name_raw: continue
            if "IDCW" in api_name_raw or "Dividend" in api_name_raw: continue
            
            clean_api = FundNameMatcher.clean_name(api_name_raw)

            # 2. STRICT CATEGORY FILTER
            if not FundNameMatcher.check_category_constraints(clean_api, category):
                continue

            # 3. AMC Match Check (Critical)
            # The first word of user query (AMC name) MUST exist in API name
            user_tokens = clean_user.split()
            if user_tokens and user_tokens[0] not in clean_api:
                continue

            # 4. Fuzzy Scoring
            # We score against ALL candidates (Original name + Synonym names)
            current_max_score = 0
            for candidate in search_candidates:
                score = difflib.SequenceMatcher(None, candidate, clean_api).ratio()
                if score > current_max_score:
                    current_max_score = score
            
            if current_max_score > best_score:
                best_score = current_max_score
                best_match = scheme

        # Threshold
        if best_score > 0.50:
            best_match['matchScore'] = best_score
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
    st.info("Now using 'Negative Filtering' to strictly ban Funds from other categories (e.g., banning 'Mid' when searching for 'Large').")

    with st.spinner("Fetching Master Data..."):
        all_schemes = MutualFundAnalyzer.get_all_schemes()

    if not all_schemes:
        st.error("API Down.")
        return

    # Process
    target_funds = USER_FUNDS_CONFIG[category]
    results = []
    
    progress = st.progress(0)
    
    for i, user_fund in enumerate(target_funds):
        progress.progress((i+1)/len(target_funds))
        
        # INTELLIGENT MATCHING
        match = FundNameMatcher.get_best_match(user_fund, all_schemes, category)
        
        if match:
            df = MutualFundAnalyzer.get_scheme_data_clean(match['schemeCode'])
            if not df.empty:
                mets = MutualFundAnalyzer.calculate_metrics(df)
                row = {
                    "User Name": user_fund,
                    "Matched API Name": match['schemeName'], # Verify this!
                    "Latest NAV": mets.get('Latest NAV'),
                    "1Y (%)": mets.get('1Y'),
                    "3Y (%)": mets.get('3Y'),
                    "5Y (%)": mets.get('5Y')
                }
                results.append(row)
        
        time.sleep(0.01)

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
