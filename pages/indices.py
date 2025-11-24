import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime
import numpy as np

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Advanced Market Dashboard")

# --- Constants & Ticker Mapping ---
# Yahoo Finance Tickers for Indian Indices (using standard proxies)
TICKERS = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP 100": "^NSMIDCP", # Standard proxy for Midcap
    "NIFTY SMALLCAP 100": "SMALLCAP.NS", # Standard proxy for Smallcap
    "SENSEX": "^BSESN"
}

# --- Helper Functions ---

@st.cache_data(ttl=3600) # Cache data for 1 hour
def fetch_data(period="2y"):
    """
    Fetches OHLC data for all tickers from Yahoo Finance.
    Returns a dictionary of DataFrames.
    """
    data_dict = {}
    ticker_list = list(TICKERS.values())
    
    # Bulk download is faster
    raw_data = yf.download(ticker_list, period=period, group_by='ticker', auto_adjust=True)
    
    for name, ticker in TICKERS.items():
        try:
            # Extract specific ticker data
            # Handle single-ticker download result structure
            if len(ticker_list) == 1:
                df = raw_data.copy()
            else:
                df = raw_data[ticker].copy()
                
            if not df.empty:
                # Drop rows with NaN (holidays/weekends)
                df.dropna(inplace=True)
                # Ensure the index is a plain datetime index (no timezone issues)
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                data_dict[name] = df
        except KeyError:
            # Handle cases where a specific ticker might fail in a multi-ticker download
            continue
            
    return data_dict

def calculate_rsi(series, period=14):
    """Calculates RSI."""
    delta = series.diff()
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    # Relative Strength (RS)
    rs = gain / loss
    # Relative Strength Index (RSI)
    return 100 - (100 / (1 + rs))

def calculate_drawdown(series):
    """Calculates percentage drawdown from peak."""
    rolling_max = series.cummax()
    drawdown = (series / rolling_max) - 1
    return drawdown * 100

# --- Main App Logic ---

