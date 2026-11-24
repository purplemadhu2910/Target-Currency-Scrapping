@echo off
title Live Currencies & Energy Commodities Dashboard
cd /d "%~dp0"
echo ========================================================
echo   Launching Market Automation Dashboard (Currencies + Energy)...
echo ========================================================
python -m streamlit run app.py
pause
