import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Advanced Market Dashboard")

# --- Constants & Ticker Mapping ---
# Yahoo Finance Tickers for Indian Indices
TICKERS = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP 100": "^NSMIDCP", # Yahoo often uses ^NSMIDCP for Nifty Midcap Select or similar variants
    "NIFTY SMALLCAP 100": "^CNXSC", # Ticker might vary, using standard smallcap index proxy
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
            df = raw_data[ticker].copy()
            if not df.empty:
                # Drop rows with NaN (holidays/weekends)
                df.dropna(inplace=True)
                data_dict[name] = df
        except KeyError:
            st.error(f"Could not fetch data for {name} ({ticker})")
            
    return data_dict

def calculate_rsi(series, period=14):
    """Calculates RSI manually to avoid heavy dependencies like pandas-ta."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_drawdown(series):
    """Calculates percentage drawdown from peak."""
    rolling_max = series.cummax()
    drawdown = (series / rolling_max) - 1
    return drawdown * 100

# --- Main App Layout ---

def main():
    st.title("📈 Indian Market Dashboard: Live Analysis")
    st.markdown("Real-time data fetched via Yahoo Finance | Comparison, Risk & Technicals")

    # 1. Sidebar Controls
    with st.sidebar:
        st.header("Settings")
        refresh = st.button("🔄 Refresh Data")
        
        # Date Range Logic
        period_options = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
        selected_period = st.selectbox("Data Lookback Period", period_options, index=4)
        
        st.subheader("Chart Settings")
        normalize = st.checkbox("Normalize Prices (Start=100)", value=True)
        ma_windows = st.multiselect("Moving Averages", [20, 50, 100, 200], default=[50, 200])

    # 2. Load Data
    if refresh:
        st.cache_data.clear()
    
    with st.spinner("Fetching market data..."):
        market_data = fetch_data(period=selected_period)

    if not market_data:
        st.error("No data available. Please check your internet connection.")
        return

    # 3. Dynamic KPI Cards
    st.subheader("Market Snapshot")
    cols = st.columns(len(market_data))
    
    for i, (name, df) in enumerate(market_data.items()):
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        daily_change = current_price - prev_price
        daily_pct = (daily_change / prev_price) * 100
        
        cols[i].metric(
            label=name,
            value=f"{current_price:,.0f}",
            delta=f"{daily_pct:.2f}%"
        )

    # 4. Tabs for Analysis
    tab_compare, tab_risk, tab_deep_dive = st.tabs(["📊 Index Comparison", "📉 Risk & Drawdown", "🕯️ Technical Deep Dive"])

    # --- TAB 1: COMPARISON & CORRELATION ---
    with tab_compare:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Price Performance Comparison")
            indices_to_plot = st.multiselect("Select Indices", list(market_data.keys()), default=list(market_data.keys()))
            
            fig_compare = go.Figure()
            for name in indices_to_plot:
                df = market_data[name]
                y_data = df['Close']
                
                if normalize:
                    # Normalize to 100 at the start
                    start_val = y_data.iloc[0]
                    y_data = (y_data / start_val) * 100
                    title_y = "Normalized Price (Start=100)"
                else:
                    title_y = "Price"
                    
                fig_compare.add_trace(go.Scatter(x=df.index, y=y_data, mode='lines', name=name))
            
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

    # --- TAB 2: RISK ANALYSIS ---
    with tab_risk:
        st.subheader("Underwater Plot (Drawdowns)")
        st.markdown("Shows how far each index has fallen from its all-time high within the selected period.")
        
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
            returns = df['Close'].pct_change().dropna()
            # Annualized Volatility = Daily Std Dev * Sqrt(252)
            ann_vol = returns.std() * np.sqrt(252) * 100
            max_dd = calculate_drawdown(df['Close']).min()
            
            vol_data.append({
                "Index": name, 
                "Annualized Volatility": f"{ann_vol:.2f}%",
                "Max Drawdown (Period)": f"{max_dd:.2f}%"
            })
            
        st.dataframe(pd.DataFrame(vol_data), use_container_width=True)

    # --- TAB 3: DEEP DIVE ---
    with tab_deep_dive:
        st.subheader("Technical Deep Dive")
        
        col_dd_1, col_dd_2 = st.columns([1, 3])
        
        with col_dd_1:
            selected_asset = st.selectbox("Select Asset to Analyze", list(market_data.keys()))
            df_asset = market_data[selected_asset].copy()
            
            # Calculate Indicators
            df_asset['RSI'] = calculate_rsi(df_asset['Close'])
            for ma in ma_windows:
                df_asset[f'MA_{ma}'] = df_asset['Close'].rolling(window=ma).mean()
                
            st.dataframe(df_asset[['Close', 'RSI']].tail(10).sort_index(ascending=False), use_container_width=True)

        with col_dd_2:
            # Create Subplots: Row 1 = Price/MA, Row 2 = RSI
            from plotly.subplots import make_subplots
            
            fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                     vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            # Candlestick
            fig_tech.add_trace(go.Candlestick(
                x=df_asset.index,
                open=df_asset['Open'], high=df_asset['High'],
                low=df_asset['Low'], close=df_asset['Close'],
                name="OHLC"
            ), row=1, col=1)
            
            # Moving Averages
            colors = ['orange', 'blue', 'purple', 'black']
            for i, ma in enumerate(ma_windows):
                if f'MA_{ma}' in df_asset.columns:
                    fig_tech.add_trace(go.Scatter(
                        x=df_asset.index, y=df_asset[f'MA_{ma}'], 
                        mode='lines', name=f'{ma} DMA',
                        line=dict(width=1, color=colors[i % len(colors)])
                    ), row=1, col=1)
            
            # RSI
            fig_tech.add_trace(go.Scatter(
                x=df_asset.index, y=df_asset['RSI'], 
                name='RSI (14)', line=dict(color='purple')
            ), row=2, col=1)
            
            # RSI Levels
            fig_tech.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig_tech.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig_tech.update_layout(height=600, title=f"{selected_asset} Technical Chart", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_tech, use_container_width=True)

if __name__ == "__main__":
    main()
