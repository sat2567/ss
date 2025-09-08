import streamlit as st
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

st.set_page_config(layout="wide", page_title="Mutual Fund Rank Tracker")

def fetch_table(url, rename_map=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'mctable1'})
        
        if table:
            # Extract headers
            headers = [th.text.strip() for th in table.find_all('th')]
            
            # Extract rows
            rows = []
            for tr in table.find_all('tr')[1:]:  # Skip header row
                row = [td.text.strip() for td in tr.find_all('td')]
                if row:  # Only add non-empty rows
                    rows.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            # Rename columns if needed
            if rename_map:
                df.rename(columns=rename_map, inplace=True)
                
            # Remove columns with all null values
            df = df.dropna(axis=1, how='all')
            
            return df
        return None
    except Exception as e:
        st.error(f"Error fetching data from {url}: {str(e)}")
        return None

def scrape_mf_ranks():
    base_url = "https://www.moneycontrol.com/mutual-funds/performance-tracker/ranks/flexi-cap-fund.html"
    
    # Fetch the rank table
    df = fetch_table(base_url)
    
    if df is None:
        return None
    
    # Clean up the column names
    df.columns = [col.strip() for col in df.columns]
    
    # Filter only Regular + Growth plans
    if 'Plan' in df.columns and 'Scheme Name' in df.columns:
        df = df[df["Plan"] == "Regular"]
        df = df[df["Scheme Name"].str.contains("Growth", case=False, na=False)]
    
    # Clean up numeric columns
    for col in df.columns:
        if col not in ['Scheme Name', 'Plan']:
            # Remove percentage signs and convert to numeric
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')
    
    return df

def main():
    st.title("📊 Mutual Fund Rank Tracker")
    st.write("Fetching live mutual fund rank data from Moneycontrol...")
    
    # Fetch data
    df = scrape_mf_ranks()
    
    if df is not None and not df.empty:
        # Display the data
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            hide_index=True,
            column_config={
                "Scheme Name": st.column_config.TextColumn("Scheme Name", width="large"),
                **{col: st.column_config.NumberColumn(col, format="%.2f%%") 
                   for col in df.columns if col not in ['Scheme Name', 'Plan']}
            }
        )
        
        # Show top 5 funds by rank
        if len(df.columns) > 2:  # If we have rank columns
            rank_col = df.columns[2]  # Assuming rank is the 3rd column
            st.subheader(f"🏆 Top 5 Funds by {rank_col}")
            top_funds = df.nsmallest(5, rank_col)[['Scheme Name', rank_col]]
            st.dataframe(
                top_funds,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Scheme Name": "Fund Name",
                    rank_col: st.column_config.NumberColumn(rank_col, format="%.1f%%")
                }
            )
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="mf_ranks.csv",
            mime="text/csv"
        )
    else:
        st.error("Failed to fetch data. Please try again later.")

if __name__ == "__main__":
    main()
