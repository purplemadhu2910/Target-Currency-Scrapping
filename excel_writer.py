"""
Excel Automation Module using OpenPyXL.
Handles saving extracted data to 'output/extracted_data.xlsx'
and 'extracted_data.xlsx' across THREE dedicated worksheets:
  1. 'Live_Rates': Latest live currency rates snapshot (5 rows).
  2. 'History_Log': Historical log of currency extractions with timestamps.
  3. 'Energy_Commodities': Energy commodities (Crude Oil, Brent, Natural gas, TTF Gas, Ethanol, Methanol, Jet Fuel).

Rules:
  - Currencies: If Price < 1, multiplied by 100 (e.g. JPY/INR -> 58.35).
  - Methanol: Factored by live USD/CNY rate.
  - Smart Lock: Saves to fallback file if Excel is open.
"""

import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import config

logger = logging.getLogger("ExcelWriter")

# Professional Styling Definitions
HEADER_FONT = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")  # Dark Navy Blue
HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center", wrap_text=True)

DATA_FONT = Font(name="Segoe UI", size=10)
DATA_ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
DATA_ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
DATA_ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

THIN_SIDE = Side(style="thin", color="D9D9D9")
BORDER_ALL_THIN = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)


def _apply_header_styles(ws, columns):
    """Applies styling to the header row (row 1)."""
    ws.row_dimensions[1].height = 28
    for col_num in range(1, len(columns) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGNMENT
        cell.border = BORDER_ALL_THIN


def _auto_adjust_column_widths(ws):
    """Auto-fits column widths based on maximum content length with padding."""
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_length = 0
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_length:
                max_length = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_length + 5, 14)


