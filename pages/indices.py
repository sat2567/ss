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

# 1. Major Indices
INDEX_TICKERS = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP 100": "^NSMIDCP",
    "SMALLCAP (BSE)": "^BSSMLCAP", 
    "SENSEX": "^BSESN",
    "INDIA VIX": "^INDIAVIX"
}

# 2. Sectoral Indices
SECTOR_TICKERS = {
    "Bank": "^NSEBANK",
    "IT": "^CNXIT",
    "Auto": "^CNXAUTO",
    "Pharma": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "Metal": "^CNXMETAL",
    "Energy": "^CNXENERGY",
    "Realty": "^CNXREALTY",
    "Infra": "^CNXINFRA"
}

# --- Helper Functions ---

@st.cache_data(ttl=3600)
def fetch_data(ticker_dict, period="2y"):
    """
    Fetches OHLC data for a dictionary of tickers.
    Includes robust error handling to prevent IndexErrors.
    """
    data_dict = {}
    ticker_list = list(ticker_dict.values())
    
    try:
        # Bulk download
        raw_data = yf.download(ticker_list, period=period, group_by='ticker', auto_adjust=True)
    except Exception as e:
        st.error(f"Error connecting to Yahoo Finance: {e}")
        return {}
    
    for name, ticker in ticker_dict.items():
        try:
            # Handle structure differences (Single ticker vs Multi ticker)
            if len(ticker_list) == 1:
                df = raw_data.copy()
            else:
                # Check if ticker exists in the columns
                if ticker not in raw_data.columns.levels[0]:
                    continue
                df = raw_data[ticker].copy()
            
            # --- CRITICAL FIX: Empty Data Check ---
            if df.empty:
                continue

            # Drop rows where all columns are NaN
            df = df.dropna(how='all')
            
            # If df becomes empty after dropping NaNs, skip it
            if df.empty:
                continue

            # Forward fill to handle small data gaps (holidays/glitches)
            df = df.ffill() 
            
            # Remove Timezone
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            data_dict[name] = df
            
        except KeyError:
            continue
        except Exception:
            continue
            
    return data_dict

