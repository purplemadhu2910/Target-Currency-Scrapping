"""
Data Processing Module.
Parses the rendered HTML pages, extracts the 5 required columns (Crosses, Price, Weekly, Monthly, YoY),
and filters specifically for the 5 target currency pairs:
USD/INR, EUR/INR, JPY/INR, USD/JPY, EUR/USD.

Rule: If Price < 1, it is multiplied by 100 (e.g. JPY/INR 0.5835 -> 58.35).
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any, Union
from bs4 import BeautifulSoup
import pandas as pd

import config

logger = logging.getLogger("DataProcessor")


def _find_column_index(headers: List[str], target_field: str) -> int:
    """
    Finds the 0-based column index matching target_field using alias lists.
    Returns -1 if not found.
    """
    aliases = [a.lower() for a in config.COLUMN_ALIASES.get(target_field, [target_field])]
    for idx, header in enumerate(headers):
        header_clean = header.strip().lower()
        for alias in aliases:
            if alias in header_clean or header_clean in alias:
                return idx
    return -1


def _clean_cell_value(val: str) -> str:
    """Cleans cell text by removing extra spaces and newlines."""
    if not val:
        return "N/A"
    clean = " ".join(val.split()).strip()
    return clean if clean else "N/A"


def _normalize_ticker(raw_ticker: str) -> Tuple[str, str]:
    """
    Normalizes a ticker string (e.g. 'EURUSD', 'EUR/USD', 'EURUSD:CUR').
    Returns a tuple of (clean_unslashed, display_slashed) if it matches target pairs,
    or ('', '') if it does not match.
    """
    clean = raw_ticker.replace("/", "").replace(":", "").replace(" ", "").upper()
    for unslashed_key, display_name in config.TARGET_PAIRS_MAP.items():
        if clean.startswith(unslashed_key):
            return unslashed_key, display_name
    return "", ""


def _process_price(raw_val: str, display_name: str) -> str:
    """
    Cleans the Price value.
    If the numeric price is less than 1, multiplies it by 100.
    """
    try:
        clean_str = raw_val.replace(",", "").strip()
        price_num = float(clean_str)
        if price_num < 1.0:
            old_val = price_num
            price_num = price_num * 100.0
            logger.info(f"Price for {display_name} is < 1 ({old_val}); multiplied by 100 -> {price_num:.4f}")
        return f"{price_num:.4f}"
    except (ValueError, TypeError):
        return _clean_cell_value(raw_val)


def parse_target_currencies(html_pages: Union[str, List[str]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Parses one or multiple HTML pages, locates the tables, and filters strictly
    for the five target pairs: USD/INR, EUR/INR, JPY/INR, USD/JPY, EUR/USD.
    Extracts the 5 columns: Crosses, Price, Weekly, Monthly, YoY.
    Applies the rule: If Price < 1, multiply by 100.

    Returns:
        tuple: (pd.DataFrame with 5 columns for the 5 pairs, dict containing extraction metadata)
    """
    if isinstance(html_pages, str):
        html_pages = [html_pages]

    matched_records: Dict[str, Dict[str, str]] = {}
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for page_idx, html in enumerate(html_pages, start=1):
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        for tbl in tables:
            th_tags = tbl.find_all("th")
            if not th_tags:
                first_tr = tbl.find("tr")
                if first_tr:
                    th_tags = first_tr.find_all(["th", "td"])

            headers = [th.get_text(strip=True) for th in th_tags]
            if not headers:
                continue

            # Map the required columns dynamically
            col_indices = {}
            for col_name in config.REQUIRED_COLUMNS:
                col_indices[col_name] = _find_column_index(headers, col_name)

            # First column is always Crosses / Symbol
            if col_indices["Crosses"] == -1 and len(headers) > 0:
                col_indices["Crosses"] = 0

            # Ensure essential columns exist
            if col_indices["Crosses"] == -1 or col_indices["Price"] == -1:
                continue

            for row in tbl.find_all("tr"):
                cells = row.find_all("td")
                if not cells:
                    continue

                raw_cross = cells[col_indices["Crosses"]].get_text(strip=True)
                unslashed_key, display_name = _normalize_ticker(raw_cross)

                # Only process if it is one of the requested 5 target pairs
                if unslashed_key:
                    row_data = {}
                    row_data["Crosses"] = display_name

                    for col_name in config.REQUIRED_COLUMNS[1:]:  # Price, Weekly, Monthly, YoY
                        c_idx = col_indices[col_name]
                        if c_idx != -1 and c_idx < len(cells):
                            raw_val = cells[c_idx].get_text(strip=True)
                            if col_name == "Price":
                                row_data["Price"] = _process_price(raw_val, display_name)
                            else:
                                row_data[col_name] = _clean_cell_value(raw_val)
                        else:
                            row_data[col_name] = "N/A"

                    # Store or update latest quote
                    matched_records[unslashed_key] = row_data
                    logger.debug(f"Captured target pair: {display_name} -> {row_data}")

    # Build DataFrame in the exact order requested by user
    ordered_rows = []
    found_targets = []
    missing_targets = []

    for display_pair in config.TARGET_PAIRS_DISPLAY:
        unslashed = display_pair.replace("/", "")
        if unslashed in matched_records:
            ordered_rows.append(matched_records[unslashed])
            found_targets.append(display_pair)
        else:
            missing_targets.append(display_pair)

    if ordered_rows:
        df = pd.DataFrame(ordered_rows)[config.REQUIRED_COLUMNS]
    else:
        df = pd.DataFrame(columns=config.REQUIRED_COLUMNS)

    metadata = {
        "timestamp": timestamp_str,
        "total_records": len(df),
        "found_pairs": found_targets,
        "missing_pairs": missing_targets,
    }

    logger.info(
        f"Target extraction completed: {len(found_targets)}/{len(config.TARGET_PAIRS_DISPLAY)} "
        f"pairs found ({', '.join(found_targets)})."
    )
    if missing_targets:
        logger.warning(f"Pairs not found in current cycle: {', '.join(missing_targets)}")

    return df, metadata
