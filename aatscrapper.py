# aatscrapper.py
import requests
from bs4 import BeautifulSoup as bs
import urllib.parse
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

def get_anime_urls(url: str) -> Dict:
    """Get anime URLs with quality options from a given page."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = bs(r.content, "html.parser")
        
        anime_data = {}
        title_div = soup.find("div", "entry-content clear")
        
        if not title_div:
            raise ValueError("Could not find title element")
            
        anime_data["title"] = title_div.find("h2").text.strip(" !")
        anime_data["links"] = []
        
        for div in soup.find_all("div", "bg-margin-for-link"):
            quality = div.find("a", "bg-showmore-plg-link").text
            quality = determine_quality(quality)
            
            links = [link["href"] for link in div.find("div").find_all("a")]
            if links:
                anime_data["links"].append((quality, links))
                
        return anime_data
        
    except Exception as e:
        logger.error(f"Error in get_anime_urls: {e}")
        raise

def determine_quality(quality_str: str) -> str:
    """Determine video quality from string."""
    quality = "SD"
    if "FHD" in quality_str:
        quality = "FHD"
    elif "HD" in quality_str:
        quality = "HD"
    return quality

def fix_url(url: str) -> str:
    """Fix malformed URLs."""
    try:
        if "/0:/" in url:
            x, y = url.split("/0:/")
            return x + "/0:/" + urllib.parse.quote(y)
        return url
    except Exception as e:
        logger.error(f"Error fixing URL: {e}")
        return url

def get_index_urls(url: str) -> List[str]:
    """Get index URLs from iframes."""
    try:
        r = requests.get(url, allow_redirects=False, timeout=10)
        r.raise_for_status()
        soup = bs(r.text, "html.parser")
        
        return [fix_url(i["src"]) for i in soup.find_all("iframe") if i.get("src")]
        
    except Exception as e:
        logger.error(f"Error in get_index_urls: {e}")
        raise
