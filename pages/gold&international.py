import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
import numpy as np

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Global Markets Dashboard")

# --- Constants & Ticker Mapping ---
# Selected Major Global Indices & Commodities
GLOBAL_TICKERS = {
    "🇺🇸 S&P 500": "^GSPC",
    "🇺🇸 Nasdaq 100": "^NDX",
    "🇺🇸 Dow Jones": "^DJI",
    "🇬🇧 FTSE 100 (UK)": "^FTSE",
    "🇩🇪 DAX (Germany)": "^GDAXI",
    "🇫🇷 CAC 40 (France)": "^FCHI",
    "🇯🇵 Nikkei 225": "^N225",
    "🇰🇷 KOSPI": "^KS11",
    "🇭🇰 Hang Seng": "^HSI",
    "🇨🇳 Shanghai Comp": "000001.SS",
    "🥇 Gold (Futures)": "GC=F",
    "🛢️ Crude Oil": "CL=F",
    "🥈 Silver": "SI=F"
}

# --- Helper Functions ---

@st.cache_data(ttl=3600)
def fetch_global_data(ticker_dict, period="1y"):
    """
    Fetches data for global tickers with robust error handling for different timezones.
    """
    data_dict = {}
    ticker_list = list(ticker_dict.values())
    
    try:
        # Bulk download
        raw_data = yf.download(ticker_list, period=period, group_by='ticker', auto_adjust=True, threads=True)
    except Exception as e:
        st.error(f"API Error: {e}")
        return {}
    
    for name, ticker in ticker_dict.items():
        try:
            # Handle single vs multi-ticker structure
            if len(ticker_list) == 1:
                df = raw_data.copy()
            else:
                if ticker not in raw_data.columns.levels[0]:
                    continue
                df = raw_data[ticker].copy()
            
            if df.empty: continue

            # Basic Cleaning
            df = df.dropna(how='all')
            
            # CRITICAL: Forward fill is essential for global data because markets 
            # are open at different times (e.g., Nikkei is closed when S&P is open).
            df = df.ffill()
            
            # Remove Timezones for uniform plotting
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            data_dict[name] = df
        except KeyError:
            continue
            
    return data_dict

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- Main Application ---

