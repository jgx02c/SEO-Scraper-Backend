import os
import json
import re
import asyncio
import logging
from bs4 import BeautifulSoup
from functools import partial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_seo_and_content(html_content):
    """Extracts metadata, links, headings, images, and content from an HTML string."""
    try:
        logger.info("Starting SEO data extraction")
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove unnecessary scripts and styles
        for tag in soup(['script', 'style']):
            tag.decompose()

        # Categorize meta tags
        meta_tags = {
            "SEO": {},
            "Technical": {},
            "Social Media": {}
        }

        logger.info("Processing meta tags")
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')

            if name and content:
                if name in ["description", "keywords", "robots", "canonical"] or name.startswith("og:"):
                    meta_tags["SEO"][name] = content
                elif name.startswith("twitter:"):
                    meta_tags["Social Media"][name] = content
                else:
                    meta_tags["Technical"][name] = content

            if meta.get('charset'):
                meta_tags["Technical"]["charset"] = meta.get('charset')

        # Extract page title
        title = soup.title.string.strip() if soup.title else "No Title"
        logger.info(f"Extracted title: {title[:50]}...")

        # Extract all links
        logger.info("Processing links")
        links = [link.get('href') for link in soup.find_all('a', href=True)]
        internal_links = [link for link in links if link and (link.startswith("/") or "leapsandrebounds.com" in link)]
        external_links = [link for link in links if link and "leapsandrebounds.com" not in link and not link.startswith("/")]

        # Extract headings by level
        logger.info("Processing headings")
        headings = {f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")] for i in range(1, 7)}

        # Extract images with src and alt text
        logger.info("Processing images")
        images = {}
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            images[src] = {
                "alt": alt if alt else "MISSING ALT TEXT",
                "width": img.get("width", ""),
                "height": img.get("height", "")
            }

        # Extract structured data (JSON-LD)
        logger.info("Processing structured data")
        json_ld_scripts = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if script.string:
                    json_ld_scripts.append(json.loads(script.string))
            except json.JSONDecodeError:
                json_ld_scripts.append({"error": "Invalid JSON-LD"})

        # Extract text content
        logger.info("Processing text content")
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
        divs = [div.get_text(separator=' ', strip=True) for div in soup.find_all(['div', 'section', 'article'])]
        cleaned_content = ' '.join(paragraphs + divs)

        result = {
            "title": title,
            "meta": meta_tags,
            "links": {
                "internal": internal_links,
                "external": external_links
            },
            "headings": headings,
            "images": images,
            "structured_data": json_ld_scripts,
            "content": cleaned_content,
            "html_lang": soup.find('html').get('lang', '')
        }

        logger.info("SEO data extraction completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in extract_seo_and_content: {str(e)}")
        raise

def _process_html_sync(html_content):
    """Synchronous function to process HTML and return structured SEO insights."""
    try:
        seo_data = extract_seo_and_content(html_content)
        return json.dumps(seo_data, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error in _process_html_sync: {str(e)}")
        raise

async def process_html(html_content):
    """
    Asynchronous wrapper for HTML processing.
    Uses a thread pool for CPU-intensive operations.
    
    Args:
        html_content (str): The HTML content to process
        
    Returns:
        str: JSON string containing structured SEO data
    """
    try:
        logger.info("Starting async HTML processing")
        
        # Run the CPU-intensive processing in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(_process_html_sync, html_content)
        )
        
        logger.info("HTML processing completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in async process_html: {str(e)}")
        raise

# Example usage
if __name__ == "__main__":
    async def main():
        with open("example.html", "r", encoding="utf-8") as file:
            html_content = file.read()
        try:
            result = await process_html(html_content)
            print(result)
        except Exception as e:
            print(f"Error processing HTML: {e}")

    asyncio.run(main())