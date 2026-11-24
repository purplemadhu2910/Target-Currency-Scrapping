"""
Main Orchestrator Module.
Extracts:
  1. Target Currencies: USD/INR, EUR/INR, JPY/INR, USD/JPY, EUR/USD
  2. Energy Commodities: Crude Oil, Brent, Natural gas, TTF Gas, Ethanol, Methanol (factored by USDCNY), Jet Fuel
Supports:
  - Manual mode: Single run on demand.
  - Periodic mode: Automatic extraction every N minutes.
  - Continuous monitoring mode: Continuous polling with change detection.
  - Daily mode: Runs everyday at set time (e.g. 15:00 / 3:00 PM).
"""

import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from tabulate import tabulate

import config
from scraper import fetch_all_pages_html
from data_processing import parse_all_target_data
from excel_writer import save_or_update_excel


def setup_logging():
    """Configures logging to output to both console and a log file."""
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


logger = logging.getLogger("Main")


def display_terminal_output(
    df_currencies: pd.DataFrame,
    df_energy: pd.DataFrame,
    df_metals: pd.DataFrame,
    metadata: Dict[str, Any],
    mode_name: str
):
    """
    Prints a clean, formatted report directly to the terminal,
    displaying Target Currencies, Energy Commodities, and Metals Commodities.
    """
    separator = "=" * 80
    sub_sep = "-" * 80

    print("\n" + separator)
    print("      LIVE MARKET DATA EXTRACTION REPORT (CURRENCIES, ENERGY & METALS)")
    print(separator)
    print(f"Extraction Timestamp : {metadata.get('timestamp')}")
    print(f"Execution Mode       : {mode_name.capitalize()}")
    print(f"Live USD/CNY Factor  : {metadata.get('usdcny_factor')}")
    print(f"Target Excel Path    : {config.EXCEL_FILE}")
    print(sub_sep)

    # 1. Currencies Table
    print("📈 SECTION 1: TARGET CURRENCY PAIRS (Sheets: Live_Rates & History_Log)")
    if not df_currencies.empty:
        curr_table = tabulate(
            df_currencies,
            headers="keys",
            tablefmt="grid",
            showindex=False,
            stralign="right",
            numalign="right",
        )
        print(curr_table)
    else:
        print("  [!] No currency records extracted.")

    print("\n" + sub_sep)

    # 2. Energy Commodities Table
    print("⚡ SECTION 2: ENERGY COMMODITIES (Sheet: Energy_Commodities)")
    if not df_energy.empty:
        energy_table = tabulate(
            df_energy,
            headers="keys",
            tablefmt="grid",
            showindex=False,
            stralign="right",
            numalign="right",
        )
        print(energy_table)
    else:
        print("  [!] No energy commodities extracted.")

    print("\n" + sub_sep)

    # 3. Metals & Industrial Commodities Table
    print("🏗️ SECTION 3: METALS & INDUSTRIAL COMMODITIES (Sheet: Metals_Commodities)")
    if not df_metals.empty:
        metals_table = tabulate(
            df_metals,
            headers="keys",
            tablefmt="grid",
            showindex=False,
            stralign="right",
            numalign="right",
        )
        print(metals_table)
    else:
        print("  [!] No metals commodities extracted.")

    print(separator + "\n")