def calculate_rsi(series, period=14):
    """Calculates RSI."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_drawdown(series):
    """Calculates percentage drawdown."""
    rolling_max = series.cummax()
    drawdown = (series / rolling_max) - 1
    return drawdown * 100

# --- Main App Logic ---

def main():
    # 1. Sidebar Controls
    with st.sidebar:
        st.header("Dashboard Settings")
        refresh = st.button("🔄 Refresh Data")
        
        # Date Range Logic
        period_options = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
        selected_period = st.selectbox("Data Lookback Period", period_options, index=4)
        
        st.subheader("Chart Configuration")
        normalize = st.checkbox("Normalize Prices (Start=100)", value=True)
        ma_windows = st.multiselect("Moving Averages (Days)", [20, 50, 100, 200], default=[50, 200])

    # 2. Load Data
    if refresh:
        st.cache_data.clear()
    
    with st.spinner(f"Fetching {selected_period} of market data..."):
        index_data = fetch_data(INDEX_TICKERS, period=selected_period)
        sector_data = fetch_data(SECTOR_TICKERS, period=selected_period)

    # Global Data Check
    if not index_data and not sector_data:
        st.error("No data fetched. Try refreshing or checking your internet connection.")
        return

    st.title("🇮🇳 Indian Market Dashboard")
    st.markdown(f"*Data Snapshot: Past {selected_period}*")

    # 3. KPI Cards (Indices Only)
    st.subheader("Market Snapshot")
    
    kpi_indices = ["NIFTY 50", "NIFTY BANK", "NIFTY MIDCAP 100", "SMALLCAP (BSE)", "INDIA VIX"]
    cols = st.columns(len(kpi_indices))
    
    for i, name in enumerate(kpi_indices):
        # Default values
        val_str = "N/A"
        delta_str = "N/A"
        color = "off"

        if name in index_data:
            df = index_data[name]
            
            # --- CRITICAL FIX: Check length before accessing .iloc ---
            if not df.empty:
                current_price = df['Close'].iloc[-1]
                val_str = f"{current_price:,.2f}"

                if len(df) >= 2:
                    prev_price = df['Close'].iloc[-2]
                    daily_change = current_price - prev_price
                    daily_pct = (daily_change / prev_price) * 100
                    delta_str = f"{daily_pct:.2f}%"
                
                # VIX logic (Red is good if VIX drops)
                if name == "INDIA VIX":
                    color = "inverse"
                else:
                    color = "normal"

        cols[i].metric(
            label=name,
            value=val_str,
            delta=delta_str,
            delta_color=color
        )

    # 4. Tabs for Analysis
    tab_compare, tab_sectors, tab_risk, tab_deep_dive = st.tabs([
        "📊 Index Comparison", 
        "🏢 Sector Performance", 
        "📉 Risk & Volatility", 
        "🕯️ Technical Deep Dive"
    ])
    
    available_indices = list(index_data.keys())

    # --- TAB 1: COMPARISON ---
    with tab_compare:
        st.subheader("Relative Performance")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Ensure default selection exists in available keys
            default_sel = [x for x in ["NIFTY 50", "NIFTY MIDCAP 100", "SMALLCAP (BSE)"] if x in available_indices]
            indices_to_plot = st.multiselect("Select Indices", available_indices, default=default_sel)
            
            fig_compare = go.Figure()
            
            for name in indices_to_plot:
                if name in index_data:
                    df = index_data[name].copy()
                    if df.empty: continue # Safety check
                    
                    y_data = df['Close']
                    
                    if normalize:
                        start_val = y_data.iloc[0]
                        # Avoid division by zero
                        if start_val == 0: start_val = 1 
                        y_data = (y_data / start_val) * 100
                        title_y = "Normalized (Base=100)"
                    else:
                        title_y = "Price"
                        
                    fig_compare.add_trace(go.Scatter(x=df.index, y=y_data, mode='lines', name=name))
            
            fig_compare.update_layout(yaxis_title=title_y, height=450, hovermode="x unified", margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_compare, use_container_width=True)

        with col2:
            st.markdown("**Correlation Matrix**")
            if len(indices_to_plot) > 1:
                price_dict = {name: index_data[name]['Close'] for name in indices_to_plot if name in index_data and not index_data[name].empty}
                if price_dict:
                    close_df = pd.DataFrame(price_dict)
                    corr_matrix = close_df.pct_change().corr()
                    
                    fig_corr = px.imshow(
                        corr_matrix, 
                        text_auto=".2f", 
                        color_continuous_scale='RdBu', 
                        zmin=-1, zmax=1,
                        aspect="auto"
                    )
                    fig_corr.update_layout(height=450)
                    st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("Select at least 2 indices.")

    # --- TAB 2: SECTORS ---
    with tab_sectors:
        st.subheader("Sector Rotation")
        
        if not sector_data:
            st.warning("Sector data not available.")
        else:
            col_sec1, col_sec2 = st.columns([1, 2])
            
            sector_returns = {}
            for name, df in sector_data.items():
                if not df.empty:
                    start = df['Close'].iloc[0]
                    end = df['Close'].iloc[-1]
                    if start != 0:
                        ret = ((end - start) / start) * 100
                        sector_returns[name] = ret
            
            if sector_returns:
                df_ret = pd.DataFrame(list(sector_returns.items()), columns=['Sector', 'Return'])
                df_ret = df_ret.sort_values(by='Return', ascending=True)
                df_ret['Color'] = df_ret['Return'].apply(lambda x: '#2ecc71' if x >= 0 else '#e74c3c')

                with col_sec1:
                    st.markdown(f"**Total Return ({selected_period})**")
                    fig_bar = go.Figure()
                    fig_bar.add_trace(go.Bar(
                        y=df_ret['Sector'], 
                        x=df_ret['Return'],
                        orientation='h',
                        marker=dict(color=df_ret['Color']),
                        text=df_ret['Return'].apply(lambda x: f"{x:.1f}%"),
                        textposition='auto'
                    ))
                    fig_bar.update_layout(height=500, margin=dict(l=0, r=0, t=20, b=0))
                    st.plotly_chart(fig_bar, use_container_width=True)

                with col_sec2:
                    st.markdown("**Relative Strength**")
                    # Safe default selection
                    avail_sectors = list(sector_data.keys())
                    sel_sectors = st.multiselect("Compare Sectors", avail_sectors, default=avail_sectors[:5] if len(avail_sectors) > 5 else avail_sectors)
                    
                    fig_sec_line = go.Figure()
                    for name in sel_sectors:
                        if name in sector_data:
                            df = sector_data[name]
                            if not df.empty:
                                start_val = df['Close'].iloc[0]
                                if start_val == 0: start_val = 1
                                norm_price = (df['Close'] / start_val) * 100
                                fig_sec_line.add_trace(go.Scatter(x=df.index, y=norm_price, name=name))
                    
                    fig_sec_line.update_layout(yaxis_title="Rebased to 100", height=500, hovermode="x unified")
                    st.plotly_chart(fig_sec_line, use_container_width=True)

    # --- TAB 3: RISK ---
    with tab_risk:
        col_risk1, col_risk2 = st.columns([2, 1])
        
        with col_risk1:
            st.subheader("Drawdown Analysis")
            fig_dd = go.Figure()
            for name in indices_to_plot:
                if name in index_data and not index_data[name].empty:
                    dd = calculate_drawdown(index_data[name]['Close'])
                    fig_dd.add_trace(go.Scatter(x=dd.index, y=dd, name=name, fill='tozeroy'))
            fig_dd.update_layout(yaxis_title="Drawdown %", height=400, hovermode="x unified")
            st.plotly_chart(fig_dd, use_container_width=True)

        with col_risk2:
            st.subheader("Risk Metrics")
            vol_list = []
            for name in indices_to_plot:
                if name in index_data and not index_data[name].empty:
                    df = index_data[name]
                    if len(df) > 1:
                        returns = df['Close'].pct_change().dropna()
                        ann_vol = returns.std() * np.sqrt(252) * 100
                        max_dd = calculate_drawdown(df['Close']).min()
                        vol_list.append({
                            "Index": name,
                            "Volatility": f"{ann_vol:.2f}%",
                            "Max Drawdown": f"{max_dd:.2f}%"
                        })
            st.dataframe(pd.DataFrame(vol_list), use_container_width=True, hide_index=True)

    # --- TAB 4: DEEP DIVE ---
    with tab_deep_dive:
        st.subheader("Technical Analysis")
        
        all_assets = {**index_data, **sector_data}
        # Filter out empty dataframes
        valid_assets = {k: v for k, v in all_assets.items() if not v.empty}
        
        if not valid_assets:
            st.error("No valid data available for analysis.")
        else:
            col_dd_1, col_dd_2 = st.columns([1, 3])
            
            with col_dd_1:
                selected_asset = st.selectbox("Select Asset", list(valid_assets.keys()))
                df_asset = valid_assets[selected_asset].copy()
                
                # Indicators
                df_asset['RSI'] = calculate_rsi(df_asset['Close'])
                for ma in ma_windows:
                    df_asset[f'MA_{ma}'] = df_asset['Close'].rolling(window=ma).mean()
                
                if not df_asset.empty:
                    latest_close = df_asset['Close'].iloc[-1]
                    latest_rsi = df_asset['RSI'].iloc[-1]
                    
                    st.metric("Current Price", f"{latest_close:,.2f}")
                    st.metric("RSI (14)", f"{latest_rsi:.2f}")
                    
                    st.markdown("---")
                    st.markdown("**Recent Data**")
                    st.dataframe(df_asset[['Close', 'RSI']].tail(10).sort_index(ascending=False), use_container_width=True)

            with col_dd_2:
                if 'RSI' in df_asset.columns and not df_asset.empty:
                    from plotly.subplots import make_subplots
                    
                    fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                             vertical_spacing=0.03, row_heights=[0.7, 0.3])
                    
                    # Price & MA
                    fig_tech.add_trace(go.Candlestick(
                        x=df_asset.index, open=df_asset['Open'], high=df_asset['High'],
                        low=df_asset['Low'], close=df_asset['Close'], name="Price"
                    ), row=1, col=1)
                    
                    colors = ['#f39c12', '#2980b9', '#8e44ad', '#2c3e50']
                    for i, ma in enumerate(ma_windows):
                        if f'MA_{ma}' in df_asset.columns:
                            fig_tech.add_trace(go.Scatter(
                                x=df_asset.index, y=df_asset[f'MA_{ma}'], 
                                mode='lines', name=f'{ma} DMA',
                                line=dict(width=1, color=colors[i % len(colors)])
                            ), row=1, col=1)
                    
                    # RSI
                    fig_tech.add_trace(go.Scatter(x=df_asset.index, y=df_asset['RSI'], name='RSI', line=dict(color='#e74c3c')), row=2, col=1)
                    fig_tech.add_hline(y=70, line_dash="dash", line_color="gray", row=2, col=1)
                    fig_tech.add_hline(y=30, line_dash="dash", line_color="gray", row=2, col=1)
                    
                    fig_tech.update_layout(height=600, xaxis_rangeslider_visible=False, title=f"{selected_asset} Chart")
                    st.plotly_chart(fig_tech, use_container_width=True)

if __name__ == "__main__":
    main()
