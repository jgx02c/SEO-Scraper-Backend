import time
import asyncio
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging
from functools import partial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_chromium_driver_path():
    """Get the path to the system chromium driver."""
    # Common paths for chromium-driver in Linux/Docker environments
    possible_paths = [
        '/usr/bin/chromedriver',           # Most common in Docker
        '/usr/local/bin/chromedriver',     # Alternative location
        '/snap/bin/chromium.chromedriver', # Snap package
        'chromedriver'                     # System PATH
    ]
    
    for path in possible_paths:
        if os.path.exists(path) or path == 'chromedriver':
            logger.info(f"Using chromium driver at: {path}")
            return path
    
    raise Exception("No chromium driver found. Please install chromium-driver package.")

def _fetch_html_sync(url: str) -> str:
    """Synchronous function to fetch HTML content using Selenium."""
    logger.info(f"Starting HTML fetch for: {url}")
    
    chrome_options = Options()
    
    # Set chromium binary location - works for Docker and local with chromium installed
    chromium_path = '/usr/bin/chromium'
    if os.path.exists(chromium_path):
        chrome_options.binary_location = chromium_path
    elif os.path.exists('/usr/bin/chromium-browser'):
        chrome_options.binary_location = '/usr/bin/chromium-browser'
    
    # Essential options for headless operation in Docker
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # Docker-specific options (removed --single-process as it can cause hanging)
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    chrome_options.add_argument("--data-path=/tmp/chrome-data")
    chrome_options.add_argument("--disk-cache-dir=/tmp/chrome-cache")
    
    # Set window size for consistent rendering
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Memory and performance options
    chrome_options.add_argument("--max_old_space_size=4096")
    chrome_options.add_argument("--memory-pressure-off")
    
    driver = None
    try:
        # Use system chromium driver instead of ChromeDriverManager
        driver_path = _get_chromium_driver_path()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set shorter timeouts to prevent hanging
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(5)
        
        logger.info(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for JavaScript to execute - reduced from 5 to 3 seconds
        logger.info("Waiting for page load...")
        time.sleep(3)
        
        html_content = driver.page_source
        logger.info(f"Successfully fetched HTML for: {url} (length: {len(html_content)})")
        return html_content
        
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None
        
    finally:
        if driver:
            try:
                logger.info("Closing browser")
                driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")

async def fetch_html(url: str) -> str:
    """
    Asynchronous wrapper for fetching HTML content.
    Uses a thread pool executor to run Selenium without blocking.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        str: The HTML content of the page, or None if there was an error
    """
    try:
        logger.info(f"Starting async HTML fetch for: {url}")
        
        # Run the synchronous function in a thread pool
        loop = asyncio.get_event_loop()
        html_content = await loop.run_in_executor(
            None,
            partial(_fetch_html_sync, url)
        )
        
        if html_content:
            logger.info(f"Successfully retrieved HTML for: {url}")
            return html_content
        else:
            logger.error(f"Failed to retrieve HTML for: {url}")
            return None
            
    except Exception as e:
        logger.error(f"Async wrapper error for {url}: {e}")
        return None

# Example usage
if __name__ == "__main__":
    async def main():
        test_url = "https://example.com"
        html = await fetch_html(test_url)
        if html:
            print("Preview of fetched HTML:")
            print(html[:500])  # Print first 500 characters of HTML for preview
        else:
            print("Failed to fetch HTML")

    asyncio.run(main())