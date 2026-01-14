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
    
    headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
    })
    
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
