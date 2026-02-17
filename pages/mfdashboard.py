import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta

# --- 1. STRICT 6-CATEGORY LOGIC (IMPROVED) ---
def categorize_fund(fund_name):
    """
    Categorizes ALL funds into exactly 6 buckets.
    Hierarchy is critical here to catch specific types before general ones.
    
    Improvements over original:
    - Catches FoF, REIT, Mining, Clean Energy, Treasury, Climate Change as International
    - Correctly classifies Parag Parikh (Flexi Cap marketed as Large Cap) into Multi Cap
    - Catches Long-Short / Alternative funds into Multi Cap
    - Expanded international keyword list for Hang Seng, FANG, NYSE, etc.
    """
    name = fund_name.lower()

    # 1. INTERNATIONAL FUNDS (Highest Priority)
    intl_keywords = [
        'intl', 'international', 'global', 'overseas', 'world', 'fof',
        'us ', 'u.s.', 'usa', 'america', 'nasdaq', 's&p',
        'china', 'japan', 'europe', 'brazil', 'taiwan', 'hong kong',
        'asia', 'emerging', 'greater china', 'asean', 'deutschland',
        'hang seng', 'fang', 'nyse', 'reit', 'mining', 'clean energy',
        'treasury', 'aqua fof', 'metal and energy equity fof',
        'climate change fof'
    ]
    if any(x in name for x in intl_keywords):
        return 'International Funds'

    # 2. LONG-SHORT / ALTERNATIVE → Multi Cap
    if 'long short' in name or 'long-short' in name:
        return 'Multi Cap'

    # 3. PARAG PARIKH → Multi Cap (it's a Flexi Cap fund, not a true Large Cap)
    if 'parag parikh' in name:
        return 'Multi Cap'

    # 4. LARGE & MID CAP (Specific 'And' Logic)
    if 'large' in name and 'mid' in name:
        return 'Large & Mid Cap'

    # 5. SMALL CAP
    if 'small' in name:
        return 'Small Cap'

    # 6. MID CAP (Must check after Large & Mid to avoid double counting)
    if 'mid' in name:
        return 'Mid Cap'

    # 7. LARGE CAP
    if 'large' in name or 'bluechip' in name or 'top 100' in name or 'frontline' in name or 'nifty' in name or 'sensex' in name:
        return 'Large Cap'

    # 8. MULTI CAP (The Catch-All)
    return 'Multi Cap'


# --- 2. RETURN CALCULATION LOGIC ---
def calculate_returns(df, fund_col, date_col, period_days=None, period_months=None, period_years=None):
    """
    Calculates absolute return % between Latest Date and (Latest Date - Period).
    """
    df = df.sort_values(by=date_col, ascending=False).reset_index(drop=True)

    if df.empty:
        return np.nan

    valid_idx = df[fund_col].first_valid_index()
    if valid_idx is None:
        return np.nan

    latest_row = df.iloc[valid_idx]
    latest_date = latest_row[date_col]
    latest_nav = latest_row[fund_col]

    target_date = latest_date
    if period_days:
        target_date -= timedelta(days=period_days)
    elif period_months:
        target_date -= timedelta(days=30 * period_months)
    elif period_years:
        target_date -= timedelta(days=365 * period_years)
    else:
        return np.nan

    mask = df[date_col] <= target_date
    past_rows = df[mask]

    if past_rows.empty:
        return np.nan

    past_nav = past_rows.iloc[0][fund_col]

    if pd.isna(past_nav) or past_nav == 0:
        return np.nan

    return ((latest_nav - past_nav) / past_nav) * 100


# --- 3. EXCEPTIONAL FUND DETECTION ---
def compute_percentile_rank(value, all_values):
    """
    Returns percentile rank (0-100) of a value within a list.
    100 = best in category.
    """
    valid = [v for v in all_values if not pd.isna(v)]
    if not valid or pd.isna(value):
        return np.nan
    rank = sum(1 for v in valid if v < value)
    return (rank / len(valid)) * 100