def main():
    # 1. Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Dashboard Settings")
        refresh = st.button("🔄 Refresh Data")
        
        period_options = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
        selected_period = st.selectbox("Lookback Period", period_options, index=3)
        
        st.subheader("Chart Options")
        normalize = st.checkbox("Normalize (Start=100)", value=True, help="Rebases all indices to 100 at the start date for easy comparison.")
        ma_windows = st.multiselect("Moving Averages", [50, 100, 200], default=[50, 200])

    if refresh:
        st.cache_data.clear()

    # 2. Fetch Data
    with st.spinner(f"Fetching global market data ({selected_period})..."):
        market_data = fetch_global_data(GLOBAL_TICKERS, period=selected_period)

    if not market_data:
        st.error("Could not fetch data. Please check your internet connection.")
        return

    st.title("🌍 Global Markets Overview")
    st.markdown(f"**Status:** Live Analysis | **Period:** {selected_period}")

    # 3. Dynamic KPI Cards
    st.subheader("Market Snapshot (Latest Close)")
    
    # Select top key indices for the snapshot
    key_indices = ["🇺🇸 S&P 500", "🇯🇵 Nikkei 225", "🇬🇧 FTSE 100", "🥇 Gold (Futures)", "🛢️ Crude Oil"]
    
    cols = st.columns(len(key_indices))
    for i, name in enumerate(key_indices):
        if name in market_data:
            df = market_data[name]
            if not df.empty:
                current_price = df['Close'].iloc[-1]
                
                # Calculate change
                if len(df) >= 2:
                    prev_price = df['Close'].iloc[-2]
                    daily_change = current_price - prev_price
                    daily_pct = (daily_change / prev_price) * 100
                    delta_str = f"{daily_pct:.2f}%"
                else:
                    delta_str = "N/A"
                
                cols[i].metric(label=name, value=f"{current_price:,.2f}", delta=delta_str)

    # 4. Analysis Tabs
    tab_compare, tab_perf, tab_deep = st.tabs(["📊 Trend Comparison", "🏆 Performance Ranking", "🕯️ Technical Deep Dive"])

    # --- TAB 1: TREND COMPARISON ---
    with tab_compare:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Price History")
            selected_comparison = st.multiselect(
                "Select Assets to Compare", 
                list(market_data.keys()), 
                default=["🇺🇸 S&P 500", "🇯🇵 Nikkei 225", "🥇 Gold (Futures)"]
            )
            
            fig_comp = go.Figure()
            for name in selected_comparison:
                df = market_data[name]
                y_data = df['Close']
                
                if normalize:
                    start_val = y_data.iloc[0]
                    if start_val == 0: start_val = 1 # Avoid div by zero
                    y_data = (y_data / start_val) * 100
                    y_title = "Normalized (Base=100)"
                else:
                    y_title = "Price"
                
                fig_comp.add_trace(go.Scatter(x=df.index, y=y_data, name=name))
            
            fig_comp.update_layout(yaxis_title=y_title, height=500, hovermode="x unified")
            st.plotly_chart(fig_comp, use_container_width=True)

        with col2:
            st.markdown("**Correlation Matrix**")
            st.caption("How closely do these markets move together?")
            
            if len(selected_comparison) > 1:
                # Build correlation DF
                price_dict = {name: market_data[name]['Close'] for name in selected_comparison}
                close_df = pd.DataFrame(price_dict)
                # Drop NaN created by non-overlapping holidays
                corr_matrix = close_df.pct_change().corr()
                
                fig_corr = px.imshow(
                    corr_matrix, 
                    text_auto=".2f", 
                    color_continuous_scale='RdBu', 
                    zmin=-1, zmax=1, aspect="auto"
                )
                fig_corr.update_layout(height=500)
                st.plotly_chart(fig_corr, use_container_width=True)

    # --- TAB 2: PERFORMANCE RANKING ---
    with tab_perf:
        st.subheader(f"Asset Returns over {selected_period}")
        
        returns_dict = {}
        for name, df in market_data.items():
            if not df.empty:
                start = df['Close'].iloc[0]
                end = df['Close'].iloc[-1]
                ret = ((end - start) / start) * 100
                returns_dict[name] = ret
        
        df_ret = pd.DataFrame(list(returns_dict.items()), columns=['Asset', 'Return'])
        df_ret = df_ret.sort_values(by='Return', ascending=True)
        df_ret['Color'] = df_ret['Return'].apply(lambda x: '#2ecc71' if x >= 0 else '#e74c3c')
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=df_ret['Asset'],
            x=df_ret['Return'],
            orientation='h',
            marker=dict(color=df_ret['Color']),
            text=df_ret['Return'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto'
        ))
        
        fig_bar.update_layout(
            title="Winners vs. Losers", 
            xaxis_title="Total Return (%)", 
            height=600
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TAB 3: TECHNICAL DEEP DIVE ---
    with tab_deep:
        st.subheader("Technical Analysis")
        col_dd1, col_dd2 = st.columns([1, 3])
        
        with col_dd1:
            selected_asset = st.selectbox("Analyze Asset", list(market_data.keys()))
            df_asset = market_data[selected_asset].copy()
            
            # Calc Indicators
            df_asset['RSI'] = calculate_rsi(df_asset['Close'])
            for ma in ma_windows:
                df_asset[f'MA_{ma}'] = df_asset['Close'].rolling(window=ma).mean()
            
            last_close = df_asset['Close'].iloc[-1]
            last_rsi = df_asset['RSI'].iloc[-1]
            
            st.metric("Latest Price", f"{last_close:,.2f}")
            st.metric("RSI (14-Day)", f"{last_rsi:.2f}")
            
            if last_rsi > 70:
                st.warning("⚠️ Overbought Zone")
            elif last_rsi < 30:
                st.success("✅ Oversold Zone")
            else:
                st.info("ℹ️ Neutral Zone")

            st.write("Recent Data:")
            st.dataframe(df_asset[['Close', 'RSI']].tail(10).sort_index(ascending=False), use_container_width=True)

        with col_dd2:
            # Candlestick Chart with Subplots
            from plotly.subplots import make_subplots
            
            fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            
            # 1. Candlestick
            fig_tech.add_trace(go.Candlestick(
                x=df_asset.index,
                open=df_asset['Open'], high=df_asset['High'],
                low=df_asset['Low'], close=df_asset['Close'],
                name="OHLC"
            ), row=1, col=1)
            
            # 

[Image of candlestick chart explanation]

            
            # 2. Moving Averages
            colors = ['orange', 'blue', 'purple']
            for i, ma in enumerate(ma_windows):
                if f'MA_{ma}' in df_asset.columns:
                    fig_tech.add_trace(go.Scatter(
                        x=df_asset.index, y=df_asset[f'MA_{ma}'],
                        mode='lines', name=f'{ma}-Day MA',
                        line=dict(width=1.5, color=colors[i % len(colors)])
                    ), row=1, col=1)

            # 3. RSI
            fig_tech.add_trace(go.Scatter(
                x=df_asset.index, y=df_asset['RSI'],
                name="RSI", line=dict(color='purple', width=1)
            ), row=2, col=1)
            
            # RSI Bands
            fig_tech.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig_tech.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
            
            fig_tech.update_layout(
                height=600, 
                title=f"{selected_asset} Technicals",
                xaxis_rangeslider_visible=False,
                showlegend=True
            )
            st.plotly_chart(fig_tech, use_container_width=True)

if __name__ == "__main__":
    main()
