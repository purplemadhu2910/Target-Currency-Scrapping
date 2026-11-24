"""
Configuration settings for the Web Scraping & Excel Automation Project.
All project constants, paths, and URLs are maintained in this single module.
"""

from pathlib import Path

# --- DIRECTORY PATHS ---
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Ensure output and log directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Excel output file path and sheet names
EXCEL_FILE = OUTPUT_DIR / "extracted_data.xlsx"
EXCEL_SHEET_LIVE = "Live_Rates"
EXCEL_SHEET_HISTORY = "History_Log"
EXCEL_SHEET_ENERGY = "Energy_Commodities"

# Log file path
LOG_FILE = LOGS_DIR / "scraper.log"

# --- SPECIFIC TARGET CURRENCY PAIRS ---
TARGET_PAIRS_DISPLAY = [
    "USD/INR",
    "EUR/INR",
    "JPY/INR",
    "USD/JPY",
    "EUR/USD"
]

# Canonical lookup mapping (normalized without slash -> display format with slash)
TARGET_PAIRS_MAP = {
    "USDINR": "USD/INR",
    "EURINR": "EUR/INR",
    "JPYINR": "JPY/INR",
    "USDJPY": "USD/JPY",
    "EURUSD": "EUR/USD"
}

# --- SPECIFIC TARGET ENERGY COMMODITIES ---
TARGET_COMMODITIES = {
    "Crude Oil": ["Crude Oil"],
    "Brent": ["Brent"],
    "Natural gas": ["Natural gas"],
    "TTF Gas": ["EU Gas", "TTF Gas", "Dutch TTF"],
    "Ethanol": ["Ethanol"],
    "Methanol": ["Methanol"],
    "Jet Fuel": ["Jet Fuel", "Kerosene"]
}

# Target URLs needed to capture currencies + energy commodities from Trading Economics
TARGET_URLS = [
    "https://tradingeconomics.com/currencies",           # Contains USD/INR, USD/JPY, EUR/USD, USD/CNY
    "https://tradingeconomics.com/currencies?base=eur",  # Contains EUR/INR
    "https://tradingeconomics.com/currencies?base=jpy",  # Contains JPY/INR
    "https://tradingeconomics.com/commodities",          # Contains Energy commodities table
]

# Columns configuration
REQUIRED_COLUMNS = ["Crosses", "Price", "Weekly", "Monthly", "YoY"]
COMMODITY_COLUMNS = ["Commodity", "Price", "Weekly", "Monthly", "YoY"]
HISTORY_COLUMNS = ["Timestamp", "Crosses", "Price", "Weekly", "Monthly", "YoY"]

# Column mapping aliases to match dynamic website header text
COLUMN_ALIASES = {
    "Crosses": ["Crosses", "Symbol", "Major", "Europe", "America", "Asia", "Oceania", "Africa", "Currency", "Commodity", "Energy"],
    "Price": ["Price", "Last"],
    "Weekly": ["Weekly", "1W", "Week"],
    "Monthly": ["Monthly", "1M", "Month"],
    "YoY": ["YoY", "Yearly", "1Y", "Year over Year"]
}

# --- BROWSER / SCRAPER SETTINGS ---
HEADLESS = True
PAGE_LOAD_TIMEOUT = 30  # Maximum seconds to wait for initial page load
TABLE_WAIT_TIMEOUT = 15  # Maximum seconds to wait for table data to render
MAX_RETRIES = 3          # Retry attempts if extraction encounters an error
RETRY_DELAY_SEC = 3      # Seconds to wait between retries

# User Agent string to mimic a standard Google Chrome browser
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# --- AUTOMATION DEFAULTS ---
DEFAULT_PERIODIC_INTERVAL_MIN = 5  # Default interval for periodic mode (in minutes)
DEFAULT_CONTINUOUS_POLL_SEC = 30   # Default polling delay for continuous mode (in seconds)
