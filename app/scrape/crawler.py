import aiohttp
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urlparse
from typing import List
import logging
import asyncio

async def crawl_and_clean_urls(base_url: str) -> List[str]:
    """
    Crawls a URL and returns a cleaned list of all links found on the page.
    The links are deduplicated and filtered to only include URLs from the same domain.
    
    Args:
        base_url (str): The URL to crawl and use as base domain filter
        
    Returns:
        list: Cleaned and filtered list of URLs from the page
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def get_page_links(url: str) -> List[str]:
        """Helper function to get all links from a page"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.error(f"Error status {response.status} for {url}")
                        return []
                    
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    links = soup.find_all('a', href=True)
                    
                    # Convert relative URLs to absolute
                    urls = [urllib.parse.urljoin(url, link['href']) for link in links]
                    logger.info(f"Found {len(urls)} raw URLs")
                    return urls
            
        except aiohttp.ClientError as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while crawling {url}: {str(e)}")
            return []
    
    def clean_urls(urls: List[str]) -> List[str]:
        """Helper function to clean and filter URLs"""
        # Get the base domain
        base_domain = urlparse(base_url).netloc
        
        # Filter URLs to only those matching base domain
        filtered_urls = [
            url for url in urls 
            if urlparse(url).netloc == base_domain
        ]
        
        # Remove duplicates while preserving order
        cleaned_urls = list(dict.fromkeys(filtered_urls))
        logger.info(f"Cleaned URLs: {len(cleaned_urls)} unique URLs from same domain")
        return cleaned_urls
    
    # Execute the crawl and clean process
    raw_urls = await get_page_links(base_url)
    cleaned_urls = clean_urls(raw_urls)
    
    # Add a small delay to prevent overwhelming the server
    await asyncio.sleep(0.1)
    
    return cleaned_urls

# Example usage
if __name__ == "__main__":
    async def main():
        test_url = "https://example.com"
        results = await crawl_and_clean_urls(test_url)
        for url in results:
            print(url)
    
    asyncio.run(main())