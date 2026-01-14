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
    """Async URL fetcher with better headers"""
    if headers is None:
        headers = {}

    # Comprehensive headers for bypassing restrictions
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Sec-Ch-Ua': '"Not A(Brand";v="8", "Chromium";v="132"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }
    
    # Merge provided headers with defaults
    merged_headers = {**default_headers, **headers}
    
    # Add Referer if not present and if it's a player page
    if 'referer' not in merged_headers and 'zephyrflick' in url.lower():
        merged_headers['Referer'] = 'https://watchanimeworld.net/'
    
    for attempt in range(3):
        try:
            async with session.get(url, headers=merged_headers, timeout=15) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status in [403, 429]:
                    # Rate limiting or forbidden - wait and retry
                    await asyncio.sleep(2)
                    continue
                else:
                    # Try with different User-Agent
                    merged_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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