def detect_exceptional_funds(df_results):
    """
    For each fund, compute percentile rank within its category for each return period.
    A fund is 'Exceptional' if it ranks in the top 15th percentile (>=85) in 2+ periods.
    
    Returns the enriched dataframe with:
    - Percentile columns for each period
    - 'Exceptional Periods' count
    - 'Is Exceptional' boolean flag
    """
    return_cols = ["1W (%)", "2W (%)", "1M (%)", "3M (%)", "6M (%)", "1Y (%)"]

    # Initialize new columns
    for col in return_cols:
        df_results[f"Pctl_{col}"] = np.nan
    df_results["Exceptional Periods"] = 0
    df_results["Is Exceptional"] = False

    for category in df_results["Category"].unique():
        cat_mask = df_results["Category"] == category
        cat_funds = df_results[cat_mask]

        for col in return_cols:
            all_values = cat_funds[col].tolist()
            for idx in cat_funds.index:
                val = df_results.loc[idx, col]
                pctl = compute_percentile_rank(val, all_values)
                df_results.loc[idx, f"Pctl_{col}"] = pctl

    # Count how many periods each fund is in the top 15%
    for idx in df_results.index:
        exc_count = 0
        for col in return_cols:
            pctl = df_results.loc[idx, f"Pctl_{col}"]
            if not pd.isna(pctl) and pctl >= 85:
                exc_count += 1
        df_results.loc[idx, "Exceptional Periods"] = exc_count
        df_results.loc[idx, "Is Exceptional"] = exc_count >= 2

    return df_results


# --- 4. FILE PROCESSOR ---
import os

# ============================================================
# AUTO-LOAD: Finds alldata.xlsx automatically from the repo.
# Works on Streamlit Cloud (file lives next to this script or
# in the repo root) and locally. No upload needed.
# ============================================================
def find_alldata_file():
    """
    Search for alldata.xlsx in common locations relative to the script
    and the repo root. Returns the first path found, or None.
    """
    possible_paths = [
        # Same directory as this script
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "alldata.xlsx"),
        # Repo root (one level up from pages/)
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "alldata.xlsx"),
        # Repo root (two levels up, e.g. pages/subfolder/)
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "alldata.xlsx"),
        # Current working directory
        os.path.join(os.getcwd(), "alldata.xlsx"),
        # Explicit common Streamlit Cloud mount
        "/mount/src/ss/alldata.xlsx",
        "/mount/src/ss/pages/alldata.xlsx",
    ]
    for p in possible_paths:
        resolved = os.path.abspath(p)
        if os.path.isfile(resolved):
            return resolved
    return None


@st.cache_data
def process_alldata(file_path_or_upload):
    """
    Process alldata.xlsx from either a file path (str) or a Streamlit
    UploadedFile object. Both are supported for flexibility.
    """
    try:
        # Determine if it's a file path or an uploaded file object
        if isinstance(file_path_or_upload, str):
            # It's a file path on disk
            file_path = file_path_or_upload
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=2)
            else:
                df = pd.read_excel(file_path, header=2)
        else:
            # It's a Streamlit UploadedFile
            if file_path_or_upload.name.endswith('.csv'):
                df = pd.read_csv(file_path_or_upload, header=2)
            else:
                df = pd.read_excel(file_path_or_upload, header=2)

        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)

        # Skip sub-header row if present (e.g., "NAV Date", "Adjusted NAV...")
        if isinstance(df.iloc[0]['Date'], str) and 'nav' in str(df.iloc[0]['Date']).lower():
            df = df.iloc[1:]

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        fund_columns = [c for c in df.columns if c != 'Date' and "Unnamed" not in str(c)]

        for col in fund_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        results = []
        for fund in fund_columns:
            cat = categorize_fund(fund)

            row = {
                "Category": cat,
                "Fund Name": fund,
                "1W (%)": calculate_returns(df, fund, 'Date', period_days=7),
                "2W (%)": calculate_returns(df, fund, 'Date', period_days=14),
                "1M (%)": calculate_returns(df, fund, 'Date', period_months=1),
                "3M (%)": calculate_returns(df, fund, 'Date', period_months=3),
                "6M (%)": calculate_returns(df, fund, 'Date', period_months=6),
                "1Y (%)": calculate_returns(df, fund, 'Date', period_years=1)
            }
            results.append(row)

        df_results = pd.DataFrame(results)

        # --- DETECT EXCEPTIONAL FUNDS ---
        df_results = detect_exceptional_funds(df_results)

        return df_results

    except Exception as e:
        st.error(f"Error processing file: {e}")
        return pd.DataFrame()


# --- 5. STYLING HELPERS ---
def color_return(val):
    """Color-code a return value for the dataframe."""
    if pd.isna(val):
        return 'color: #6b7280'
    if val >= 5:
        return 'color: #16a34a; font-weight: 700'
    elif val >= 2:
        return 'color: #22c55e'
    elif val >= 0:
        return 'color: #86efac'
    elif val >= -2:
        return 'color: #fca5a5'
    elif val >= -5:
        return 'color: #f87171'
    else:
        return 'color: #ef4444; font-weight: 700'


def highlight_exceptional_row(row):
    """Highlight entire row if the fund is exceptional."""
    if row.get("Is Exceptional", False):
        return ['background-color: rgba(251, 191, 36, 0.08)'] * len(row)
    return [''] * len(row)


def build_highlight_func(filtered_df, return_cols, pctl_cols):
    """
    Build a row-level style function that highlights cells where the fund
    is in the top 15th percentile. Uses a lookup dict from filtered_df
    so the style function only returns styles matching display_df columns.
    """
    # Pre-build a lookup: index -> {return_col: is_top_percentile}
    pctl_lookup = {}
    for idx in filtered_df.index:
        tops = {}
        for rc, pc in zip(return_cols, pctl_cols):
            pctl = filtered_df.loc[idx, pc]
            tops[rc] = (not pd.isna(pctl)) and pctl >= 85
        pctl_lookup[idx] = tops

    def _highlight_row(row):
        styles = [''] * len(row)
        tops = pctl_lookup.get(row.name, {})
        for rc in return_cols:
            if tops.get(rc, False) and rc in row.index:
                col_idx = row.index.get_loc(rc)
                styles[col_idx] = 'background-color: rgba(251, 191, 36, 0.18); font-weight: 800'
        return styles

    return _highlight_row


# --- 6. DASHBOARD UI ---
st.set_page_config(page_title="Mutual Fund Analytics", layout="wide", page_icon="📈")

# Custom CSS
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp { background-color: #0a0e17; }
    
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #111827, #1a2236);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-card h3 {
        color: #9ca3af;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .metric-card .value {
        font-size: 28px;
        font-weight: 800;
        color: #22d3ee;
    }
    .metric-card .sublabel {
        font-size: 11px;
        color: #6b7280;
        margin-top: 4px;
    }
    
    .exceptional-card {
        background: linear-gradient(135deg, rgba(251,191,36,0.1), rgba(251,191,36,0.03));
        border: 1px solid rgba(251,191,36,0.3);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 8px;
    }
    .exceptional-card .fund-name {
        font-size: 14px;
        font-weight: 700;
        color: #fbbf24;
    }
    .exceptional-card .fund-cat {
        font-size: 11px;
        color: #9ca3af;
    }
    .exceptional-card .fund-returns {
        font-size: 12px;
        color: #e5e7eb;
        margin-top: 6px;
    }
    
    .category-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    
    /* Table header styling */
    .stDataFrame thead th {
        background-color: #111827 !important;
        color: #9ca3af !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
</style>
""", unsafe_allow_html=True)


# --- HEADER ---
st.markdown("""
<div style="display:flex; align-items:center; gap:16px; margin-bottom:8px;">
    <div style="width:48px;height:48px;border-radius:12px;
        background:linear-gradient(135deg,#22d3ee,#0891b2);
        display:flex;align-items:center;justify-content:center;font-size:24px;
        box-shadow:0 0 30px rgba(34,211,238,0.15);">📈</div>
    <div>
        <h1 style="margin:0;font-size:28px;font-weight:800;
            background:linear-gradient(90deg,#f9fafb,#22d3ee);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Mutual Fund Analytics Dashboard</h1>
        <p style="margin:0;color:#6b7280;font-size:13px;font-family:monospace;">
            6 categories • Exceptional performers highlighted • Percentile-ranked</p>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================
# AUTO-LOAD alldata.xlsx FROM REPO
# =============================================
auto_file_path = find_alldata_file()
data_source = None  # Will hold the file path or uploaded file

if auto_file_path:
    data_source = auto_file_path
    st.success(f"✅ Auto-loaded **alldata.xlsx** from repo: `{auto_file_path}`")
else:
    st.warning("⚠️ **alldata.xlsx** not found in the repo. Please upload it manually.")
    uploaded_file = st.file_uploader("Upload **alldata.xlsx**", type=['xlsx', 'csv'])
    if uploaded_file:
        data_source = uploaded_file

if data_source:
    with st.spinner("⏳ Processing, categorizing & detecting exceptional performers..."):
        df_results = process_alldata(data_source)

    if not df_results.empty:
        return_cols = ["1W (%)", "2W (%)", "1M (%)", "3M (%)", "6M (%)", "1Y (%)"]
        pctl_cols = [f"Pctl_{c}" for c in return_cols]
        strict_order = ['Large Cap', 'Large & Mid Cap', 'Mid Cap', 'Small Cap', 'Multi Cap', 'International Funds']

        # =============================================
        # SIDEBAR FILTERS
        # =============================================
        st.sidebar.header("🔍 Filters")

        available_cats = [c for c in strict_order if c in df_results["Category"].unique()]
        selected_cats = st.sidebar.multiselect(
            "Select Categories",
            available_cats,
            default=available_cats
        )

        search_query = st.sidebar.text_input("🔎 Search Fund Name")

        show_exceptional_only = st.sidebar.toggle(
            "⭐ Show Exceptional Funds Only",
            value=False,
            help="Show only funds in the top 15th percentile of their category in 2+ return periods"
        )

        sort_by = st.sidebar.selectbox(
            "Sort By",
            ["1M (%)", "3M (%)", "1W (%)", "2W (%)", "6M (%)", "1Y (%)", "Exceptional Periods"],
            index=0
        )

        # Apply filters
        filtered_df = df_results[df_results["Category"].isin(selected_cats)]
        if search_query:
            filtered_df = filtered_df[filtered_df["Fund Name"].str.contains(search_query, case=False, na=False)]
        if show_exceptional_only:
            filtered_df = filtered_df[filtered_df["Is Exceptional"] == True]

        filtered_df = filtered_df.sort_values(by=sort_by, ascending=False, na_position='last')

        # =============================================
        # CATEGORY OVERVIEW CARDS
        # =============================================
        st.subheader("📊 Category Overview")

        cat_cols = st.columns(len(available_cats))
        for i, cat in enumerate(available_cats):
            cat_data = df_results[df_results["Category"] == cat]
            avg_1m = cat_data["1M (%)"].mean()
            exc_count = cat_data["Is Exceptional"].sum()
            total = len(cat_data)

            avg_display = f"{avg_1m:+.2f}%" if not pd.isna(avg_1m) else "—"
            avg_color = "#22c55e" if avg_1m and avg_1m >= 0 else "#f87171"

            with cat_cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{cat}</h3>
                    <div class="value" style="color:{avg_color}">{avg_display}</div>
                    <div class="sublabel">avg 1M return • {total} funds</div>
                    {"<div style='margin-top:8px;font-size:12px;color:#fbbf24;'>⭐ " + str(int(exc_count)) + " exceptional</div>" if exc_count > 0 else ""}
                </div>
                """, unsafe_allow_html=True)

        # =============================================
        # EXCEPTIONAL PERFORMERS SPOTLIGHT
        # =============================================
        st.markdown("---")
        st.subheader("⭐ Exceptional Performers by Category")
        st.caption(
            "Funds ranked in the **top 15th percentile** of their category peers "
            "in **2 or more time periods** (1W, 2W, 1M, 3M, 6M, 1Y). "
            "These are consistent outperformers, not one-period flukes."
        )

        for cat in strict_order:
            cat_exc = df_results[
                (df_results["Category"] == cat) & (df_results["Is Exceptional"] == True)
            ].sort_values("Exceptional Periods", ascending=False)

            if cat_exc.empty:
                continue

            with st.expander(f"**{cat}** — {len(cat_exc)} exceptional fund{'s' if len(cat_exc) != 1 else ''}", expanded=True):
                for _, fund in cat_exc.iterrows():
                    # Build return badges
                    badges = []
                    for rc, pc in zip(return_cols, pctl_cols):
                        val = fund[rc]
                        pctl = fund[pc]
                        if pd.isna(val):
                            continue
                        is_top = (not pd.isna(pctl)) and pctl >= 85
                        color = "#fbbf24" if is_top else ("#22c55e" if val >= 0 else "#f87171")
                        icon = "🏆" if is_top else ""
                        period_label = rc.replace(" (%)", "")
                        badges.append(
                            f"<span style='display:inline-block;padding:3px 8px;margin:2px;border-radius:6px;"
                            f"background:{'rgba(251,191,36,0.15)' if is_top else 'rgba(255,255,255,0.05)'};"
                            f"color:{color};font-size:11px;font-family:monospace;'>"
                            f"{icon}{period_label}: {val:+.2f}%</span>"
                        )

                    st.markdown(f"""
                    <div class="exceptional-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <span class="fund-name">⭐ {fund['Fund Name']}</span>
                                <span class="fund-cat" style="margin-left:12px;">{cat}</span>
                            </div>
                            <span style="font-size:12px;font-weight:700;color:#fbbf24;
                                background:rgba(251,191,36,0.15);padding:4px 10px;border-radius:8px;">
                                {int(fund['Exceptional Periods'])}/6 periods
                            </span>
                        </div>
                        <div class="fund-returns" style="margin-top:8px;">
                            {''.join(badges)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # =============================================
        # TOP PERFORMERS QUICK VIEW
        # =============================================
        st.markdown("---")
        st.subheader("🏆 Top Performers (Per Period)")

        period_tabs = st.tabs(["1 Week", "2 Weeks", "1 Month", "3 Months", "6 Months", "1 Year"])
        for tab, rc in zip(period_tabs, return_cols):
            with tab:
                period_label = rc.replace(" (%)", "")
                # Top 5 per category for this period
                for cat in strict_order:
                    cat_data = df_results[df_results["Category"] == cat].copy()
                    cat_top = cat_data.nlargest(5, rc, keep='first')
                    if cat_top.empty or cat_top[rc].isna().all():
                        continue

                    top_rows = []
                    for rank, (_, row) in enumerate(cat_top.iterrows(), 1):
                        val = row[rc]
                        pctl = row[f"Pctl_{rc}"]
                        is_top = (not pd.isna(pctl)) and pctl >= 85
                        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
                        exc_flag = " ⭐" if row["Is Exceptional"] else ""
                        top_rows.append({
                            "Rank": medal,
                            "Fund": f"{row['Fund Name']}{exc_flag}",
                            f"{period_label} Return": f"{val:+.2f}%" if not pd.isna(val) else "—",
                            "Top 15%": "🏆" if is_top else "",
                        })

                    if top_rows:
                        st.markdown(f"**{cat}**")
                        st.dataframe(
                            pd.DataFrame(top_rows),
                            use_container_width=True,
                            hide_index=True,
                            height=min(35 + 35 * len(top_rows), 220),
                        )

        # =============================================
        # FULL DETAILED TABLE
        # =============================================
        st.markdown("---")
        st.subheader("📋 Detailed Returns Table")
        st.caption(
            f"Showing **{len(filtered_df)}** funds "
            f"{'(exceptional only)' if show_exceptional_only else ''} "
            f"| Sorted by **{sort_by}** descending "
            f"| 🟡 Gold cells = top 15% in category"
        )

        # Columns to display
        display_cols = ["Category", "Fund Name"] + return_cols + ["Exceptional Periods"]

        # Build styled dataframe
        display_df = filtered_df[display_cols].copy()
        display_df["Exceptional Periods"] = display_df["Exceptional Periods"].astype(int)

        # Add star emoji to exceptional fund names
        exc_mask = filtered_df["Is Exceptional"].values
        display_df.loc[exc_mask, "Fund Name"] = "⭐ " + display_df.loc[exc_mask, "Fund Name"]

        # Style it
        highlight_fn = build_highlight_func(filtered_df, return_cols, pctl_cols)

        styled = (
            display_df.style
            .format({c: "{:+.2f}" for c in return_cols}, na_rep="—")
            .background_gradient(
                cmap="RdYlGn", subset=return_cols,
                vmin=-10, vmax=15
            )
            .apply(highlight_fn, axis=1)
        )

        st.dataframe(
            styled,
            use_container_width=True,
            height=700,
            column_config={
                "Fund Name": st.column_config.TextColumn("Fund Name", width="large"),
                "Category": st.column_config.TextColumn("Category", width="medium"),
                "Exceptional Periods": st.column_config.ProgressColumn(
                    "Score",
                    help="Number of periods (out of 6) where this fund is in the top 15% of its category",
                    min_value=0,
                    max_value=6,
                    format="%d/6",
                ),
            }
        )

        # =============================================
        # CATEGORY-WISE SUMMARY STATISTICS
        # =============================================
        st.markdown("---")
        st.subheader("📈 Category Statistics")

        cat_stats = []
        for cat in strict_order:
            cat_data = df_results[df_results["Category"] == cat]
            if cat_data.empty:
                continue
            row = {"Category": cat, "Funds": len(cat_data)}
            for rc in return_cols:
                period = rc.replace(" (%)", "")
                vals = cat_data[rc].dropna()
                row[f"{period} Avg"] = vals.mean() if len(vals) > 0 else np.nan
                row[f"{period} Best"] = vals.max() if len(vals) > 0 else np.nan
                row[f"{period} Worst"] = vals.min() if len(vals) > 0 else np.nan
            row["Exceptional"] = int(cat_data["Is Exceptional"].sum())
            cat_stats.append(row)

        stats_df = pd.DataFrame(cat_stats)
        avg_cols = [c for c in stats_df.columns if 'Avg' in c]
        best_cols = [c for c in stats_df.columns if 'Best' in c]

        st.dataframe(
            stats_df.style.format(
                {c: "{:+.2f}" for c in avg_cols + best_cols + [c for c in stats_df.columns if 'Worst' in c]},
                na_rep="—"
            ).background_gradient(cmap="RdYlGn", subset=avg_cols, vmin=-5, vmax=10),
            use_container_width=True,
            hide_index=True,
        )

        # =============================================
        # DOWNLOAD
        # =============================================
        st.markdown("---")

        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            csv_full = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Full Analysis (CSV)",
                csv_full,
                "mf_full_analysis.csv",
                "text/csv"
            )

        with col_dl2:
            exc_df = df_results[df_results["Is Exceptional"] == True]
            csv_exc = exc_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⭐ Download Exceptional Funds Only (CSV)",
                csv_exc,
                "mf_exceptional_funds.csv",
                "text/csv"
            )

    else:
        st.error("Could not process data. Ensure file format is correct.")
