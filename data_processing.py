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
    raw_lower = raw_item.lower().strip()
    for a in aliases:
        a_lower = a.lower().strip()
        # Prevent 'ethanol' from falsely matching 'methanol'
        if a_lower == "ethanol" and "methanol" in raw_lower:
            continue
        if a_lower in raw_lower:
            return True
    return False


def _matches_metal_alias(target_name: str, aliases: List[str], raw_item: str) -> bool:
    """Checks if raw_item matches metal aliases with strict disambiguation."""
    raw_lower = raw_item.lower().strip()
    for a in aliases:
        a_lower = a.lower().strip()
        # Strict exact or prefix match for short names
        if a_lower == "tin":
            if raw_lower == "tin" or raw_lower.startswith("tin "):
                return True
            continue
        if a_lower == "lead":
            if raw_lower == "lead" or raw_lower.startswith("lead "):
                return True
            continue
        if a_lower == "zinc":
            if raw_lower == "zinc" or raw_lower.startswith("zinc "):
                return True
            continue
        if a_lower == "nickel":
            if raw_lower == "nickel" or raw_lower.startswith("nickel "):
                return True
            continue
        if a_lower == "copper":
            if raw_lower == "copper" or raw_lower.startswith("copper "):
                return True
            continue
        if a_lower == "urea":
            if raw_lower == "urea" or raw_lower.startswith("urea "):
                return True
            continue
        if a_lower == "tinusd":
            if (raw_lower == "tin" or "tin" in raw_lower) and "platinum" not in raw_lower:
                return True
            continue
        if a_lower in ["aluminum", "aluminium"]:
            if raw_lower in ["aluminum", "aluminium"] or raw_lower.startswith("aluminum ") or raw_lower.startswith("aluminium "):
                return True
            continue
        if a_lower == "aluminum alloy":
            if "aluminum alloy" in raw_lower:
                return True
            continue
        if a_lower in ["di-ammonium", "dap"]:
            if any(k in raw_lower for k in ["di-ammonium", "diammonium", "dap"]):
                return True
            continue
        if a_lower in raw_lower:
            return True
    return False


def parse_all_target_data(html_pages: Union[str, List[str]]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Parses all collected HTML pages.
    Returns:
      tuple: (df_currencies, df_energy_commodities, df_metals_commodities, metadata)
    """
    if isinstance(html_pages, str):
        html_pages = [html_pages]

    matched_currencies: Dict[str, Dict[str, str]] = {}
    matched_commodities: Dict[str, Dict[str, str]] = {}
    matched_metals: Dict[str, Dict[str, str]] = {}
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

            # Check if this is a Commodities table (Energy, Metals, Industrial, Agricultural)
            elif any(k in first_header for k in ["energy", "metal", "industrial", "agricultural", "commodity"]) or any(
                c in str(tbl) for c in ["Crude Oil", "Brent", "Copper", "HRC Steel", "Zinc"]
            ):
                col_indices = {col: _find_column_index(headers, col) for col in config.COMMODITY_COLUMNS}
                if col_indices["Commodity"] == -1:
                    col_indices["Commodity"] = 0

                for row in tbl.find_all("tr"):
                    cells = row.find_all("td")
                    if not cells:
                        continue

                    comm_cell = cells[col_indices["Commodity"]]
                    b_tag = comm_cell.find("b")
                    raw_item = b_tag.get_text(strip=True) if b_tag else comm_cell.get_text(strip=True)

                    # 1. Match against our 7 target Energy commodities
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

                    # 2. Match against our 13 target Metals & Industrial commodities
                    for metal_spec in config.METALS_COMMODITIES:
                        m_name = metal_spec["commodity"]
                        aliases = metal_spec.get("aliases", [m_name])
                        factor = metal_spec.get("factor", 1)

                        if _matches_metal_alias(m_name, aliases, raw_item):
                            row_data = {"Commodity": m_name}
                            for col_name in config.COMMODITY_COLUMNS[1:]:
                                c_idx = col_indices[col_name]
                                if c_idx != -1 and c_idx < len(cells):
                                    raw_cell = _clean_cell_value(cells[c_idx].get_text(strip=True))
                                    if col_name == "Price":
                                        try:
                                            num_p = float(raw_cell.replace(",", ""))
                                            factored_p = num_p * factor
                                            if factor != 1:
                                                row_data["Price"] = f"{factored_p:,.2f}"
                                                logger.info(
                                                    f"Factored {m_name}: {raw_cell} * {factor} -> {factored_p:,.2f}"
                                                )
                                            else:
                                                row_data["Price"] = f"{factored_p:,.2f}" if "." in raw_cell else f"{factored_p:,.0f}"
                                        except Exception:
                                            row_data["Price"] = raw_cell
                                    else:
                                        row_data[col_name] = raw_cell
                                else:
                                    row_data[col_name] = "N/A"

                            matched_metals[m_name] = row_data
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

    # Format Metals & Industrial Commodities DataFrame
    ordered_metal_rows = []
    for metal_spec in config.METALS_COMMODITIES:
        target_metal = metal_spec["commodity"]
        display_item = config.METALS_NAME_MAP.get(target_metal, target_metal)
        table_type = metal_spec.get("table", "Metal")

        if target_metal in matched_metals:
            m_dict = matched_metals[target_metal].copy()
            m_dict["Item"] = display_item
            m_dict["Table"] = table_type
            ordered_metal_rows.append(m_dict)
        else:
            ordered_metal_rows.append({
                "Item": display_item,
                "Table": table_type,
                "Price": "N/A",
                "Weekly": "N/A",
                "Monthly": "N/A",
                "YoY": "N/A"
            })

    df_metals = pd.DataFrame(ordered_metal_rows)[config.METALS_COLUMNS] if ordered_metal_rows else pd.DataFrame(columns=config.METALS_COLUMNS)

    metadata = {
        "timestamp": timestamp_str,
        "currencies_count": len(df_currencies),
        "energy_count": len(df_energy),
        "metals_count": len(df_metals),
        "usdcny_factor": usdcny_rate,
    }

    return df_currencies, df_energy, df_metals, metadata