def main():
    # 1. Sidebar Controls
    with st.sidebar:
        st.header("Settings")
        refresh = st.button("🔄 Refresh Data", help="Clears cache and fetches new data.")
        
        # Date Range Logic
        period_options = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
        selected_period = st.selectbox("Data Lookback Period", period_options, index=4)
        
        st.subheader("Chart Settings")
        normalize = st.checkbox("Normalize Prices (Start=100)", value=True)
        ma_windows = st.multiselect("Moving Averages (Days)", [20, 50, 100, 200], default=[50, 200])

    # 2. Load Data
    if refresh:
        st.cache_data.clear()
    
    with st.spinner(f"Fetching {selected_period} of market data..."):
        market_data = fetch_data(period=selected_period)

    if not market_data:
        st.error("Failed to fetch data for any ticker. Please check API connectivity or refresh the page.")
        return

    st.title("📈 Indian Market Dashboard: Live Analysis")

    # 3. Dynamic KPI Cards (The corrected section)
    st.subheader("Market Snapshot")
    cols = st.columns(len(market_data))
    
    for i, (name, df) in enumerate(market_data.items()):
        # Defensive check: ensure enough data exists
        if len(df) < 1:
            current_price = 0
            delta_str = "No Data"
        else:
            current_price = df['Close'].iloc[-1]
            
            if len(df) >= 2:
                # This is the line that caused the error, now safely inside an IF block
                prev_price = df['Close'].iloc[-2]
                daily_change = current_price - prev_price
                daily_pct = (daily_change / prev_price) * 100
                delta_str = f"{daily_pct:.2f}%"
            else:
                # Only 1 day of data available (cannot calculate change)
                delta_str = "N/A"

        cols[i].metric(
            label=name,
            value=f"{current_price:,.0f}",
            delta=delta_str
        )

    # 4. Tabs for Analysis
    tab_compare, tab_risk, tab_deep_dive = st.tabs(["📊 Index Comparison", "📉 Risk & Volatility", "🕯️ Technical Deep Dive"])
    
    # Get the list of indices that successfully loaded data
    available_indices = list(market_data.keys())

    # --- TAB 1: COMPARISON & CORRELATION ---
    with tab_compare:
        
        # Multiselect for comparison chart (put here so it doesn't affect the KPI cards)
        indices_to_plot = st.multiselect("Select Indices for Comparison", available_indices, default=available_indices)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Price Performance Comparison")
            
            fig_compare = go.Figure()
            
            for name in indices_to_plot:
                df = market_data[name].copy()
                y_data = df['Close']
                
                if normalize:
                    start_val = y_data.iloc[0]
                    y_data = (y_data / start_val) * 100
                    title_y = "Normalized Price (Start=100)"
                else:
                    title_y = "Price"
                    
                # Add main close line
                fig_compare.add_trace(go.Scatter(x=df.index, y=y_data, mode='lines', name=name))
                
                # Add moving averages
                for window in ma_windows:
                    ma_label = f'{name} MA{window}'
                    df[ma_label] = y_data.rolling(window=window).mean()
                    fig_compare.add_trace(go.Scatter(
                        x=df.index, y=df[ma_label], 
                        mode='lines', name=f'{name} {window} DMA',
                        line=dict(dash='dash', width=1)
                    ))
            
            fig_compare.update_layout(yaxis_title=title_y, height=500, hovermode="x unified")
            st.plotly_chart(fig_compare, use_container_width=True)

        with col2:
            st.subheader("Correlation Matrix")
            st.caption("Based on daily returns over selected period")
            
            # Prepare Correlation Data
            close_prices = pd.DataFrame({name: data['Close'] for name, data in market_data.items()})
            corr_matrix = close_prices.pct_change().corr()
            
            fig_corr = px.imshow(
                corr_matrix, 
                text_auto=".2f", 
                color_continuous_scale='RdBu_r', 
                zmin=-1, zmax=1,
                aspect="auto"
            )
            st.plotly_chart(fig_corr, use_container_width=True)

    # --- TAB 2: RISK & VOLATILITY ---
    with tab_risk:
        st.subheader("Underwater Plot (Drawdowns)")
        
        fig_dd = go.Figure()
        
        for name in indices_to_plot:
            df = market_data[name]
            dd = calculate_drawdown(df['Close'])
            fig_dd.add_trace(go.Scatter(x=dd.index, y=dd, name=name, fill='tozeroy'))
            
        fig_dd.update_layout(yaxis_title="Drawdown (%)", height=400, hovermode="x unified")
        st.plotly_chart(fig_dd, use_container_width=True)
        
        # Volatility Table
        st.subheader("Volatility Metrics (Annualized)")
        vol_data = []
        for name in indices_to_plot:
            df = market_data[name]
            
            if len(df) < 252: # Need approx 1 year of data for valid annual calculation
                vol_data.append({"Index": name, "Annualized Volatility": "N/A", "Max Drawdown (Period)": "N/A"})
                continue

            returns = df['Close'].pct_change().dropna()
            ann_vol = returns.std() * np.sqrt(252) * 100
            max_dd = calculate_drawdown(df['Close']).min()
            
            vol_data.append({
                "Index": name, 
                "Annualized Volatility": f"{ann_vol:.2f}%",
                "Max Drawdown (Period)": f"{max_dd:.2f}%"
            })
            
        st.dataframe(pd.DataFrame(vol_data), use_container_width=True)

    # --- TAB 3: TECHNICAL DEEP DIVE ---
    with tab_deep_dive:
        st.subheader("Technical Deep Dive")
        
        col_dd_1, col_dd_2 = st.columns([1, 3])
        
        with col_dd_1:
            selected_asset = st.selectbox("Select Asset to Analyze", available_indices, key="deep_dive_asset")
            df_asset = market_data[selected_asset].copy()
            
            # Calculate Indicators
            if len(df_asset) > 14:
                df_asset['RSI'] = calculate_rsi(df_asset['Close'])
                for ma in ma_windows:
                    df_asset[f'MA_{ma}'] = df_asset['Close'].rolling(window=ma).mean()
            
            # Display current RSI value
            latest_rsi = df_asset['RSI'].iloc[-1] if 'RSI' in df_asset.columns else np.nan
            st.metric("Latest RSI (14-Day)", f"{latest_rsi:.2f}" if not np.isnan(latest_rsi) else "N/A")
            
            st.dataframe(df_asset.tail(10).sort_index(ascending=False), use_container_width=True, height=300)

        with col_dd_2:
            if 'RSI' in df_asset.columns:
                from plotly.subplots import make_subplots
                
                # Create Subplots: Row 1 = Price/MA, Row 2 = RSI
                fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                         vertical_spacing=0.05, row_heights=[0.7, 0.3])
                
                # Candlestick (Row 1)
                fig_tech.add_trace(go.Candlestick(
                    x=df_asset.index,
                    open=df_asset['Open'], high=df_asset['High'],
                    low=df_asset['Low'], close=df_asset['Close'],
                    name="OHLC"
                ), row=1, col=1)
                
                # Moving Averages (Row 1)
                colors = ['orange', 'blue', 'purple', 'black']
                for i, ma in enumerate(ma_windows):
                    if f'MA_{ma}' in df_asset.columns:
                        fig_tech.add_trace(go.Scatter(
                            x=df_asset.index, y=df_asset[f'MA_{ma}'], 
                            mode='lines', name=f'{ma} DMA',
                            line=dict(width=1, color=colors[i % len(colors)])
                        ), row=1, col=1)
                
                # RSI (Row 2)
                fig_tech.add_trace(go.Scatter(
                    x=df_asset.index, y=df_asset['RSI'], 
                    name='RSI (14)', line=dict(color='purple')
                ), row=2, col=1)
                
                # RSI Levels
                fig_tech.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig_tech.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                
                fig_tech.update_layout(height=600, title=f"{selected_asset} Technical Chart", 
                                       xaxis_rangeslider_visible=False, showlegend=True)
                st.plotly_chart(fig_tech, use_container_width=True)
            else:
                st.warning("Not enough data (minimum 14 days) to calculate technical indicators.")

if __name__ == "__main__":
    main()
