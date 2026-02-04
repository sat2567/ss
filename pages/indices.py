"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     🇮🇳 PRO QUANT INDIA MULTI-CAP DASHBOARD (3 Indices) 🇮🇳                    ║
║                                                                              ║
║  India-Calibrated Valuation: Nifty 50 | Midcap 100 | Smallcap 250           ║
║  Analysis Period: April 2021 - Present                                       ║
║                                                                              ║
║  USAGE:  streamlit run pro_quant_dashboard.py                                ║
║  REQUIREMENTS: pip install streamlit pandas numpy plotly                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Pro Quant India 3-Cap Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

try:
    SCRIPT_DIR = Path(__file__).parent.resolve()
except:
    SCRIPT_DIR = Path.cwd()

# Analysis start date
ANALYSIS_START = '2021-04-01'

# ══════════════════════════════════════════════════════════════════════════════
# INDIA-CALIBRATED THRESHOLDS (Based on April 2021 - Present Analysis)
# ══════════════════════════════════════════════════════════════════════════════

"""
CALIBRATION DATA (April 2021 - Present):

NIFTY 50:
- PE: Mean 22.83, Median 22.31, Range 18.9-33.6
- PB: Mean 3.99, Median 4.08, Range 3.26-4.88
- Div: Mean 1.27%, Median 1.28%

MIDCAP 100:
- PE: Mean 30.31, Median 29.63, Range 20.6-45.4
- PB: Mean 3.82, Median 3.54, Range 2.47-5.58
- Div: Mean 0.97%, Median 0.91%

SMALLCAP 250:
- PE: Mean 27.57, Median 28.54, Range 16.9-48.2
- PB: Mean 3.62, Median 3.62, Range 2.74-4.66
- Div: Mean 0.91%, Median 0.88%
"""