def execute_extraction(mode_name: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Executes a single extraction lifecycle:
      1. Fetches rendered HTML across target pages (currencies & commodities).
      2. Parses data into DataFrames.
      3. Displays results in terminal.
      4. Saves/updates Excel workbook across all 4 sheets.
    """
    logger.info(f"Starting extraction cycle (Mode: {mode_name})...")

    # 1. Fetch live HTML pages using single browser session
    html_pages = fetch_all_pages_html()
    if not html_pages:
        logger.error("Extraction aborted: Unable to retrieve rendered HTML from target pages.")
        return None, None, None

    # 2. Parse tables for Currencies + Energy + Metals Commodities
    df_currencies, df_energy, df_metals, metadata = parse_all_target_data(html_pages)
    if df_currencies.empty and df_energy.empty and df_metals.empty:
        logger.warning("No data extracted from target pages.")
        return None, None, None

    # 3. Print tabular results in terminal
    display_terminal_output(df_currencies, df_energy, df_metals, metadata, mode_name)

    # 4. Save to Excel workbook across 4 sheets
    timestamp = metadata.get("timestamp")
    excel_success = save_or_update_excel(df_currencies, df_energy, df_metals, config.EXCEL_FILE, timestamp_str=timestamp)
    if excel_success:
        logger.info(f"[SUCCESS] Excel workbook updated successfully: {config.EXCEL_FILE} (4 sheets)")
    else:
        logger.warning(f"[WARNING] Failed to update Excel workbook at: {config.EXCEL_FILE}")

    return df_currencies, df_energy, df_metals


def run_manual_mode():
    """Runs a single on-demand extraction."""
    logger.info("Executing Manual Mode...")
    df_c, df_e, df_m = execute_extraction(mode_name="Manual")
    if df_c is not None or df_e is not None or df_m is not None:
        logger.info("Manual extraction completed successfully.")
    else:
        logger.error("Manual extraction failed.")


def run_periodic_mode(interval_minutes: int):
    """Runs data extraction at a recurring interval (in minutes)."""
    logger.info(f"Starting Periodic Mode. Will extract every {interval_minutes} minute(s).")
    print(f"[*] Periodic automation started. Press Ctrl+C at any time to stop.\n")

    cycle_count = 1
    try:
        while True:
            logger.info(f"--- Periodic Cycle #{cycle_count} ---")
            execute_extraction(mode_name=f"Periodic (Cycle #{cycle_count})")
            logger.info(f"Cycle #{cycle_count} finished. Sleeping for {interval_minutes} minute(s)...")
            time.sleep(interval_minutes * 60)
            cycle_count += 1
    except KeyboardInterrupt:
        print("\n[*] Periodic automation stopped by user.")
        logger.info("Periodic mode terminated by user.")


def run_continuous_mode(poll_seconds: int):
    """Continuously monitors target assets, captures price updates, and updates Excel."""
    logger.info(f"Starting Continuous Monitoring Mode (Polling every {poll_seconds}s).")
    print(f"[*] Continuous monitoring started. Press Ctrl+C at any time to stop.\n")

    previous_prices: Dict[str, str] = {}
    cycle = 1

    try:
        while True:
            logger.info(f"--- Continuous Polling Cycle #{cycle} ---")
            html_pages = fetch_all_pages_html()
            if html_pages:
                df_c, df_e, df_m, metadata = parse_all_target_data(html_pages)
                current_prices = {}
                if not df_c.empty:
                    current_prices.update(dict(zip(df_c["Crosses"], df_c["Price"])))
                if not df_e.empty:
                    current_prices.update(dict(zip(df_e["Commodity"], df_e["Price"])))
                if not df_m.empty:
                    current_prices.update(dict(zip(df_m["Commodity"], df_m["Price"])))

                changes = []
                for item, current_price in current_prices.items():
                    prev_price = previous_prices.get(item)
                    if prev_price is not None and prev_price != current_price:
                        changes.append(f"{item}: {prev_price} -> {current_price}")

                if not previous_prices:
                    logger.info("Initial baseline captured. Writing to Excel...")
                    display_terminal_output(df_c, df_e, df_m, metadata, mode_name=f"Continuous (Cycle #{cycle})")
                    save_or_update_excel(df_c, df_e, df_m, config.EXCEL_FILE, timestamp_str=metadata.get("timestamp"))
                    previous_prices = current_prices
                elif changes:
                    logger.info(f"Detected {len(changes)} price changes: {', '.join(changes)}")
                    display_terminal_output(df_c, df_e, df_m, metadata, mode_name=f"Continuous (Cycle #{cycle} - UPDATES)")
                    save_or_update_excel(df_c, df_e, df_m, config.EXCEL_FILE, timestamp_str=metadata.get("timestamp"))
                    previous_prices = current_prices
                else:
                    logger.info("No price changes detected among target assets.")
            else:
                logger.warning("Could not fetch pages in continuous cycle.")

            time.sleep(poll_seconds)
            cycle += 1

    except KeyboardInterrupt:
        print("\n[*] Continuous monitoring stopped by user.")
        logger.info("Continuous mode terminated by user.")


def run_daily_mode(target_time_str: str = "15:00"):
    """Runs extraction daily at a specific 24-hour time (e.g., '15:00' for 3:00 PM)."""
    logger.info(f"Starting Daily Scheduled Mode. Scheduled for: {target_time_str} everyday.")
    print(f"[*] Daily automation active. Scheduled to run at {target_time_str} everyday.")
    print(f"[*] Press Ctrl+C at any time to stop.\n")

    try:
        target_hour, target_minute = map(int, target_time_str.split(":"))
    except Exception:
        logger.error(f"Invalid time format '{target_time_str}'. Please use HH:MM (e.g. 15:00).")
        return

    try:
        while True:
            now = datetime.now()
            target_today = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

            if now >= target_today:
                next_run = target_today + timedelta(days=1)
            else:
                next_run = target_today

            seconds_to_wait = (next_run - now).total_seconds()
            hours_to_wait = seconds_to_wait / 3600
            logger.info(f"Next scheduled extraction: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {hours_to_wait:.2f} hours).")

            time.sleep(seconds_to_wait)

            logger.info(f"Scheduled time reached ({target_time_str})! Triggering daily extraction...")
            execute_extraction(mode_name=f"Daily ({target_time_str})")
            time.sleep(120)

    except KeyboardInterrupt:
        print("\n[*] Daily schedule stopped by user.")
        logger.info("Daily schedule terminated by user.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Live Market Data Extraction (Currencies & Energy Commodities)"
    )
    parser.add_argument(
        "--mode",
        choices=["manual", "periodic", "continuous", "daily"],
        default="manual",
        help="Execution mode: manual, periodic, continuous, or daily",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=config.DEFAULT_PERIODIC_INTERVAL_MIN,
        help=f"Interval in minutes for periodic mode (default: {config.DEFAULT_PERIODIC_INTERVAL_MIN})",
    )
    parser.add_argument(
        "--poll",
        type=int,
        default=config.DEFAULT_CONTINUOUS_POLL_SEC,
        help=f"Polling delay in seconds for continuous mode (default: {config.DEFAULT_CONTINUOUS_POLL_SEC})",
    )
    parser.add_argument(
        "--time",
        type=str,
        default="15:00",
        help="Daily execution time in 24-hr format HH:MM (default: 15:00 for 3:00 PM)",
    )

    args = parser.parse_args()

    setup_logging()

    if args.mode == "manual":
        run_manual_mode()
    elif args.mode == "periodic":
        run_periodic_mode(args.interval)
    elif args.mode == "continuous":
        run_continuous_mode(args.poll)
    elif args.mode == "daily":
        run_daily_mode(args.time)


if __name__ == "__main__":
    main()
