"""
Excel Automation Module using OpenPyXL.
Handles saving extracted target currency data to 'output/extracted_data.xlsx'
and 'extracted_data.xlsx', updating records, avoiding duplicates,
and applying professional styling and formatting.

Rule: If Price < 1, it is multiplied by 100 (e.g. JPY/INR 0.5835 -> 58.35).
Smart Lock Handling: If the file is open in Microsoft Excel, saves a fallback copy without crashing.
"""

import shutil
import logging
from pathlib import Path
from typing import Dict, Any
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


def _apply_header_styles(ws):
    """Applies styling to the header row (row 1)."""
    ws.row_dimensions[1].height = 28
    for col_num in range(1, len(config.REQUIRED_COLUMNS) + 1):
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
        ws.column_dimensions[col_letter].width = max(max_length + 5, 15)


def save_or_update_excel(df: pd.DataFrame, file_path: Path = config.EXCEL_FILE) -> bool:
    """
    Saves the extracted currency DataFrame (the 5 target pairs without YTD)
    into the Excel workbook.
    Ensures that if Price < 1, it is multiplied by 100.
    Writes clean headers, formats numbers/percentages, and applies auto-fitting.
    If the file is open in Microsoft Excel, saves a fallback copy so data is never lost.

    Returns:
        bool: True on success, False if file writing encounters an error.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided. Skipping Excel write.")
        return False

    target_path = Path(file_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Build fresh workbook for target pairs to ensure clean, dedicated view
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = config.EXCEL_SHEET_NAME

        # Write header row (Crosses, Price, Weekly, Monthly, YoY)
        for col_idx, col_name in enumerate(config.REQUIRED_COLUMNS, start=1):
            ws.cell(row=1, column=col_idx, value=col_name)

        _apply_header_styles(ws)

        # Write data rows
        for row_idx, (_, row_data) in enumerate(df.iterrows(), start=2):
            ws.row_dimensions[row_idx].height = 22

            for col_idx, col_name in enumerate(config.REQUIRED_COLUMNS, start=1):
                val = row_data[col_name]
                cell = ws.cell(row=row_idx, column=col_idx)

                # Format numeric Price (if < 1, multiply by 100)
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

        _auto_adjust_column_widths(ws)

        # Try saving to the main target path
        try:
            wb.save(target_path)
            logger.info(f"Successfully saved {len(df)} target pairs into Excel: {target_path}")
        except PermissionError:
            # File is currently open in Microsoft Excel
            fallback_path = target_path.parent / "extracted_data_latest.xlsx"
            wb.save(fallback_path)
            logger.warning(
                f"NOTICE: '{target_path.name}' is currently OPEN in Microsoft Excel (Windows file lock). "
                f"The updated data has been saved to: '{fallback_path.name}'. "
                "Close Microsoft Excel to allow updating the main file directly."
            )

        # Also save a convenience copy in wsp root
        root_copy_path = config.BASE_DIR / "extracted_data.xlsx"
        try:
            wb.save(root_copy_path)
        except Exception:
            pass

        return True

    except Exception as e:
        logger.error(f"Unexpected error while saving Excel file: {e}")
        return False