# Thresholds based on percentiles
THRESHOLDS = {
    'nifty50': {
        'pe': {'p10': 20.6, 'p25': 21.5, 'p50': 22.3, 'p75': 23.1, 'p90': 26.6},
        'pb': {'p10': 3.45, 'p25': 3.62, 'p50': 4.08, 'p75': 4.28, 'p90': 4.43},
        'div': {'p10': 1.13, 'p25': 1.20, 'p50': 1.28, 'p75': 1.36, 'p90': 1.41}
    },
    'midcap': {
        'pe': {'p10': 22.8, 'p25': 24.5, 'p50': 29.6, 'p75': 34.2, 'p90': 41.9},
        'pb': {'p10': 2.95, 'p25': 3.14, 'p50': 3.54, 'p75': 4.45, 'p90': 5.06},
        'div': {'p10': 0.75, 'p25': 0.82, 'p50': 0.91, 'p75': 1.19, 'p90': 1.29}
    },
    'smallcap': {
        'pe': {'p10': 18.9, 'p25': 21.8, 'p50': 28.5, 'p75': 31.4, 'p90': 33.8},
        'pb': {'p10': 3.00, 'p25': 3.26, 'p50': 3.62, 'p75': 3.93, 'p90': 4.26},
        'div': {'p10': 0.67, 'p25': 0.77, 'p50': 0.88, 'p75': 1.05, 'p90': 1.13}
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# CSS STYLES
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

.stApp { background: linear-gradient(180deg, #0a0f1a 0%, #111827 100%); }
#MainMenu, footer, header {visibility: hidden;}

.main-title {
    font-family: 'Orbitron', monospace;
    font-size: 1.8rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #ff9933, #ffffff, #138808);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    padding: 0.5rem 0;
}

.subtitle { font-family: 'Rajdhani', sans-serif; color: #64748b; text-align: center; font-size: 0.85rem; margin-bottom: 0.75rem; }

.index-card {
    background: linear-gradient(135deg, #111827, #1f2937);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 0.75rem;
    margin: 0.25rem 0;
}

.index-header {
    font-family: 'Orbitron', monospace;
    font-size: 0.9rem;
    font-weight: 700;
    padding: 0.4rem 0.75rem;
    border-radius: 6px;
    text-align: center;
    margin-bottom: 0.5rem;
}

.nifty-header { background: linear-gradient(135deg, #1e3a5f, #0f172a); color: #3b82f6; border: 1px solid #3b82f6; }
.midcap-header { background: linear-gradient(135deg, #3d1e5f, #1a0f2e); color: #8b5cf6; border: 1px solid #8b5cf6; }
.smallcap-header { background: linear-gradient(135deg, #1e5f3d, #0f2e1a); color: #10b981; border: 1px solid #10b981; }

.metric-row {
    display: flex;
    justify-content: space-between;
    padding: 0.3rem 0;
    border-bottom: 1px solid #1e3a5f;
}

.metric-label { font-family: 'Rajdhani', sans-serif; font-size: 0.75rem; color: #64748b; }
.metric-value { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 600; color: #e2e8f0; }
.metric-pctl { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; padding: 0.1rem 0.4rem; border-radius: 10px; }

.pctl-low { background: rgba(16,185,129,0.2); color: #10b981; }
.pctl-mid { background: rgba(245,158,11,0.2); color: #f59e0b; }
.pctl-high { background: rgba(239,68,68,0.2); color: #ef4444; }

.signal-badge {
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    display: inline-block;
    text-align: center;
    width: 100%;
}

.signal-buy { background: linear-gradient(135deg, #059669, #10b981); color: white; }
.signal-accumulate { background: linear-gradient(135deg, #0891b2, #06b6d4); color: white; }
.signal-hold { background: linear-gradient(135deg, #d97706, #f59e0b); color: white; }
.signal-trim { background: linear-gradient(135deg, #ea580c, #f97316); color: white; }
.signal-sell { background: linear-gradient(135deg, #dc2626, #ef4444); color: white; }

.comparison-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
}

.comparison-table th {
    background: #1e3a5f;
    color: #e2e8f0;
    padding: 0.5rem;
    text-align: center;
}

.comparison-table td {
    padding: 0.4rem;
    text-align: center;
    border-bottom: 1px solid #1e3a5f;
    color: #e2e8f0;
}

.winner { background: rgba(16,185,129,0.2); color: #10b981; font-weight: bold; }
.loser { background: rgba(239,68,68,0.1); }

.section-header {
    font-family: 'Orbitron', monospace;
    font-size: 0.95rem;
    color: #e2e8f0;
    padding: 0.4rem 0.75rem;
    margin: 0.75rem 0 0.5rem 0;
    background: linear-gradient(90deg, rgba(255,153,51,0.2), transparent);
    border-left: 3px solid #ff9933;
    border-radius: 0 6px 6px 0;
}

.divider { height: 1px; background: linear-gradient(90deg, transparent, #ff9933, #138808, transparent); margin: 0.75rem 0; }

.info-box { border-radius: 6px; padding: 0.6rem; margin: 0.4rem 0; font-size: 0.8rem; }
.info-success { background: linear-gradient(135deg, #064e3b, #111827); border-left: 3px solid #10b981; color: #e2e8f0; }
.info-warning { background: linear-gradient(135deg, #451a03, #111827); border-left: 3px solid #f59e0b; color: #e2e8f0; }
.info-danger { background: linear-gradient(135deg, #450a0a, #111827); border-left: 3px solid #ef4444; color: #e2e8f0; }

.premium-positive { color: #ef4444; }
.premium-negative { color: #10b981; }

[data-testid="stSidebar"] { background: linear-gradient(180deg, #111827, #0a0f1a); }
.stTabs [data-baseweb="tab-list"] { background: #111827; padding: 4px; border-radius: 6px; }
.stTabs [data-baseweb="tab"] { font-size: 0.8rem; color: #64748b; }
.stTabs [aria-selected="true"] { background: #1e3a5f; color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def find_file(names):
    locations = [SCRIPT_DIR, Path.cwd(), SCRIPT_DIR/"data", Path.cwd()/"data"]
    for loc in locations:
        if loc.exists():
            for name in names:
                if (loc / name).exists():
                    return loc / name
    return None

@st.cache_data(ttl=3600)
def load_all_data():
    data = {}
    
    # Nifty 50
    path = find_file(['Nifty50_PE_PB_Div_Merged.csv'])
    if path:
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.rename(columns={'PE': 'PE', 'PB': 'PB', 'DivYield': 'DivYield'})
        data['nifty50'] = df[df['Date'] >= ANALYSIS_START].copy()
    
    # Midcap 100
    path = find_file(['NiftyMidcap100_PE_PB_Div_Merged.csv'])
    if path:
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.rename(columns={'PE': 'PE', 'PB': 'PB', 'DivYield': 'DivYield'})
        data['midcap'] = df[df['Date'] >= ANALYSIS_START].copy()
    
    # Smallcap 250
    path = find_file(['NiftySmallcap250_PE_PB_Div_Merged.csv'])
    if path:
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.rename(columns={'PE': 'PE', 'PB': 'PB', 'DivYield': 'DivYield'})
        data['smallcap'] = df[df['Date'] >= ANALYSIS_START].copy()
    
    # Calculate percentiles for each
    for key in data:
        df = data[key]
        df['PE_Pctl'] = df['PE'].rank(pct=True) * 100
        df['PB_Pctl'] = df['PB'].rank(pct=True) * 100
        df['DivYield_Pctl'] = (1 - df['DivYield'].rank(pct=True)) * 100  # Inverted - higher div is better
        data[key] = df
    
    return data

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_percentile_signal(pctl, inverted=False):
    """Get signal based on percentile (lower is better for PE/PB, higher for Div)"""
    if inverted:
        pctl = 100 - pctl
    
    if pctl <= 20:
        return 'VERY CHEAP', 2, 'pctl-low'
    elif pctl <= 40:
        return 'CHEAP', 1, 'pctl-low'
    elif pctl <= 60:
        return 'FAIR', 0, 'pctl-mid'
    elif pctl <= 80:
        return 'EXPENSIVE', -1, 'pctl-high'
    else:
        return 'VERY EXPENSIVE', -2, 'pctl-high'

def get_composite_score(pe_pctl, pb_pctl, div_pctl):
    """Calculate composite score (0-100, lower is cheaper)"""
    # Weight: PE 50%, PB 30%, Div 20% (inverted)
    composite = pe_pctl * 0.50 + pb_pctl * 0.30 + (100 - div_pctl) * 0.20
    return composite

def get_signal_from_composite(score):
    """Get signal from composite score"""
    if score <= 25:
        return 'STRONG BUY', 'signal-buy'
    elif score <= 40:
        return 'BUY', 'signal-buy'
    elif score <= 55:
        return 'ACCUMULATE', 'signal-accumulate'
    elif score <= 70:
        return 'HOLD', 'signal-hold'
    elif score <= 85:
        return 'TRIM', 'signal-trim'
    else:
        return 'REDUCE', 'signal-sell'

# ══════════════════════════════════════════════════════════════════════════════
# CHART FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def create_comparison_chart(data, metric, title):
    """Create comparison line chart for all 3 indices"""
    fig = go.Figure()
    
    colors = {'nifty50': '#3b82f6', 'midcap': '#8b5cf6', 'smallcap': '#10b981'}
    names = {'nifty50': 'Nifty 50', 'midcap': 'Midcap 100', 'smallcap': 'Smallcap 250'}
    
    for key in ['nifty50', 'midcap', 'smallcap']:
        if key in data and metric in data[key].columns:
            df = data[key].dropna(subset=[metric])
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df[metric],
                name=names[key],
                line=dict(color=colors[key], width=2)
            ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='#e2e8f0'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17,24,39,0.8)',
        font=dict(color='#e2e8f0', size=10),
        xaxis=dict(gridcolor='#1e3a5f'),
        yaxis=dict(gridcolor='#1e3a5f'),
        legend=dict(orientation='h', y=1.1, x=0.5, xanchor='center', font=dict(size=10)),
        height=300, margin=dict(l=50, r=20, t=50, b=30),
        hovermode='x unified'
    )
    return fig

def create_percentile_bars(n50_pctl, mid_pctl, small_pctl, title):
    """Create horizontal bar chart for percentile comparison"""
    fig = go.Figure()
    
    indices = ['Smallcap 250', 'Midcap 100', 'Nifty 50']
    values = [small_pctl, mid_pctl, n50_pctl]
    colors = ['#10b981' if v <= 40 else '#ef4444' if v >= 60 else '#f59e0b' for v in values]
    
    fig.add_trace(go.Bar(
        y=indices, x=values,
        orientation='h',
        marker_color=colors,
        text=[f'{v:.0f}%' for v in values],
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=11)
    ))
    
    # Add reference lines
    fig.add_vline(x=30, line_dash="dash", line_color="#10b981", line_width=1)
    fig.add_vline(x=70, line_dash="dash", line_color="#ef4444", line_width=1)
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color='#e2e8f0'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17,24,39,0.8)',
        font=dict(color='#e2e8f0', size=10),
        xaxis=dict(gridcolor='#1e3a5f', range=[0, 100], title='Percentile'),
        yaxis=dict(gridcolor='#1e3a5f'),
        height=200, margin=dict(l=100, r=50, t=40, b=30),
        showlegend=False
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

def main():
    st.markdown('<h1 class="main-title">🇮🇳 INDIA 3-CAP VALUATION DASHBOARD</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">Nifty 50 | Midcap 100 | Smallcap 250 • Analysis from April 2021</p>', unsafe_allow_html=True)
    
    # Load data
    data = load_all_data()
    
    if not data:
        st.error("No data loaded! Please check file locations.")
        return
    
    # Get latest values
    latest = {}
    stats = {}
    
    for key in ['nifty50', 'midcap', 'smallcap']:
        if key in data:
            df = data[key].dropna(subset=['PE'])
            latest[key] = df.iloc[-1]
            stats[key] = {
                'pe_mean': df['PE'].mean(),
                'pe_median': df['PE'].median(),
                'pb_mean': df['PB'].mean(),
                'pb_median': df['PB'].median(),
                'div_mean': df['DivYield'].mean(),
                'div_median': df['DivYield'].median(),
            }
    
    # Calculate composite scores
    composites = {}
    for key in latest:
        l = latest[key]
        composites[key] = get_composite_score(l['PE_Pctl'], l['PB_Pctl'], l['DivYield_Pctl'])
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════════════════════
    # ROW 1: Three Index Cards Side by Side
    # ══════════════════════════════════════════════════════════════════════════
    
    col1, col2, col3 = st.columns(3)
    
    # NIFTY 50
    with col1:
        if 'nifty50' in latest:
            l = latest['nifty50']
            sig, sig_cls = get_signal_from_composite(composites['nifty50'])
            
            st.markdown('<div class="index-header nifty-header">📊 NIFTY 50</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="index-card">', unsafe_allow_html=True)
            
            # PE
            pe_sig, _, pe_cls = get_percentile_signal(l['PE_Pctl'])
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">PE Ratio</span>
                <span><span class="metric-value">{l["PE"]:.2f}</span> <span class="metric-pctl {pe_cls}">{l["PE_Pctl"]:.0f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            # PB
            pb_sig, _, pb_cls = get_percentile_signal(l['PB_Pctl'])
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">PB Ratio</span>
                <span><span class="metric-value">{l["PB"]:.2f}</span> <span class="metric-pctl {pb_cls}">{l["PB_Pctl"]:.0f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            # Div
            div_sig, _, div_cls = get_percentile_signal(l['DivYield_Pctl'], inverted=True)
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">Div Yield</span>
                <span><span class="metric-value">{l["DivYield"]:.2f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            # Signal
            st.markdown(f'<div class="signal-badge {sig_cls}">{sig}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;font-size:0.7rem;color:#64748b;margin-top:0.3rem">Composite: {composites["nifty50"]:.1f}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # MIDCAP 100
    with col2:
        if 'midcap' in latest:
            l = latest['midcap']
            sig, sig_cls = get_signal_from_composite(composites['midcap'])
            
            st.markdown('<div class="index-header midcap-header">📈 MIDCAP 100</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="index-card">', unsafe_allow_html=True)
            
            pe_sig, _, pe_cls = get_percentile_signal(l['PE_Pctl'])
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">PE Ratio</span>
                <span><span class="metric-value">{l["PE"]:.2f}</span> <span class="metric-pctl {pe_cls}">{l["PE_Pctl"]:.0f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            pb_sig, _, pb_cls = get_percentile_signal(l['PB_Pctl'])
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">PB Ratio</span>
                <span><span class="metric-value">{l["PB"]:.2f}</span> <span class="metric-pctl {pb_cls}">{l["PB_Pctl"]:.0f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">Div Yield</span>
                <span><span class="metric-value">{l["DivYield"]:.2f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            st.markdown(f'<div class="signal-badge {sig_cls}">{sig}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;font-size:0.7rem;color:#64748b;margin-top:0.3rem">Composite: {composites["midcap"]:.1f}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # SMALLCAP 250
    with col3:
        if 'smallcap' in latest:
            l = latest['smallcap']
            sig, sig_cls = get_signal_from_composite(composites['smallcap'])
            
            st.markdown('<div class="index-header smallcap-header">🚀 SMALLCAP 250</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="index-card">', unsafe_allow_html=True)
            
            pe_sig, _, pe_cls = get_percentile_signal(l['PE_Pctl'])
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">PE Ratio</span>
                <span><span class="metric-value">{l["PE"]:.2f}</span> <span class="metric-pctl {pe_cls}">{l["PE_Pctl"]:.0f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            pb_sig, _, pb_cls = get_percentile_signal(l['PB_Pctl'])
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">PB Ratio</span>
                <span><span class="metric-value">{l["PB"]:.2f}</span> <span class="metric-pctl {pb_cls}">{l["PB_Pctl"]:.0f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            st.markdown(f'''
            <div class="metric-row">
                <span class="metric-label">Div Yield</span>
                <span><span class="metric-value">{l["DivYield"]:.2f}%</span></span>
            </div>''', unsafe_allow_html=True)
            
            st.markdown(f'<div class="signal-badge {sig_cls}">{sig}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;font-size:0.7rem;color:#64748b;margin-top:0.3rem">Composite: {composites["smallcap"]:.1f}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════════════════════
    # ROW 2: Percentile Comparison Bars
    # ══════════════════════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-header">📊 Percentile Comparison (Lower = Cheaper)</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if all(k in latest for k in ['nifty50', 'midcap', 'smallcap']):
            fig = create_percentile_bars(
                latest['nifty50']['PE_Pctl'],
                latest['midcap']['PE_Pctl'],
                latest['smallcap']['PE_Pctl'],
                'PE Percentile'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if all(k in latest for k in ['nifty50', 'midcap', 'smallcap']):
            fig = create_percentile_bars(
                latest['nifty50']['PB_Pctl'],
                latest['midcap']['PB_Pctl'],
                latest['smallcap']['PB_Pctl'],
                'PB Percentile'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        if all(k in latest for k in ['nifty50', 'midcap', 'smallcap']):
            fig = create_percentile_bars(
                composites['nifty50'],
                composites['midcap'],
                composites['smallcap'],
                'Composite Score'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # ══════════════════════════════════════════════════════════════════════════
    # ROW 3: Premium Analysis
    # ══════════════════════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-header">💰 Premium Analysis (vs Nifty 50)</div>', unsafe_allow_html=True)
    
    if all(k in latest for k in ['nifty50', 'midcap', 'smallcap']):
        n50 = latest['nifty50']
        mid = latest['midcap']
        small = latest['smallcap']
        
        # Current premiums
        mid_pe_prem = mid['PE'] - n50['PE']
        small_pe_prem = small['PE'] - n50['PE']
        mid_pb_prem = mid['PB'] - n50['PB']
        small_pb_prem = small['PB'] - n50['PB']
        
        # Historical avg premiums
        mid_pe_hist = stats['midcap']['pe_mean'] - stats['nifty50']['pe_mean']
        small_pe_hist = stats['smallcap']['pe_mean'] - stats['nifty50']['pe_mean']
        mid_pb_hist = stats['midcap']['pb_mean'] - stats['nifty50']['pb_mean']
        small_pb_hist = stats['smallcap']['pb_mean'] - stats['nifty50']['pb_mean']
        
        st.markdown(f'''
        <table class="comparison-table">
            <tr>
                <th>Premium vs N50</th>
                <th>Midcap PE</th>
                <th>Smallcap PE</th>
                <th>Midcap PB</th>
                <th>Smallcap PB</th>
            </tr>
            <tr>
                <td>Current</td>
                <td class="{'premium-positive' if mid_pe_prem > mid_pe_hist else 'premium-negative'}">{mid_pe_prem:+.2f}</td>
                <td class="{'premium-positive' if small_pe_prem > small_pe_hist else 'premium-negative'}">{small_pe_prem:+.2f}</td>
                <td class="{'premium-positive' if mid_pb_prem > mid_pb_hist else 'premium-negative'}">{mid_pb_prem:+.2f}</td>
                <td class="{'premium-positive' if small_pb_prem > small_pb_hist else 'premium-negative'}">{small_pb_prem:+.2f}</td>
            </tr>
            <tr>
                <td>Hist. Avg</td>
                <td>{mid_pe_hist:+.2f}</td>
                <td>{small_pe_hist:+.2f}</td>
                <td>{mid_pb_hist:+.2f}</td>
                <td>{small_pb_hist:+.2f}</td>
            </tr>
            <tr>
                <td>Deviation</td>
                <td class="{'loser' if mid_pe_prem > mid_pe_hist else 'winner'}">{mid_pe_prem - mid_pe_hist:+.2f}</td>
                <td class="{'loser' if small_pe_prem > small_pe_hist else 'winner'}">{small_pe_prem - small_pe_hist:+.2f}</td>
                <td class="{'loser' if mid_pb_prem > mid_pb_hist else 'winner'}">{mid_pb_prem - mid_pb_hist:+.2f}</td>
                <td class="{'loser' if small_pb_prem > small_pb_hist else 'winner'}">{small_pb_prem - small_pb_hist:+.2f}</td>
            </tr>
        </table>
        ''', unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════════════════════
    # ROW 4: Historical Charts
    # ══════════════════════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-header">📈 Historical Trends (April 2021 - Present)</div>', unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["PE Ratio", "PB Ratio", "Dividend Yield"])
    
    with t1:
        fig = create_comparison_chart(data, 'PE', '📊 PE Ratio Comparison')
        st.plotly_chart(fig, use_container_width=True)
    
    with t2:
        fig = create_comparison_chart(data, 'PB', '📊 PB Ratio Comparison')
        st.plotly_chart(fig, use_container_width=True)
    
    with t3:
        fig = create_comparison_chart(data, 'DivYield', '💰 Dividend Yield Comparison')
        st.plotly_chart(fig, use_container_width=True)
    
    # ══════════════════════════════════════════════════════════════════════════
    # ROW 5: Recommendations
    # ══════════════════════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-header">💡 Allocation Recommendation</div>', unsafe_allow_html=True)
    
    # Find best value
    best_idx = min(composites, key=composites.get)
    best_names = {'nifty50': 'Nifty 50 (Large Cap)', 'midcap': 'Midcap 100', 'smallcap': 'Smallcap 250'}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div class="info-box info-success">
            <strong>🏆 Best Value: {best_names[best_idx]}</strong><br>
            Composite Score: {composites[best_idx]:.1f} (lowest = best)<br>
            Consider overweighting this segment in your portfolio.
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        # Ranking
        ranked = sorted(composites.items(), key=lambda x: x[1])
        st.markdown(f'''
        <div class="info-box info-warning">
            <strong>📊 Valuation Ranking (Best to Worst):</strong><br>
            1. {best_names[ranked[0][0]]} ({ranked[0][1]:.1f})<br>
            2. {best_names[ranked[1][0]]} ({ranked[1][1]:.1f})<br>
            3. {best_names[ranked[2][0]]} ({ranked[2][1]:.1f})
        </div>
        ''', unsafe_allow_html=True)
    
    # Footer
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f'''
    <p style="text-align:center;color:#64748b;font-size:0.75rem">
    🇮🇳 Pro Quant India 3-Cap Dashboard | Analysis Period: April 2021 - Present<br>
    <em>Composite Score = PE Pctl × 50% + PB Pctl × 30% + (100-Div Pctl) × 20%</em>
    </p>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
