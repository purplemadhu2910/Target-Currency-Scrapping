# Live Market Scraping & Excel Automation Project (`wsp`)

A Python web scraping, Excel automation, and web dashboard system that extracts **Target Currencies** and **Energy Commodities** directly from **Trading Economics**, displays them cleanly in the VS Code terminal or web dashboard, and automatically creates/updates an Excel workbook (`extracted_data.xlsx`).

---

## 1. Tracked Assets & Rules

### A. Target Currency Pairs (Forex)
1. **USD/INR** (US Dollar / Indian Rupee)
2. **EUR/INR** (Euro / Indian Rupee)
3. **JPY/INR** (Japanese Yen / Indian Rupee - multiplied by 100 per market convention)
4. **USD/JPY** (US Dollar / Japanese Yen)
5. **EUR/USD** (Euro / US Dollar)

### B. Target Energy Commodities
1. **Crude Oil** (USD/Bbl)
2. **Brent** (USD/Bbl)
3. **Natural gas** (USD/MMBtu)
4. **TTF Gas** (European Natural Gas benchmark - EUR/MWh)
5. **Ethanol** (USD/Gal)
6. **Methanol** (CNY/Tonne converted/factored by live USD/CNY rate)
7. **Jet Fuel** (Tracked status)

---

## 2. Excel Workbook Structure (`extracted_data.xlsx`)

The generated workbook contains **three dedicated sheets**:

* **Sheet 1 (`Live_Rates`):** Latest live snapshot of the 5 currency pairs.
* **Sheet 2 (`History_Log`):** Historical log of past currency extractions with timestamps.
* **Sheet 3 (`Energy_Commodities`):** Live Energy commodities data (Crude Oil, Brent, Natural gas, TTF Gas, Ethanol, Methanol factored by USDCNY, Jet Fuel).

---

## 3. Project Structure

```text
wsp/
│
├── app.py                # Streamlit interactive Web Dashboard (Currencies + Commodities)
├── config.py             # URLs, asset lists, mapping dictionaries, timeouts
├── scraper.py            # Single-session headless Selenium browser engine
├── data_processing.py    # BeautifulSoup & Pandas parser: currencies, energy, and Methanol factoring
├── excel_writer.py       # OpenPyXL 3-sheet automation (Live_Rates, History_Log, Energy_Commodities)
├── main.py               # Main CLI orchestrator (Manual, Periodic, Continuous, and Daily modes)
├── run_scraper.bat       # 1-click launcher for terminal extraction & opening Excel
├── run_dashboard.bat     # 1-click launcher for the Streamlit web dashboard
├── requirements.txt      # Project library dependencies
├── README.md             # Usage guide
│
├── logs/                 # Execution logs
│   └── scraper.log
└── output/               # Output Excel file
    └── extracted_data.xlsx
```

---

## 4. How to Run

From your terminal inside `wsp`:

### A. Manual Run (Run Once on Demand)
```powershell
python main.py --mode manual
```

### B. Daily Run at 3:00 PM
```powershell
python main.py --mode daily --time 15:00
```

### C. Web Dashboard (Interactive Frontend)
```powershell
python -m streamlit run app.py
```
*(Or double-click `run_dashboard.bat`).*

### D. Other Modes
- **Periodic (Every N min):** `python main.py --mode periodic --interval 5`
- **Continuous (Change Detection):** `python main.py --mode continuous --poll 30`
- **1-Click Run:** Double-click `run_scraper.bat`.

---

## 5. Output Locations

- **Excel Files:** 
  - [wsp/output/extracted_data.xlsx](file:///c:/Users/madhu/OneDrive/Desktop/Madhu/INTERNSHIP/wsp/output/extracted_data.xlsx)
  - [wsp/extracted_data.xlsx](file:///c:/Users/madhu/OneDrive/Desktop/Madhu/INTERNSHIP/wsp/extracted_data.xlsx)
- **Log File:** [wsp/logs/scraper.log](file:///c:/Users/madhu/OneDrive/Desktop/Madhu/INTERNSHIP/wsp/logs/scraper.log)
