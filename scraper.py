"""
Web Scraper Module using Selenium.
Handles browser automation, waiting for dynamic JavaScript/AWS WAF content to render,
and retrieving the rendered HTML across the target URLs using a single efficient browser session.
"""

import time
import logging
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

import config

logger = logging.getLogger("Scraper")


def create_driver(headless: bool = config.HEADLESS) -> webdriver.Chrome:
    """
    Initializes and configures a Chrome WebDriver instance.
    Sets standard flags to mimic a real user and avoid automation detection.
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"user-agent={config.USER_AGENT}")

    # Hide automation flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Disable images and notifications to speed up loading
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    return driver


def fetch_all_pages_html(urls: Optional[List[str]] = None) -> List[str]:
    """
    Launches a single browser session and visits each target URL sequentially.
    Waits for the table content to load on each page and collects the rendered HTML.

    Returns:
        List[str]: List of rendered HTML source strings for each successfully fetched URL.
    """
    if urls is None:
        urls = config.TARGET_URLS

    html_pages = []
    driver = None

    try:
        logger.info(f"Initializing Chrome browser session for {len(urls)} target page(s)...")
        driver = create_driver()

        for idx, url in enumerate(urls, start=1):
            success = False
            for attempt in range(1, config.MAX_RETRIES + 1):
                try:
                    logger.info(f"Fetching URL [{idx}/{len(urls)}] (Attempt {attempt}): {url}")
                    driver.get(url)

                    # Explicitly wait until at least one <table> appears
                    wait = WebDriverWait(driver, config.TABLE_WAIT_TIMEOUT)
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

                    # Brief pause to ensure all dynamically injected cells populate
                    time.sleep(2)

                    page_source = driver.page_source
                    html_pages.append(page_source)
                    logger.info(f"Successfully loaded page {idx}: {len(page_source):,} characters.")
                    success = True
                    break

                except TimeoutException:
                    logger.warning(f"Timeout on page [{idx}/{len(urls)}] attempt {attempt}.")
                except WebDriverException as e:
                    logger.warning(f"WebDriver glitch on page [{idx}/{len(urls)}] attempt {attempt}: {e}")

                if attempt < config.MAX_RETRIES:
                    time.sleep(config.RETRY_DELAY_SEC)

            if not success:
                logger.error(f"Failed to load URL after {config.MAX_RETRIES} attempts: {url}")

    except Exception as e:
        logger.error(f"Error during browser automation session: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser session closed cleanly.")
            except Exception:
                pass

    return html_pages
