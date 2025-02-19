import time
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging
from functools import partial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _fetch_html_sync(url: str) -> str:
    """Synchronous function to fetch HTML content using Selenium."""
    logger.info(f"Starting HTML fetch for: {url}")
    
    # Configure Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    
    # Use webdriver-manager to automatically manage the ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        logger.info(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for JavaScript to execute
        logger.info("Waiting for page load...")
        time.sleep(5)  # Consider replacing with explicit waits if possible
        
        html_content = driver.page_source
        logger.info(f"Successfully fetched HTML for: {url}")
        return html_content
        
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None
        
    finally:
        logger.info("Closing browser")
        driver.quit()

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