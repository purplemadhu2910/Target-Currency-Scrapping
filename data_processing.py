"""
Data Processing Module.
Parses the rendered HTML pages for:
  1. 5 Target Currency Pairs: USD/INR, EUR/INR, JPY/INR, USD/JPY, EUR/USD
     (Rule: If Price < 1, multiplied by 100).
  2. 7 Target Energy Commodities: Crude Oil, Brent, Natural gas, TTF Gas, Ethanol, Methanol, Jet Fuel
     (Rule: Methanol price is in CNY and factored by live USD/CNY rate).
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any, Union
from bs4 import BeautifulSoup
import pandas as pd

import config

logger = logging.getLogger("DataProcessor")


def _find_column_index(headers: List[str], target_field: str) -> int:
    """Finds the 0-based column index matching target_field using alias lists."""
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
    """Normalizes a ticker string (e.g. 'EURUSD', 'EUR/USD')."""
    clean = raw_ticker.replace("/", "").replace(":", "").replace(" ", "").upper()
    for unslashed_key, display_name in config.TARGET_PAIRS_MAP.items():
        if clean.startswith(unslashed_key):
            return unslashed_key, display_name
    return "", ""


def _process_currency_price(raw_val: str, display_name: str) -> str:
    """If Price < 1, multiplies by 100 (e.g. JPY/INR)."""
    try:
        clean_str = raw_val.replace(",", "").strip()
        price_num = float(clean_str)
        if price_num < 1.0:
            price_num = price_num * 100.0
            logger.info(f"Price for {display_name} is < 1; multiplied by 100 -> {price_num:.4f}")
        return f"{price_num:.4f}"
    except (ValueError, TypeError):
        return _clean_cell_value(raw_val)


def _matches_commodity_alias(target_name: str, aliases: List[str], raw_item: str) -> bool:
    """Checks if raw_item matches commodity aliases avoiding partial overlap (e.g. ethanol vs methanol)."""
    raw_lower = raw_item.lower()
    for a in aliases:
        a_lower = a.lower()
        # Prevent 'ethanol' from falsely matching 'methanol'
        if a_lower == "ethanol" and "methanol" in raw_lower:
            continue
        if a_lower in raw_lower:
            return True
    return False


def parse_all_target_data(html_pages: Union[str, List[str]]) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Parses all collected HTML pages.
    Returns:
      tuple: (df_currencies, df_energy_commodities, metadata)
    """
    if isinstance(html_pages, str):
        html_pages = [html_pages]

    matched_currencies: Dict[str, Dict[str, str]] = {}
    matched_commodities: Dict[str, Dict[str, str]] = {}
    usdcny_rate = 7.24  # Standard default fallback rate
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Step 1: Scan for currencies, live USDCNY rate, and commodities
    for html in html_pages:
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        for tbl in tables:
            th_tags = tbl.find_all("th")
            if not th_tags and tbl.find("tr"):
                th_tags = tbl.find("tr").find_all(["th", "td"])

            headers = [th.get_text(strip=True) for th in th_tags]
            if not headers:
                continue

            first_header = headers[0].lower()

            # Check if this is a Currency table
            if any(k in first_header for k in ["major", "europe", "america", "asia", "oceania", "africa", "currency", "crosses"]):
                col_indices = {col: _find_column_index(headers, col) for col in config.REQUIRED_COLUMNS}
                if col_indices["Crosses"] == -1:
                    col_indices["Crosses"] = 0

                for row in tbl.find_all("tr"):
                    cells = row.find_all("td")
                    if not cells:
                        continue

                    raw_cross = cells[col_indices["Crosses"]].get_text(strip=True)

                    # Check for USDCNY rate to factor Methanol
                    if "USDCNY" in raw_cross.replace("/", "").upper():
                        try:
                            raw_p = cells[col_indices["Price"]].get_text(strip=True).replace(",", "")
                            usdcny_rate = float(raw_p)
                            logger.info(f"Captured live USDCNY exchange rate: {usdcny_rate}")
                        except Exception:
                            pass

                    # Check for our 5 target currency pairs
                    unslashed_key, display_name = _normalize_ticker(raw_cross)
                    if unslashed_key:
                        row_data = {"Crosses": display_name}
                        for col_name in config.REQUIRED_COLUMNS[1:]:
                            c_idx = col_indices[col_name]
                            if c_idx != -1 and c_idx < len(cells):
                                raw_val = cells[c_idx].get_text(strip=True)
                                if col_name == "Price":
                                    row_data["Price"] = _process_currency_price(raw_val, display_name)
                                else:
                                    row_data[col_name] = _clean_cell_value(raw_val)
                            else:
                                row_data[col_name] = "N/A"

                        matched_currencies[unslashed_key] = row_data

            # Check if this is the Energy Commodities table
            elif "energy" in first_header or any(c in str(tbl) for c in ["Crude Oil", "Brent", "Natural gas"]):
                col_indices = {col: _find_column_index(headers, col) for col in config.COMMODITY_COLUMNS}
                if col_indices["Commodity"] == -1:
                    col_indices["Commodity"] = 0

                for row in tbl.find_all("tr"):
                    cells = row.find_all("td")
                    if not cells:
                        continue

                    raw_item = cells[col_indices["Commodity"]].get_text(strip=True)

                    # Match against our 7 target commodities (specifically check Methanol before Ethanol)
                    for target_name in ["Methanol", "Ethanol", "Crude Oil", "Brent", "Natural gas", "TTF Gas", "Jet Fuel"]:
                        aliases = config.TARGET_COMMODITIES.get(target_name, [])
                        if _matches_commodity_alias(target_name, aliases, raw_item):
                            row_data = {"Commodity": target_name}
                            for col_name in config.COMMODITY_COLUMNS[1:]:
                                c_idx = col_indices[col_name]
                                if c_idx != -1 and c_idx < len(cells):
                                    row_data[col_name] = _clean_cell_value(cells[c_idx].get_text(strip=True))
                                else:
                                    row_data[col_name] = "N/A"

                            matched_commodities[target_name] = row_data
                            break

    # Format Currencies DataFrame
    ordered_curr_rows = []
    for display_pair in config.TARGET_PAIRS_DISPLAY:
        unslashed = display_pair.replace("/", "")
        if unslashed in matched_currencies:
            ordered_curr_rows.append(matched_currencies[unslashed])

    df_currencies = pd.DataFrame(ordered_curr_rows)[config.REQUIRED_COLUMNS] if ordered_curr_rows else pd.DataFrame(columns=config.REQUIRED_COLUMNS)

    # Format Energy Commodities DataFrame
    ordered_comm_rows = []
    for target_comm in config.TARGET_COMMODITIES.keys():
        if target_comm in matched_commodities:
            row_dict = matched_commodities[target_comm].copy()

            # Apply Methanol USDCNY factor rule
            if target_comm == "Methanol":
                try:
                    raw_cny_price = float(row_dict["Price"].replace(",", ""))
                    factored_usd = raw_cny_price / usdcny_rate
                    row_dict["Price"] = f"{factored_usd:.2f}"
                    logger.info(
                        f"Factored Methanol price: {raw_cny_price} CNY / {usdcny_rate} USDCNY -> {factored_usd:.2f} USD/T"
                    )
                except Exception as e:
                    logger.warning(f"Could not factor Methanol price: {e}")

            ordered_comm_rows.append(row_dict)
        else:
            ordered_comm_rows.append({
                "Commodity": target_comm,
                "Price": "N/A (Not on TE Energy table)",
                "Weekly": "N/A",
                "Monthly": "N/A",
                "YoY": "N/A"
            })

    df_energy = pd.DataFrame(ordered_comm_rows)[config.COMMODITY_COLUMNS] if ordered_comm_rows else pd.DataFrame(columns=config.COMMODITY_COLUMNS)

    metadata = {
        "timestamp": timestamp_str,
        "currencies_count": len(df_currencies),
        "energy_count": len(df_energy),
        "usdcny_factor": usdcny_rate,
    }

    return df_currencies, df_energy, metadata
