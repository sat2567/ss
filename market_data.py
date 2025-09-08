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

def get_weekly_change(ticker):
    """Get weekly percentage change for a ticker"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='5d')
        if len(hist) >= 2:
            return ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
        return 0
    except:
        return 0

def display_market_data():
    """Display simplified market data with price and weekly change"""
    try:
        st.header("📊 Market Overview")
        
        # Create columns for layout
        cols = st.columns(5)
        
        # Gold price
        with cols[0]:
            gold_price = get_gold_price()
            gold_change = get_weekly_change("GC=F")
            st.metric(
                "Gold (per oz)", 
                f"${gold_price:,.2f}",
                f"{gold_change:+.2f}%",
                delta_color=("normal" if gold_change >= 0 else "inverse")
            )
        
        # US Market indices
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^RUT': 'Russell 2000'
        }
        
        for idx, (ticker, name) in enumerate(indices.items(), 1):
            if idx >= len(cols):
                break
                
            with cols[idx]:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='1d')
                    if not hist.empty:
                        price = round(hist['Close'].iloc[-1], 2)
                        change = get_weekly_change(ticker)
                        st.metric(
                            name,
                            f"${price:,.2f}",
                            f"{change:+.2f}%",
                            delta_color=("normal" if change >= 0 else "inverse")
                        )
                except Exception as e:
                    st.error(f"Error fetching {name} data")
                    
    except Exception as e:
        st.error(f"Error displaying market data: {str(e)}")
