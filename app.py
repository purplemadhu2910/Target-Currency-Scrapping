"""
Streamlit Web Dashboard for Live Currency & Energy Commodities Automation.
Run via terminal inside 'wsp':
    python -m streamlit run app.py
"""

from pathlib import Path
import time
from datetime import datetime
import pandas as pd
import openpyxl
import streamlit as st

import config
from scraper import fetch_all_pages_html
from data_processing import parse_all_target_data
from excel_writer import save_or_update_excel

# Page configuration
st.set_page_config(
    page_title="Live Market Automation Dashboard",
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
    </style>
    """,
    unsafe_allow_html=True,
)


def _get_target_excel_file():
    target_file = config.EXCEL_FILE
    root_file = config.BASE_DIR / "extracted_data.xlsx"
    if target_file.exists():
        return target_file
    elif root_file.exists():
        return root_file
    return None


def load_live_currencies() -> pd.DataFrame:
    """Loads current live currency data from Live_Rates sheet."""
    f = _get_target_excel_file()
    if f:
        try:
            return pd.read_excel(f, sheet_name=config.EXCEL_SHEET_LIVE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def load_history_currencies() -> pd.DataFrame:
    """Loads all historical currency runs from History_Log sheet."""
    f = _get_target_excel_file()
    if f:
        try:
            return pd.read_excel(f, sheet_name=config.EXCEL_SHEET_HISTORY)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def load_energy_commodities() -> pd.DataFrame:
    """Loads energy commodities from Energy_Commodities sheet."""
    f = _get_target_excel_file()
    if f:
        try:
            return pd.read_excel(f, sheet_name=config.EXCEL_SHEET_ENERGY)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def load_metals_commodities() -> pd.DataFrame:
    """Loads metals & industrial commodities from Metals_Commodities sheet."""
    f = _get_target_excel_file()
    if f:
        try:
            return pd.read_excel(f, sheet_name=config.EXCEL_SHEET_METALS)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def run_live_scrape():
    """Triggers the scraper for currencies, energy & metals and updates Excel."""
    with st.spinner("Connecting to Trading Economics & extracting live Currencies, Energy and Metals..."):
        html_pages = fetch_all_pages_html()
        if not html_pages:
            st.error("Failed to retrieve live webpage content.")
            return None, None, None

        df_c, df_e, df_m, metadata = parse_all_target_data(html_pages)
        timestamp = metadata.get("timestamp")
        save_or_update_excel(df_c, df_e, df_m, config.EXCEL_FILE, timestamp_str=timestamp)
        st.success(f"Successfully updated all 4 sheets at {timestamp}!")
        return df_c, df_e, df_m


# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/currency-exchange.png", width=64)
    st.title("Control Panel")
    st.write("Live Market Scraper & Excel Automation")
    st.divider()

    st.subheader("Actions")
    scrape_clicked = st.button("🔄 Scrape & Refresh All Data Now", use_container_width=True, type="primary")

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
    st.subheader("Target Assets")
    st.markdown("**Currencies:** USD/INR, EUR/INR, JPY/INR, USD/JPY, EUR/USD")
    st.markdown("**Energy:** Crude Oil, Brent, Natural gas, TTF Gas, Ethanol, Methanol, Jet Fuel")
    st.markdown("**Metals:** HRC Steel, Copper, Aluminum Alloy, TinUSD, Zinc, Nickel, Platinum, Palladium, Rhodium, Lead, Lithium, Urea, Di-ammonium")

    st.divider()
    st.caption("Data Source: Trading Economics (Live Forex & Commodities)")


# --- MAIN DASHBOARD CONTENT ---
st.markdown('<div class="main-header">📈 Live Market Automation Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Live Currencies (Forex) • Energy Commodities • Metals & Industrial • 4-Sheet Excel Automation</div>',
    unsafe_allow_html=True,
)

if scrape_clicked:
    df_curr, df_energy, df_metals = run_live_scrape()
else:
    df_curr = load_live_currencies()
    df_energy = load_energy_commodities()
    df_metals = load_metals_commodities()

df_history = load_history_currencies()

# Top Metric Cards (Currencies + Key Energy + Key Metals)
if not df_curr.empty or not df_energy.empty or not df_metals.empty:
    st.subheader("Market Highlights (At a Glance)")
    metric_cols = st.columns(5)

    # Show top 2 currencies + Crude Oil + Copper + Lithium
    highlight_items = []
    if not df_curr.empty:
        for _, r in df_curr.head(2).iterrows():
            highlight_items.append((r["Crosses"], r["Price"], r["YoY"], r["Weekly"]))
    if not df_energy.empty:
        for _, r in df_energy.iterrows():
            if r["Commodity"] in ["Crude Oil"]:
                highlight_items.append((r["Commodity"], r["Price"], r["YoY"], r["Weekly"]))
    if not df_metals.empty:
        for _, r in df_metals.iterrows():
            if any(k in str(r.get("Item", "")) for k in ["Copper", "Lithium"]):
                highlight_items.append((r["Item"], r["Price"], r["YoY"], r["Weekly"]))

    for idx, item in enumerate(highlight_items[:5]):
        with metric_cols[idx]:
            try:
                p_val = float(str(item[1]).replace(",", ""))
                f_p = f"{p_val:,.2f}"
            except Exception:
                f_p = str(item[1])
            st.metric(
                label=item[0],
                value=f_p,
                delta=f"YoY: {item[2]} | Wk: {item[3]}",
                delta_color="normal",
            )

    st.write("")
    st.divider()

    # 4 TABS: LIVE CURRENCIES, ENERGY COMMODITIES, METALS COMMODITIES, HISTORICAL LOG
    tab_curr, tab_energy, tab_metals, tab_hist = st.tabs([
        "💱 Live Currencies (Sheet 1)",
        "⚡ Energy Commodities (Sheet 3)",
        "🏗️ Metals Commodities (Sheet 4)",
        "📜 Currency History Log (Sheet 2)"
    ])

    # TAB 1: CURRENCIES
    with tab_curr:
        col_th, col_dl = st.columns([3, 1])
        with col_th:
            st.subheader("Target Currency Exchange Rates")
        with col_dl:
            if config.EXCEL_FILE.exists():
                with open(config.EXCEL_FILE, "rb") as f:
                    st.download_button(
                        label="📥 Download Excel (.xlsx)",
                        data=f.read(),
                        file_name="extracted_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="dl_curr"
                    )

        st.dataframe(df_curr, use_container_width=True, hide_index=True)

    # TAB 2: ENERGY COMMODITIES
    with tab_energy:
        st.subheader("Target Energy Commodities")
        st.caption("Methanol price is factored by live USD/CNY rate. TTF Gas corresponds to European Natural Gas. Jet Fuel is extracted from IATA Fuel Price Monitor.")
        st.dataframe(df_energy, use_container_width=True, hide_index=True)

    # TAB 3: METALS COMMODITIES
    with tab_metals:
        st.subheader("Target Metals & Industrial Commodities")
        st.caption("Copper price is factored by 2204.62 (converted to USD/Metric Ton). All other commodities factored per specification.")
        st.dataframe(df_metals, use_container_width=True, hide_index=True)

    # TAB 4: HISTORY LOG
    with tab_hist:
        st.subheader("Historical Log of Currency Extractions")
        if not df_history.empty:
            st.caption(f"Total historical records: {len(df_history)}")
            st.dataframe(df_history, use_container_width=True, hide_index=True)
        else:
            st.info("No historical records logged yet.")

    # Log Viewer
    with st.expander("📋 View Recent Scraper Activity Logs"):
        if config.LOG_FILE.exists():
            with open(config.LOG_FILE, "r", encoding="utf-8") as f:
                recent_logs = "".join(f.readlines()[-20:])
                st.code(recent_logs, language="text")

# Auto-refresh loop
if auto_refresh:
    time.sleep(refresh_interval * 60)
    st.rerun()
