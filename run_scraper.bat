@echo off
title Live Currency Scraper & Excel Automation
cd /d "%~dp0"
echo ========================================================
echo   Starting Currency Scraper (Trading Economics)...
echo ========================================================
python main.py --mode manual
echo.
echo ========================================================
echo   Done! Opening Excel workbook...
echo ========================================================
timeout /t 2 >nul
start output\extracted_data.xlsx
pause
