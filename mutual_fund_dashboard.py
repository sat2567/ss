import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import time
from streamlit.components.v1 import html
from functools import lru_cache

# Import market data module
from market_data import display_market_data

def main():
    # Configure Streamlit page
    st.set_page_config(
        page_title="Market Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Add custom CSS for better styling
    st.markdown("""
    <style>
        .main {
            max-width: 1200px;
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
        }
        .positive {
            color: #28a745;
        }
        .negative {
            color: #dc3545;
        }
        .fund-selector {
            margin-bottom: 2rem;
        }
        .fund-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .fund-metric {
            font-size: 1.2rem;
            font-weight: 500;
        }
        .fund-metric-label {
            font-size: 0.9rem;
            color: #6c757d;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 Mutual Fund Analyzer")
    st.markdown("Select and analyze mutual funds across different categories")
    
    # Add a loading spinner while fetching data
    with st.spinner("Loading fund data..."):
        # Category mapping
        categories = {
            "Flexi Cap": "flexi-cap-fund",
            "Small Cap": "small-cap-fund",
            "Mid Cap": "mid-cap-fund",
        }
        
        # Fetch data for all categories first
        all_funds = []
        for category_label, category in categories.items():
            df = scrape_category(category, category_label)
            if df is not None and not df.empty:
                all_funds.append(df)
        
        if not all_funds:
            st.error("⚠️ Could not fetch any fund data. Please check your internet connection and try again.")
            return
        
        # Combine all funds into a single DataFrame
        combined_df = pd.concat(all_funds, ignore_index=True)
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### 🔍 Filter Funds")
        
        # Category filter
        selected_categories = st.multiselect(
            "Select Categories:",
            options=sorted(combined_df['Category'].unique()),
            default=sorted(combined_df['Category'].unique()),
            key="category_filter"
        )
        
        # Search box
        search_term = st.text_input("Search by fund name:", "", key="fund_search")
        
        # Sort by dropdown
        sort_by = st.selectbox(
            "Sort by:",
            options=["Scheme Name", "1M", "3M", "6M", "1Y", "3Y", "5Y"],
            index=0,
            key="sort_by"
        )
        
        # Sort order
        sort_ascending = st.checkbox("Ascending order", value=False, key="sort_order")
        
        # Filter and sort funds
        filtered_funds = combined_df[
            combined_df['Category'].isin(selected_categories)
        ]
        
        if search_term:
            filtered_funds = filtered_funds[
                filtered_funds['Scheme Name'].str.contains(search_term, case=False, na=False)
            ]
        
        # Sort the funds
        if sort_by in filtered_funds.columns:
            filtered_funds = filtered_funds.sort_values(
                by=sort_by, 
                ascending=sort_ascending,
                na_position='last'
            )
        
        # Fund selector
        selected_fund = st.selectbox(
            "Select a fund to analyze:",
            options=filtered_funds['Scheme Name'].tolist(),
            index=0 if not filtered_funds.empty else None,
            key="fund_selector"
        )
    
    with col2:
        if selected_fund and not filtered_funds.empty:
            fund_data = filtered_funds[filtered_funds['Scheme Name'] == selected_fund].iloc[0]
            
            # Display fund header
            st.markdown(f"# {fund_data['Scheme Name']}")
            st.markdown(f"**Category:** {fund_data['Category']} | **Plan:** {fund_data['Plan']}")
            
            # Create tabs for different sections
            tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Performance", "📋 Details"])
            
            with tab1:
                # Display key metrics in a grid
                st.markdown("### 📊 Key Metrics")
                
                # Define the metrics to show in the grid
                metric_cols = st.columns(4)
                
                # Row 1: Basic Info
                with metric_cols[0]:
                    if 'Nav' in fund_data and pd.notna(fund_data['Nav']):
                        st.metric("NAV", f"₹{fund_data['Nav']:,.2f}")
                with metric_cols[1]:
                    if 'Aum' in fund_data and pd.notna(fund_data['Aum']):
                        st.metric("AUM", f"₹{fund_data['Aum']:,.2f} Cr")
                with metric_cols[2]:
                    if 'Expense Ratio' in fund_data and pd.notna(fund_data['Expense Ratio']):
                        st.metric("Expense Ratio", f"{fund_data['Expense Ratio']}%")
                with metric_cols[3]:
                    if 'Exit Load' in fund_data and pd.notna(fund_data['Exit Load']):
                        st.metric("Exit Load", fund_data['Exit Load'])
                
                # Row 2: Risk and Rating
                metric_cols2 = st.columns(4)
                with metric_cols2[0]:
                    if 'Risk Level' in fund_data and pd.notna(fund_data['Risk Level']):
                        st.metric("Risk Level", fund_data['Risk Level'])
                with metric_cols2[1]:
                    if 'Crisil Rank' in fund_data and pd.notna(fund_data['Crisil Rank']):
                        st.metric("Crisil Rank", fund_data['Crisil Rank'])
                with metric_cols2[2]:
                    if 'Min Sip' in fund_data and pd.notna(fund_data['Min Sip']):
                        st.metric("Min SIP", f"₹{fund_data['Min Sip']}")
                with metric_cols2[3]:
                    if 'Launch Date' in fund_data and pd.notna(fund_data['Launch Date']):
                        st.metric("Launch Date", fund_data['Launch Date'])
                
                # Display all available data in a table
                st.markdown("### 📋 All Available Data")
                st.dataframe(
                    pd.DataFrame({
                        'Metric': fund_data.index,
                        'Value': fund_data.values
                    }).set_index('Metric'),
                    use_container_width=True
                )
            
            with tab1:  # Performance Tab
                st.markdown("### 📈 Returns Over Different Periods")
                
                # Get available return periods
                return_periods = [col for col in ['1W', '1M', '3M', '6M', '1Y', '3Y', '5Y'] 
                                if col in fund_data and pd.notna(fund_data[col])]
                
                if return_periods:
                    # Create columns for returns
                    cols = st.columns(len(return_periods) if len(return_periods) <= 4 else 4)
                    
                    for idx, period in enumerate(return_periods):
                        with cols[idx % 4]:
                            value = fund_data[period]
                            st.metric(
                                f"{period} Return",
                                f"{value:+.2f}%",
                                delta=None,
                                delta_color=("normal" if value >= 0 else "inverse")
                            )
                    
                    # Show performance chart if we have enough data points
                    if len(return_periods) >= 3:
                        st.markdown("### 📊 Performance Chart")
                        try:
                            chart_data = pd.DataFrame({
                                'Period': return_periods,
                                'Return': [fund_data[p] for p in return_periods]
                            })
                            st.bar_chart(
                                chart_data.set_index('Period'),
                                use_container_width=True
                            )
                        except:
                            pass
                else:
                    st.warning("No return data available for this fund.")
                
                # Show similar funds for comparison
                st.markdown("### 🔄 Compare with Similar Funds")
                similar_funds = filtered_funds[
                    (filtered_funds['Category'] == fund_data['Category']) &
                    (filtered_funds['Scheme Name'] != fund_data['Scheme Name'])
                ]
                
                if not similar_funds.empty:
                    # Get top 5 similar funds by AUM
                    if 'Aum' in similar_funds.columns:
                        similar_funds = similar_funds.sort_values('Aum', ascending=False).head(5)
                    
                    # Show comparison table
                    st.dataframe(
                        similar_funds[['Scheme Name', '1M', '3M', '6M', '1Y', '3Y', '5Y']].set_index('Scheme Name'),
                        use_container_width=True
                    )
                else:
                    st.info("No similar funds found in the same category.")
            
            with tab2:  # Details Tab
                st.markdown("### 📋 Fund Details")
                
                # Display all available information in an expandable section
                with st.expander("View Complete Fund Details", expanded=True):
                    # Convert fund data to a clean dictionary
                    fund_details = {
                        'Basic Information': {},
                        'Performance Metrics': {},
                        'Investment Details': {}
                    }
                    
                    # Categorize the data
                    basic_info_keys = ['Scheme Name', 'Plan', 'Category', 'Launch Date', 'Benchmark']
                    perf_keys = [col for col in fund_data.index if any(k in col for k in ['Return', 'Growth', 'Yield', 'Risk', 'Alpha', 'Beta', 'Sharpe', 'Sortino'])]
                    invest_keys = ['Min SIP', 'Min Lumpsum', 'SIP Available', 'Exit Load', 'Lock-in Period']
                    
                    for key, value in fund_data.items():
                        if key in basic_info_keys:
                            fund_details['Basic Information'][key] = value
                        elif key in perf_keys or any(k in key for k in ['1M', '3M', '6M', '1Y', '3Y', '5Y']):
                            fund_details['Performance Metrics'][key] = value
                        elif key in invest_keys or 'Min' in key or 'Max' in key or 'Expense' in key:
                            fund_details['Investment Details'][key] = value
                    
                    # Display each section
                    for section, data in fund_details.items():
                        if data:  # Only show if there's data
                            st.markdown(f"#### {section}")
                            st.json(data, expanded=False)
        else:
            st.info("👈 Select a fund from the filters to view details.")

# Cache the data to prevent re-fetching on every interaction
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_table(url, rename_map=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="mctable1")

        if not table:
            return None

        rows = table.find_all("tr")
        data = []
        for row in rows:
            cols = row.find_all(["td", "th"])
            cols = [ele.get_text(strip=True) for ele in cols]
            data.append(cols)

        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            if rename_map:
                df.rename(columns=rename_map, inplace=True)
            return df
        return None
    except Exception as e:
        st.error(f"Error fetching data from {url}: {str(e)}")
        return None

def scrape_category_ranks(category):
    """Scrape ranking data for Regular Growth funds in a specific category"""
    try:
        url = f"https://www.moneycontrol.com/mutual-funds/performance-tracker/ranks/{category}.html"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main table
        table = soup.find('table', {'class': 'mctable1'})
        if not table:
            st.warning(f"No ranking table found for {category}")
            return None
            
        # Extract headers
        headers = []
        for th in table.find('thead').find_all('th'):
            headers.append(th.get_text(strip=True))
        
        # Extract rows
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            row = [td.get_text(strip=True) for td in tr.find_all('td')]
            if len(row) == len(headers):
                rows.append(row)
        
        # Create DataFrame
        if not rows:
            return None
            
        df = pd.DataFrame(rows, columns=headers)
        
        # Filter for Regular Growth funds only
        if 'Plan' in df.columns and 'Scheme Name' in df.columns:
            df = df[df['Plan'] == 'Regular']
            df = df[df['Scheme Name'].str.contains('Growth', case=False, na=False)]
            
        # Clean and convert rank columns to numeric
        rank_columns = [col for col in df.columns if 'rank' in col.lower() or 'Rank' in col]
        for col in rank_columns:
            df[col] = pd.to_numeric(df[col].str.extract(r'(\d+)', expand=False), errors='coerce')
        
        # Define return periods we want to display and sort by
        return_periods = ['1W', '1M', '3M', '6M', '1Y', '3Y', '5Y']
        
        # Clean and convert return columns to numeric
        for period in return_periods:
            # Try different column name formats
            for col in [f"{period}", f"{period} Return", f"{period} Returns"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].str.rstrip('%'), errors='coerce')
        
        # Sort by 1M return by default (highest to lowest)
        sort_column = next((col for col in ['1M', '1M Return'] if col in df.columns), None)
        if sort_column:
            df = df.sort_values(sort_column, ascending=False).head(10)
        
        # Select only the columns we want to display
        display_columns = ['Scheme Name'] + rank_columns
        return df[display_columns].dropna(how='all', axis=1)
        
    except Exception as e:
        st.error(f"Error fetching ranking data: {str(e)}")
        return None

def scrape_category(category, category_label):
    base = "https://www.moneycontrol.com/mutual-funds/performance-tracker"
    urls = {
        "returns": f"{base}/returns/{category}.html",
        "rank": f"{base}/ranks/{category}.html"
    }

    # Fetch only essential data
    with ThreadPoolExecutor() as executor:
        futures = {
            "returns": executor.submit(fetch_table, urls["returns"]),
            "rank": executor.submit(fetch_table, urls["rank"], {"Crisil Rank": "Crisil Rating"})
        }
        
        # Get results
        df_returns = futures["returns"].result()
        df_rank = futures["rank"].result()

    if df_returns is None:
        return pd.DataFrame()  # Return empty DataFrame instead of None

    # Function to drop common columns
    def drop_common(df, common_cols):
        if df is not None:
            return df.drop(columns=[c for c in common_cols if c in df.columns], 
                         errors="ignore")
        return None

    # Process rank dataframe
    rank_df = drop_common(df_rank, ["Category Name", "Crisil Rating"]) if df_rank is not None else None

    # Start with returns dataframe
    combined = df_returns
    
    # Merge with rank data if available
    if rank_df is not None and not rank_df.empty and 'Scheme Name' in rank_df.columns and 'Plan' in rank_df.columns:
        combined = combined.merge(rank_df, on=["Scheme Name", "Plan"], how="left")

    # Filter only Regular + Growth plans
    if 'Plan' in combined.columns and 'Scheme Name' in combined.columns:
        combined = combined[combined["Plan"] == "Regular"]
        combined = combined[combined["Scheme Name"].str.contains("Growth", case=False, na=False)]
    else:
        return None

    # Clean and convert all numeric columns
    for col in combined.columns:
        # Handle percentage columns
        if any(period in col for period in ['1W', '1M', '3M', '6M', '1Y', '3Y', '5Y', 'Return', 'Change']):
            combined[col] = pd.to_numeric(
                combined[col].astype(str).str.rstrip('%'), 
                errors='coerce'
            )
        # Handle numeric columns with commas
        elif combined[col].dtype == 'object':
            # Check if the column contains numeric values with commas
            if combined[col].str.contains(',').any():
                combined[col] = pd.to_numeric(
                    combined[col].str.replace(',', ''),
                    errors='ignore'
                )

    # Add category info and clean up
    if not combined.empty:
        combined["Category"] = category_label
        
        # Ensure we have all important columns
        important_columns = [
            'Scheme Name', 'Plan', 'Category', 'NAV', 'AUM', 'Expense Ratio',
            '1W', '1M', '3M', '6M', '1Y', '3Y', '5Y', 'Crisil Rank',
            'Risk Level', 'Exit Load', 'Min SIP', 'Min Lumpsum', 'Launch Date'
        ]
        
        # Keep all available columns, but ensure important ones are included
        available_columns = [col for col in important_columns if col in combined.columns]
        other_columns = [col for col in combined.columns if col not in important_columns]
        combined = combined[available_columns + other_columns]
        
        # Clean up column names for better display
        combined.columns = [col.replace('_', ' ').title() for col in combined.columns]
        
        # Drop any rows with missing scheme names
        combined = combined.dropna(subset=['Scheme Name'])
        
        return combined
    
    return pd.DataFrame()  # Return empty DataFrame if no data

def main():
    st.title("📊 Mutual Fund Dashboard")
    st.write("Fetching live mutual fund data from Moneycontrol...")

    # Category mapping
    categories = {
        "Flexi Cap": "flexi-cap-fund",
        "Small Cap": "small-cap-fund",
        "Mid Cap": "mid-cap-fund",
        "Large Cap": "large-cap-fund",
        "ELSS": "elss",
        "Sectoral": "sectoral-fund",
        "Index": "index-fund"
    }

    # Sidebar for filters
    st.sidebar.header("🔍 Filters")
    
    # Category selection
    selected_category = st.sidebar.selectbox(
        "Select Fund Category:",
        list(categories.keys())
    )

    # Scrape data with loading indicator
    with st.spinner(f"Fetching {selected_category} funds data..."):
        df = scrape_category(categories[selected_category], selected_category)

    if df is not None and not df.empty:
        st.success(f"✅ Showing {selected_category} Funds ({len(df)} schemes)")

        # Additional filters
        st.sidebar.subheader("Refine Results")
        
        # AUM Filter
        if "AuM (Cr)" in df.columns:
            min_aum, max_aum = df["AuM (Cr)"].min(), df["AuM (Cr)"].max()
            aum_range = st.sidebar.slider(
                "AUM (in Cr)", 
                min_value=float(min_aum), 
                max_value=float(max_aum), 
                value=(float(min_aum), float(max_aum))
            )
            df = df[(df["AuM (Cr)"] >= aum_range[0]) & (df["AuM (Cr)"] <= aum_range[1])]

        # CRISIL Rating Filter
        if "Crisil Rating" in df.columns:
            crisil_ratings = df["Crisil Rating"].dropna().unique()
            selected_ratings = st.sidebar.multiselect(
                "CRISIL Rating",
                options=sorted(crisil_ratings),
                default=sorted(crisil_ratings)
            )
            df = df[df["Crisil Rating"].isin(selected_ratings)]

        # Display the dataframe
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            hide_index=True,
            column_config={
                "Scheme Name": st.column_config.TextColumn("Scheme Name", width="large"),
                "1W": st.column_config.NumberColumn("1W Return (%)", format="%.2f%%"),
                "AuM (Cr)": st.column_config.NumberColumn("AUM (Cr)", format="₹%.2f")
            }
        )

        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"{selected_category.lower().replace(' ', '_')}_funds.csv",
            mime="text/csv"
        )

        # Show top 10 ranked Regular Growth funds
        st.subheader(f"🏆 Top 10 {selected_category} Regular Growth Funds by Rank")
        rank_df = scrape_category_ranks(categories[selected_category])
        
        if rank_df is not None and not rank_df.empty:
            # Clean up column names for better display
            column_mapping = {
                '1W': '1 Week',
                '1M': '1 Month',
                '3M': '3 Months',
                '6M': '6 Months',
                '1Y': '1 Year',
                'YTD': 'YTD'
            }
            
            # Rename columns for better display
            rank_df = rank_df.rename(columns={col: column_mapping.get(col, col) for col in rank_df.columns})
            
            # Get rank columns (all columns except Scheme Name)
            rank_columns = [col for col in rank_df.columns if col != 'Scheme Name']
            
            if rank_columns:  # Only proceed if we have rank columns
                # Create styled dataframe with conditional formatting
                st.dataframe(
                    rank_df.style
                    .format("{:.0f}", subset=rank_columns)  # Format as integers
                    .highlight_min(rank_columns, color='#e6f7e6')  # Light green for best ranks
                    .highlight_max(rank_columns, color='#ffcccc')  # Light red for worst ranks
                    .set_properties(**{'text-align': 'center'})
                    .set_table_styles([
                        {'selector': 'th', 'props': [('text-align', 'center')]},
                        {'selector': 'td', 'props': [('text-align', 'center')]}
                    ]),
                    use_container_width=True,
                    height=(min(len(rank_df), 10) + 1) * 35 + 3,
                    hide_index=True
                )
                
                # Add caption explaining the ranking
                st.caption("🟢 Best rank | 🔴 Worst rank | Lower numbers indicate better performance")
            else:
                st.warning("No rank columns found in the data.")
                st.write(rank_df)  # Show raw data for debugging
        else:
            st.warning("No ranking data available for this category. The fund category might not exist or the data format has changed.")
            
        # Removed fund returns section as requested
    else:
        st.error("⚠️ Could not fetch data. Please try again later.")

if __name__ == "__main__":
    main()
