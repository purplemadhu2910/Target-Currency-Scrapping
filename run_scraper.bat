@echo off
title Live Currencies, Energy & Metals Market Scraper
cd /d "%~dp0"
echo ========================================================
echo   Starting Market Scraper (Currencies + Energy + Metals)...
echo   Target Energy: Crude Oil, Brent, Natural gas,
echo                  TTF Gas, Ethanol, Methanol, Jet Fuel
echo   Target Metals: HRC Steel, Copper (x2204.62), Aluminum,
echo                  TinUSD, Zinc, Nickel, Platinum,
echo                  Palladium, Rhodium, Lead, Lithium,
echo                  Urea, Di-ammonium
echo ========================================================
python main.py --mode manual
echo.
echo ========================================================
echo   Done! Opening Excel workbook (Sheets: Live_Rates, History_Log,
echo   Energy_Commodities, Metals_Commodities)
echo ========================================================
timeout /t 2 >nul
start output\extracted_data.xlsx
pause
