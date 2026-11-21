"""
Main Orchestrator Module.
Provides the Command Line Interface (CLI) for running the target currency scraper:
Extracts exclusively: USD/INR, EUR/INR, JPY/INR, USD/JPY, EUR/USD.
Supports:
  1. Manual mode: Single run on demand.
  2. Periodic mode: Automatic extraction every N minutes.
  3. Continuous monitoring mode: Continuous polling with change detection.
"""

import sys
import time
import argparse
import logging
from typing import Optional, Dict, Any
import pandas as pd
from tabulate import tabulate

import config
from scraper import fetch_all_pages_html
from data_processing import parse_target_currencies
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


def display_terminal_output(df: pd.DataFrame, metadata: Dict[str, Any], mode_name: str):
    """
    Prints a clean, formatted report directly to the terminal,
    displaying the 5 target currency pairs and execution metadata.
    """
    separator = "=" * 80
    sub_sep = "-" * 80

    print("\n" + separator)
    print("          TARGET CURRENCY EXTRACTION REPORT - TRADING ECONOMICS")
    print(separator)
    print(f"Extraction Timestamp : {metadata.get('timestamp')}")
    print(f"Execution Mode       : {mode_name.capitalize()}")
    print(f"Target Pairs Found   : {len(df)} / {len(config.TARGET_PAIRS_DISPLAY)}")
    print(f"Target Excel Path    : {config.EXCEL_FILE}")
    print(sub_sep)

    found_list = metadata.get("found_pairs", [])
    missing_list = metadata.get("missing_pairs", [])
    print(f"Pairs Captured : {', '.join(found_list) if found_list else 'None'}")
    if missing_list:
        print(f"Pairs Missing  : {', '.join(missing_list)}")
    print(sub_sep)

    if not df.empty:
        table_str = tabulate(
            df,
            headers="keys",
            tablefmt="grid",
            showindex=False,
            stralign="right",
            numalign="right",
        )
        print(table_str)
    else:
        print("  [!] None of the target currency records were extracted.")

    print(separator + "\n")


def execute_extraction(mode_name: str) -> Optional[pd.DataFrame]:
    """
    Executes a single extraction lifecycle:
      1. Fetches rendered HTML across target pages.
      2. Parses data into a DataFrame with 6 columns for the 5 target pairs.
      3. Displays results in terminal.
      4. Saves/updates Excel workbook.

    Returns:
        pd.DataFrame or None: The extracted DataFrame if successful.
    """
    logger.info(f"Starting target extraction cycle (Mode: {mode_name})...")

    # 1. Fetch live HTML pages using single browser session
    html_pages = fetch_all_pages_html()
    if not html_pages:
        logger.error("Extraction aborted: Unable to retrieve rendered HTML from target pages.")
        return None

    # 2. Parse tables and filter for target 5 pairs
    df, metadata = parse_target_currencies(html_pages)
    if df.empty:
        logger.warning("No target currency pairs were found on the pages.")
        return None

    # 3. Print tabular results in terminal
    display_terminal_output(df, metadata, mode_name)

    # 4. Save to Excel workbook
    excel_success = save_or_update_excel(df, config.EXCEL_FILE)
    if excel_success:
        logger.info(f"[SUCCESS] Excel workbook updated successfully: {config.EXCEL_FILE}")
    else:
        logger.warning(f"[WARNING] Failed to update Excel workbook at: {config.EXCEL_FILE}")

    return df


def run_manual_mode():
    """Runs a single on-demand extraction."""
    logger.info("Executing Manual Mode...")
    df = execute_extraction(mode_name="Manual")
    if df is not None:
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
    """
    Continuously monitors the 5 target pairs, captures price updates,
    and updates the Excel workbook when prices change.
    """
    logger.info(f"Starting Continuous Monitoring Mode (Polling every {poll_seconds}s).")
    print(f"[*] Continuous monitoring started. Press Ctrl+C at any time to stop.\n")

    previous_prices: Dict[str, str] = {}
    cycle = 1

    try:
        while True:
            logger.info(f"--- Continuous Polling Cycle #{cycle} ---")
            html_pages = fetch_all_pages_html()
            if html_pages:
                df, metadata = parse_target_currencies(html_pages)
                if not df.empty:
                    current_prices = dict(zip(df["Crosses"], df["Price"]))
                    changes = []

                    for cross, current_price in current_prices.items():
                        prev_price = previous_prices.get(cross)
                        if prev_price is not None and prev_price != current_price:
                            changes.append(f"{cross}: {prev_price} -> {current_price}")

                    if not previous_prices:
                        # Initial baseline
                        logger.info("Initial baseline captured for target pairs. Writing to Excel...")
                        display_terminal_output(df, metadata, mode_name=f"Continuous (Cycle #{cycle})")
                        save_or_update_excel(df, config.EXCEL_FILE)
                        previous_prices = current_prices
                    elif changes:
                        # Updates detected
                        logger.info(f"Detected {len(changes)} price changes: {', '.join(changes)}")
                        display_terminal_output(df, metadata, mode_name=f"Continuous (Cycle #{cycle} - UPDATES)")
                        save_or_update_excel(df, config.EXCEL_FILE)
                        previous_prices = current_prices
                    else:
                        logger.info("No price changes detected among target pairs.")
            else:
                logger.warning("Could not fetch pages in continuous cycle.")

            time.sleep(poll_seconds)
            cycle += 1

    except KeyboardInterrupt:
        print("\n[*] Continuous monitoring stopped by user.")
        logger.info("Continuous mode terminated by user.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Target Currency Data Extraction & Excel Automation System"
    )
    parser.add_argument(
        "--mode",
        choices=["manual", "periodic", "continuous"],
        default="manual",
        help="Execution mode: manual (single run), periodic (every N minutes), or continuous (change monitoring)",
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

    args = parser.parse_args()

    setup_logging()

    if args.mode == "manual":
        run_manual_mode()
    elif args.mode == "periodic":
        run_periodic_mode(args.interval)
    elif args.mode == "continuous":
        run_continuous_mode(args.poll)


if __name__ == "__main__":
    main()
