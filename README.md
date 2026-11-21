# Target Currency Scraping & Excel Automation Project (`wsp`)

A Python web scraping, Excel automation, and web dashboard system that extracts the **5 target currency pairs** directly from **Trading Economics**, displays them cleanly in the VS Code terminal or web dashboard, and automatically creates/updates an Excel workbook (`extracted_data.xlsx`).

---

## 1. The 5 Target Currency Pairs Extracted

1. **USD/INR** (US Dollar / Indian Rupee)
2. **EUR/INR** (Euro / Indian Rupee)
3. **JPY/INR** (Japanese Yen / Indian Rupee - multiplied by 100 per market convention)
4. **USD/JPY** (US Dollar / Japanese Yen)
5. **EUR/USD** (Euro / US Dollar)

For each pair, the **5 required columns** are extracted:
- `Crosses`
- `Price` (with rule: if price < 1, multiplied by 100)
- `Weekly`
- `Monthly`
- `YoY`

---

## 2. Project Structure

```text
wsp/
│
├── app.py                # Streamlit interactive Web Dashboard
├── config.py             # URLs, 5 target pairs mapping, and column definitions
├── scraper.py            # Single-session headless Selenium browser automation
├── data_processing.py    # BeautifulSoup & Pandas parser: filters exclusively for the 5 pairs
├── excel_writer.py       # OpenPyXL automation: formats and writes the 5 target pairs
├── main.py               # Main CLI orchestrator supporting Manual, Periodic, and Continuous modes
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

## 3. How to Run

### A. Web Dashboard (Interactive Frontend)
From your terminal inside `wsp`:
```powershell
streamlit run app.py
```
*(Or simply double-click `run_dashboard.bat`).*

### B. Terminal Modes
- **Manual Mode (Run Once):**
  ```powershell
  python main.py --mode manual
  ```
- **Periodic Mode (Run on Timer):**
  ```powershell
  python main.py --mode periodic --interval 5
  ```
- **Continuous Mode (Change Detection):**
  ```powershell
  python main.py --mode continuous --poll 30
  ```
- **1-Click Run:** Double-click `run_scraper.bat`.

---

## 4. Output Locations

- **Excel Files:** 
  - [wsp/output/extracted_data.xlsx](file:///c:/Users/madhu/OneDrive/Desktop/Madhu/INTERNSHIP/wsp/output/extracted_data.xlsx)
  - [wsp/extracted_data.xlsx](file:///c:/Users/madhu/OneDrive/Desktop/Madhu/INTERNSHIP/wsp/extracted_data.xlsx)
- **Log File:** [wsp/logs/scraper.log](file:///c:/Users/madhu/OneDrive/Desktop/Madhu/INTERNSHIP/wsp/logs/scraper.log)
