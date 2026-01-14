import re
import os
import aiohttp
import asyncio
from urllib.parse import urlparse
from config import USER_AGENT, TIMEOUT, TEMP_DIR

def is_valid_url(url):
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_domain(url):
    """Extract domain from URL"""
    return urlparse(url).netloc

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

async def fetch_url(session, url, headers=None):
    """Async URL fetcher with retry"""
    if headers is None:
        headers = {}

    # Use a full set of headers, not just User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://watchanimeworld.net/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'DNT': '1',
    }
    
    for attempt in range(3):
        try:
            async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    continue
        except Exception as e:
            if attempt == 2:
                raise e
            await asyncio.sleep(1)
    
    return None

def get_temp_path(filename):
    """Get path in temp directory"""
    return os.path.join(TEMP_DIR, filename)

def cleanup_temp(file_path):
    """Cleanup temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass

