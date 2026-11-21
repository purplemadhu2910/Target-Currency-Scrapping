"""
Streamlit Web Dashboard for Live Currency Scraping & Excel Automation.
Run via terminal inside 'wsp':
    streamlit run app.py
"""

from pathlib import Path
import time
from datetime import datetime
import pandas as pd
import openpyxl
import streamlit as st

import config
from scraper import fetch_all_pages_html
from data_processing import parse_target_currencies
from excel_writer import save_or_update_excel

# Page configuration
st.set_page_config(
    page_title="Live Currency Automation Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1F4E79;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_existing_data() -> pd.DataFrame:
    """Loads current data from the Excel file if it exists."""
    target_file = config.EXCEL_FILE
    root_file = config.BASE_DIR / "extracted_data.xlsx"

    file_to_read = None
    if target_file.exists():
        file_to_read = target_file
    elif root_file.exists():
        file_to_read = root_file

    if file_to_read:
        try:
            df = pd.read_excel(file_to_read)
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def run_live_scrape():
    """Triggers the scraper and updates Excel."""
    with st.spinner("Connecting to Trading Economics & extracting live rates via headless Chrome..."):
        html_pages = fetch_all_pages_html()
        if not html_pages:
            st.error("Failed to retrieve live webpage content.")
            return None

        df, metadata = parse_target_currencies(html_pages)
        if df.empty:
            st.error("No target currency pairs were extracted.")
            return None

        save_or_update_excel(df, config.EXCEL_FILE)
        st.success(f"Successfully updated at {metadata.get('timestamp')}!")
        return df


# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/currency-exchange.png", width=64)
    st.title("Control Panel")
    st.write("Automated Currency Scraper & Excel Exporter")
    st.divider()

    st.subheader("Actions")
    scrape_clicked = st.button("🔄 Scrape & Refresh Rates Now", use_container_width=True, type="primary")

    st.divider()
    st.subheader("Automation Settings")
    auto_refresh = st.checkbox("Enable Auto-Refresh", value=False)
    refresh_interval = st.selectbox(
        "Refresh Interval",
        options=[1, 3, 5, 10, 15],
        index=2,
        format_func=lambda x: f"Every {x} Minute(s)",
        disabled=not auto_refresh,
    )

    st.divider()
    st.subheader("Target Pairs Tracked")
    for pair in config.TARGET_PAIRS_DISPLAY:
        st.markdown(f"- **{pair}**")

    st.divider()
    st.caption("Data Source: Trading Economics (Live Forex)")


# --- MAIN DASHBOARD CONTENT ---
st.markdown('<div class="main-header">📈 Live Currency Automation Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Automated extraction for 5 key currency pairs • Dynamic Excel generation</div>',
    unsafe_allow_html=True,
)

# Handle Manual Scrape Click
if scrape_clicked:
    df_current = run_live_scrape()
else:
    df_current = load_existing_data()

# Check if data exists
if df_current.empty:
    st.info("No data found in Excel yet. Click '**Scrape & Refresh Rates Now**' in the sidebar to run the initial extraction.")
else:
    # 1. TOP METRIC CARDS
    st.subheader("Key Exchange Rates (At a Glance)")
    cols = st.columns(len(df_current))

    for idx, (_, row) in enumerate(df_current.iterrows()):
        pair = row.get("Crosses", "N/A")
        price = row.get("Price", "N/A")
        yoy = str(row.get("YoY", "0%"))
        weekly = str(row.get("Weekly", "0%"))

        # Format price cleanly
        try:
            price_val = float(price)
            formatted_price = f"{price_val:,.4f}"
        except (ValueError, TypeError):
            formatted_price = str(price)

        with cols[idx]:
            st.metric(
                label=pair,
                value=formatted_price,
                delta=f"YoY: {yoy} | Wk: {weekly}",
                delta_color="normal",
            )

    st.write("")
    st.divider()

    # 2. TABULAR VIEW & DOWNLOAD
    col_table_header, col_download = st.columns([3, 1])
    with col_table_header:
        st.subheader("Complete Currency Metrics Table")
    with col_download:
        # Download Excel Button
        excel_file_path = config.EXCEL_FILE
        if excel_file_path.exists():
            with open(excel_file_path, "rb") as f:
                st.download_button(
                    label="📥 Download Excel (.xlsx)",
                    data=f.read(),
                    file_name="extracted_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

    # Format dataframe for display
    st.dataframe(
        df_current,
        use_container_width=True,
        hide_index=True,
    )

    # 3. COMPARISON CHART
    st.divider()
    st.subheader("Performance Comparison (% Change)")

    chart_data = []
    for _, row in df_current.iterrows():
        pair = row["Crosses"]
        for metric in ["Weekly", "Monthly", "YoY"]:
            raw_pct = str(row.get(metric, "0%")).replace("%", "").strip()
            try:
                val = float(raw_pct)
                chart_data.append({"Pair": pair, "Period": metric, "Change (%)": val})
            except ValueError:
                pass

    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        pivot_chart = chart_df.pivot(index="Pair", columns="Period", values="Change (%)")
        st.bar_chart(pivot_chart)

    # 4. ACTIVITY LOG VIEWER
    with st.expander("📋 View Recent Scraper Activity Logs"):
        log_file = config.LOG_FILE
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                log_lines = f.readlines()
                recent_logs = "".join(log_lines[-20:])
                st.code(recent_logs, language="text")
        else:
            st.write("No log file found yet.")

# Auto-refresh loop handler
if auto_refresh:
    time.sleep(refresh_interval * 60)
    st.rerun()
