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
EXCEL_SHEET_METALS = "Metals_Commodities"

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

# --- SPECIFIC TARGET METALS & INDUSTRIAL COMMODITIES ---
# Base exchange-traded commodity names
METALS_BASE_NAMES = {
    "HRC Steel": "HRC Steel, NYMEX",
    "Copper": "Copper, LME",
    "Aluminum": "Aluminium, LME",
    "TinUSD": "Tin, LME",
    "Zinc": "Zinc, LME",
    "Nickel": "Nickel, LME",
    "Platinum": "Platinum, NYMEX",
    "Palladium": "Palladium, NYMEX",
    "Rhodium": "Rhodium",
    "Lead": "Lead, LME",
    "Lithium": "Lithium",
    "Urea": "Urea, CME",
    "Di-ammonium": "Di-ammonium Phosphate, CME"
}

# Item names mapped with exact units quoted below metal names on Trading Economics
METALS_NAME_MAP = {
    "HRC Steel": "HRC Steel, NYMEX (USD/T)",
    "Copper": "Copper, LME (USD/Lbs)",
    "Aluminum": "Aluminium, LME (USD/T)",
    "TinUSD": "Tin, LME (USD/T)",
    "Zinc": "Zinc, LME (USD/T)",
    "Nickel": "Nickel, LME (USD/T)",
    "Platinum": "Platinum, NYMEX (USD/t.oz)",
    "Palladium": "Palladium, NYMEX (USD/t.oz)",
    "Rhodium": "Rhodium (USD/t oz.)",
    "Lead": "Lead, LME (USD/T)",
    "Lithium": "Lithium (CNY/T)",
    "Urea": "Urea, CME (USD/T)",
    "Di-ammonium": "Di-ammonium Phosphate, CME (USD/T)"
}

METALS_COMMODITIES = [
    {"commodity": "HRC Steel", "table": "Metal", "factor": 1, "aliases": ["HRC Steel"]},
    {"commodity": "Copper", "table": "Metal", "factor": 2204.62, "aliases": ["Copper"]},
    {"commodity": "Aluminum", "table": "Metal", "factor": 1, "aliases": ["Aluminum", "Aluminium"]},
    {"commodity": "TinUSD", "table": "Industrial", "factor": 1, "aliases": ["Tin", "TinUSD"]},
    {"commodity": "Zinc", "table": "Industrial", "factor": 1, "aliases": ["Zinc"]},
    {"commodity": "Nickel", "table": "Industrial", "factor": 1, "aliases": ["Nickel"]},
    {"commodity": "Platinum", "table": "Metal", "factor": 1, "aliases": ["Platinum"]},
    {"commodity": "Palladium", "table": "Industrial", "factor": 1, "aliases": ["Palladium"]},
    {"commodity": "Rhodium", "table": "Industrial", "factor": 1, "aliases": ["Rhodium"]},
    {"commodity": "Lead", "table": "Industrial", "factor": 1, "aliases": ["Lead"]},
    {"commodity": "Lithium", "table": "Metal", "factor": 1, "aliases": ["Lithium"]},
    {"commodity": "Urea", "table": "Non Metal", "factor": 1, "aliases": ["Urea"]},
    {"commodity": "Di-ammonium", "table": "Non Metal", "factor": 1, "aliases": ["Di-ammonium", "Di-Ammonium", "DAP"]},
]

# Target URLs needed to capture currencies + energy commodities from Trading Economics
TARGET_URLS = [
    "https://tradingeconomics.com/currencies",           # Contains USD/INR, USD/JPY, EUR/USD, USD/CNY
    "https://tradingeconomics.com/currencies?base=eur",  # Contains EUR/INR
    "https://tradingeconomics.com/currencies?base=jpy",  # Contains JPY/INR
    "https://tradingeconomics.com/commodities",          # Contains Energy, Metals, Industrial tables
]

# Columns configuration
REQUIRED_COLUMNS = ["Crosses", "Price", "Weekly", "Monthly", "YoY"]
COMMODITY_COLUMNS = ["Commodity", "Price", "Weekly", "Monthly", "YoY"]
METALS_COLUMNS = ["Item", "Table", "Price", "Weekly", "Monthly", "YoY"]
HISTORY_COLUMNS = ["Timestamp", "Crosses", "Price", "Weekly", "Monthly", "YoY"]

# Column mapping aliases to match dynamic website header text
COLUMN_ALIASES = {
    "Crosses": ["Crosses", "Symbol", "Major", "Europe", "America", "Asia", "Oceania", "Africa", "Currency", "Commodity", "Energy", "Metals", "Industrial"],
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
