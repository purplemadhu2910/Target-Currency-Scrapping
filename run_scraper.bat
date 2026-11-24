@echo off
title Live Currencies & Energy Commodities Scraper
cd /d "%~dp0"
echo ========================================================
echo   Starting Market Scraper (Currencies + Energy)...
echo   Target Energy: Crude Oil, Brent, Natural gas,
echo                  TTF Gas, Ethanol, Methanol, Jet Fuel
echo ========================================================
python main.py --mode manual
echo.
echo ========================================================
echo   Done! Opening Excel workbook (Check Sheet 3: Energy_Commodities)
echo ========================================================
timeout /t 2 >nul
start output\extracted_data.xlsx
pause
