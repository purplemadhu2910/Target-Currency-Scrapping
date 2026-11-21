@echo off
title Live Currency Automation Dashboard
cd /d "%~dp0"
echo ========================================================
echo   Launching Streamlit Currency Dashboard...
echo ========================================================
streamlit run app.py
pause
