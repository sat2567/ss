"""Market data module for fetching and displaying financial market data."""
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_gold_price():
    """Fetch current gold price"""
    try:
        gold = yf.Ticker("GC=F")
        hist = gold.history(period="1d")
        return round(hist['Close'].iloc[-1], 2) if not hist.empty else 0
    except Exception as e:
        st.error(f"Error fetching gold price: {str(e)}")
        return 0

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

def display_market_data():
    """Display gold and US market data with interactive charts"""
    try:
        st.header("📊 Market Overview")
        
        # Create columns for layout
        cols = st.columns(5)
        
        # Gold price card
        with cols[0]:
            gold_price = get_gold_price()
            st.metric("Gold (per oz)", f"${gold_price:,.2f}", "")
            if st.button("View Gold Chart"):
                gold_chart = create_price_chart("GC=F")
                st.plotly_chart(gold_chart, use_container_width=True)
        
        # US Market indices
        us_market = get_us_market_data()
        if not us_market:
            st.warning("Could not fetch US market data. Please check your internet connection.")
            return
            
        for idx, (name, data) in enumerate(us_market.items(), 1):
            if idx >= len(cols):  # Ensure we don't exceed column count
                break
                
            with cols[idx]:
                st.metric(
                    name, 
                    f"${data['price']:,.2f}", 
                    f"{data['change']:+.2f}%",
                    delta_color=("normal" if data['change'] >= 0 else "inverse")
                )
                if st.button(f"View {name} Chart"):
                    chart = create_price_chart(data['ticker'])
                    st.plotly_chart(chart, use_container_width=True)
                    
    except Exception as e:
        st.error(f"Error displaying market data: {str(e)}")