def save_or_update_excel(
    df_currencies: pd.DataFrame,
    df_energy: Optional[pd.DataFrame] = None,
    df_metals: Optional[pd.DataFrame] = None,
    file_path: Path = config.EXCEL_FILE,
    timestamp_str: Optional[str] = None
) -> bool:
    """
    Saves extracted currencies, energy, and metals commodities into the Excel workbook across 4 sheets.
    """
    if df_currencies.empty and (df_energy is None or df_energy.empty) and (df_metals is None or df_metals.empty):
        logger.warning("Empty DataFrames provided. Skipping Excel write.")
        return False

    if timestamp_str is None:
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    target_path = Path(file_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load existing workbook or create new one
        if target_path.exists():
            try:
                wb = openpyxl.load_workbook(target_path)
            except Exception:
                wb = openpyxl.Workbook()
        else:
            wb = openpyxl.Workbook()

        # ==============================================================
        # SHEET 1: Live_Rates (Currencies Snapshot)
        # ==============================================================
        if not df_currencies.empty:
            if config.EXCEL_SHEET_LIVE in wb.sheetnames:
                ws_live = wb[config.EXCEL_SHEET_LIVE]
                if ws_live.max_row > 1:
                    ws_live.delete_rows(2, ws_live.max_row)
            else:
                if wb.active.title in ["Sheet", "Currencies"]:
                    ws_live = wb.active
                    ws_live.title = config.EXCEL_SHEET_LIVE
                else:
                    ws_live = wb.create_sheet(title=config.EXCEL_SHEET_LIVE, index=0)

            # Write Live Headers
            for col_idx, col_name in enumerate(config.REQUIRED_COLUMNS, start=1):
                ws_live.cell(row=1, column=col_idx, value=col_name)
            _apply_header_styles(ws_live, config.REQUIRED_COLUMNS)

            # Write Live Data Rows
            for row_idx, (_, row_data) in enumerate(df_currencies.iterrows(), start=2):
                ws_live.row_dimensions[row_idx].height = 22
                for col_idx, col_name in enumerate(config.REQUIRED_COLUMNS, start=1):
                    val = row_data[col_name]
                    cell = ws_live.cell(row=row_idx, column=col_idx)

                    if col_name == "Price":
                        try:
                            clean_num = float(str(val).replace(",", ""))
                            if clean_num < 1.0:
                                clean_num = clean_num * 100.0
                            cell.value = clean_num
                            cell.number_format = "#,##0.0000"
                            cell.alignment = DATA_ALIGN_RIGHT
                        except ValueError:
                            cell.value = val
                            cell.alignment = DATA_ALIGN_RIGHT
                    elif col_name == "Crosses":
                        cell.value = val
                        cell.alignment = DATA_ALIGN_CENTER
                        cell.font = Font(name="Segoe UI", size=10, bold=True)
                    else:
                        cell.value = val
                        cell.alignment = DATA_ALIGN_RIGHT

                    if col_name != "Crosses":
                        cell.font = DATA_FONT
                    cell.border = BORDER_ALL_THIN

            _auto_adjust_column_widths(ws_live)

        # ==============================================================
        # SHEET 2: History_Log (Append Currency Past Runs)
        # ==============================================================
        if not df_currencies.empty:
            if config.EXCEL_SHEET_HISTORY in wb.sheetnames:
                ws_history = wb[config.EXCEL_SHEET_HISTORY]
            else:
                ws_history = wb.create_sheet(title=config.EXCEL_SHEET_HISTORY)
                for col_idx, col_name in enumerate(config.HISTORY_COLUMNS, start=1):
                    ws_history.cell(row=1, column=col_idx, value=col_name)
                _apply_header_styles(ws_history, config.HISTORY_COLUMNS)

            start_history_row = ws_history.max_row + 1
            for i, (_, row_data) in enumerate(df_currencies.iterrows()):
                current_h_row = start_history_row + i
                ws_history.row_dimensions[current_h_row].height = 20

                cell_ts = ws_history.cell(row=current_h_row, column=1, value=timestamp_str)
                cell_ts.alignment = DATA_ALIGN_CENTER
                cell_ts.font = DATA_FONT
                cell_ts.border = BORDER_ALL_THIN

                for col_idx, col_name in enumerate(config.REQUIRED_COLUMNS, start=2):
                    val = row_data[col_name]
                    cell = ws_history.cell(row=current_h_row, column=col_idx)

                    if col_name == "Price":
                        try:
                            clean_num = float(str(val).replace(",", ""))
                            if clean_num < 1.0:
                                clean_num = clean_num * 100.0
                            cell.value = clean_num
                            cell.number_format = "#,##0.0000"
                            cell.alignment = DATA_ALIGN_RIGHT
                        except ValueError:
                            cell.value = val
                            cell.alignment = DATA_ALIGN_RIGHT
                    elif col_name == "Crosses":
                        cell.value = val
                        cell.alignment = DATA_ALIGN_CENTER
                        cell.font = Font(name="Segoe UI", size=10, bold=True)
                    else:
                        cell.value = val
                        cell.alignment = DATA_ALIGN_RIGHT

                    if col_name != "Crosses":
                        cell.font = DATA_FONT
                    cell.border = BORDER_ALL_THIN

            _auto_adjust_column_widths(ws_history)

        # ==============================================================
        # SHEET 3: Energy_Commodities (Crude Oil, Brent, Gas, Methanol...)
        # ==============================================================
        if df_energy is not None and not df_energy.empty:
            if config.EXCEL_SHEET_ENERGY in wb.sheetnames:
                ws_energy = wb[config.EXCEL_SHEET_ENERGY]
                if ws_energy.max_row > 1:
                    ws_energy.delete_rows(2, ws_energy.max_row)
            else:
                ws_energy = wb.create_sheet(title=config.EXCEL_SHEET_ENERGY)

            for col_idx, col_name in enumerate(config.COMMODITY_COLUMNS, start=1):
                ws_energy.cell(row=1, column=col_idx, value=col_name)
            _apply_header_styles(ws_energy, config.COMMODITY_COLUMNS)

            for row_idx, (_, row_data) in enumerate(df_energy.iterrows(), start=2):
                ws_energy.row_dimensions[row_idx].height = 22
                for col_idx, col_name in enumerate(config.COMMODITY_COLUMNS, start=1):
                    val = row_data[col_name]
                    cell = ws_energy.cell(row=row_idx, column=col_idx)

                    if col_name == "Price":
                        try:
                            clean_num = float(str(val).replace(",", ""))
                            cell.value = clean_num
                            cell.number_format = "#,##0.00"
                            cell.alignment = DATA_ALIGN_RIGHT
                        except ValueError:
                            cell.value = val
                            cell.alignment = DATA_ALIGN_RIGHT
                    elif col_name == "Commodity":
                        cell.value = val
                        cell.alignment = DATA_ALIGN_LEFT
                        cell.font = Font(name="Segoe UI", size=10, bold=True)
                    else:
                        cell.value = val
                        cell.alignment = DATA_ALIGN_RIGHT

                    if col_name != "Commodity":
                        cell.font = DATA_FONT
                    cell.border = BORDER_ALL_THIN

            _auto_adjust_column_widths(ws_energy)

        # ==============================================================
        # SHEET 4: Metals_Commodities (HRC Steel, Copper, Aluminum, Zinc...)
        # ==============================================================
        if df_metals is not None and not df_metals.empty:
            if config.EXCEL_SHEET_METALS in wb.sheetnames:
                ws_metals = wb[config.EXCEL_SHEET_METALS]
                if ws_metals.max_row > 1:
                    ws_metals.delete_rows(2, ws_metals.max_row)
            else:
                ws_metals = wb.create_sheet(title=config.EXCEL_SHEET_METALS)

            for col_idx, col_name in enumerate(config.COMMODITY_COLUMNS, start=1):
                ws_metals.cell(row=1, column=col_idx, value=col_name)
            _apply_header_styles(ws_metals, config.COMMODITY_COLUMNS)

            for row_idx, (_, row_data) in enumerate(df_metals.iterrows(), start=2):
                ws_metals.row_dimensions[row_idx].height = 22
                for col_idx, col_name in enumerate(config.COMMODITY_COLUMNS, start=1):
                    val = row_data[col_name]
                    cell = ws_metals.cell(row=row_idx, column=col_idx)

                    if col_name == "Price":
                        try:
                            clean_num = float(str(val).replace(",", ""))
                            cell.value = clean_num
                            cell.number_format = "#,##0.00"
                            cell.alignment = DATA_ALIGN_RIGHT
                        except ValueError:
                            cell.value = val
                            cell.alignment = DATA_ALIGN_RIGHT
                    elif col_name == "Commodity":
                        cell.value = val
                        cell.alignment = DATA_ALIGN_LEFT
                        cell.font = Font(name="Segoe UI", size=10, bold=True)
                    else:
                        cell.value = val
                        cell.alignment = DATA_ALIGN_RIGHT

                    if col_name != "Commodity":
                        cell.font = DATA_FONT
                    cell.border = BORDER_ALL_THIN

            _auto_adjust_column_widths(ws_metals)

        # Save workbook
        try:
            wb.save(target_path)
            logger.info(f"Successfully saved to Excel: {target_path} (All 4 sheets updated).")
        except PermissionError:
            fallback_path = target_path.parent / "extracted_data_latest.xlsx"
            wb.save(fallback_path)
            logger.warning(
                f"NOTICE: '{target_path.name}' is currently OPEN in Excel. "
                f"Updated workbook saved to fallback: '{fallback_path.name}'."
            )

        # Convenience copy in wsp root
        root_copy_path = config.BASE_DIR / "extracted_data.xlsx"
        try:
            wb.save(root_copy_path)
        except Exception:
            pass

        return True

    except Exception as e:
        logger.error(f"Unexpected error while saving Excel file: {e}")
        return False
