"""Market data module for fetching and displaying financial market data."""
import streamlit as st
import requests
from datetime import datetime, timedelta

def get_market_data():
    """Fetch market data using a simple API"""
    try:
        # Using a free market data API
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching market data: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_us_market_data():
    """Fetch major US market indices"""
    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ',
        '^RUT': 'Russell 2000'
    }
    
    market_data = {}
    for ticker, name in indices.items():
        try:
            data = yf.Ticker(ticker)
            hist = data.history(period='5d')
            if not hist.empty:
                market_data[name] = {
                    'ticker': ticker,
                    'price': round(hist['Close'].iloc[-1], 2),
                    'change': round(((hist['Close'].iloc[-1] / hist['Close'].iloc[-2]) - 1) * 100, 2) if len(hist) > 1 else 0
                }
        except Exception as e:
            st.error(f"Error fetching {name} data: {str(e)}")
    return market_data

def create_price_chart(ticker, period='1y'):
    """Create interactive price chart using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'],
            name='Price',
            line=dict(color='#1f77b4')
        ))
        
        fig.update_layout(
            title=f"{ticker} Price Chart",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        return None

def get_weekly_change(ticker):
    """Get weekly percentage change for a ticker"""
    try:
        print(f"Fetching data for {ticker}")
        stock = yf.Ticker(ticker)
        hist = stock.history(period='5d')
        print(f"History for {ticker}:")
        print(hist)
        if len(hist) >= 2:
            change = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
            print(f"Calculated change for {ticker}: {change}%")
            return change
        return 0
    except Exception as e:
        print(f"Error in get_weekly_change for {ticker}: {str(e)}")
        return 0

def display_market_data():
    """Display simplified market data"""
    st.header("📊 Market Overview")
    
    # Create columns for layout
    cols = st.columns(5)
    
    # Using a simple API for demonstration
    try:
        data = get_market_data()
        
        if data:
            # Bitcoin
            with cols[0]:
                btc_price = data.get('bitcoin', {}).get('usd', 'N/A')
                btc_change = data.get('bitcoin', {}).get('usd_24h_change', 0)
                st.metric(
                    "Bitcoin (BTC)",
                    f"${btc_price:,.2f}" if isinstance(btc_price, (int, float)) else btc_price,
                    f"{btc_change:+.2f}%" if isinstance(btc_change, (int, float)) else "N/A",
                    delta_color=("normal" if isinstance(btc_change, (int, float)) and btc_change >= 0 else "inverse")
                )
            
            # Ethereum
            with cols[1]:
                eth_price = data.get('ethereum', {}).get('usd', 'N/A')
                eth_change = data.get('ethereum', {}).get('usd_24h_change', 0)
                st.metric(
                    "Ethereum (ETH)",
                    f"${eth_price:,.2f}" if isinstance(eth_price, (int, float)) else eth_price,
                    f"{eth_change:+.2f}%" if isinstance(eth_change, (int, float)) else "N/A",
                    delta_color=("normal" if isinstance(eth_change, (int, float)) and eth_change >= 0 else "inverse")
                )
        else:
            st.warning("Could not fetch live market data. Please check your internet connection.")
            
    except Exception as e:
        st.error(f"Error displaying market data: {str(e)}")
