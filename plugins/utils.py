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
    """Async URL fetcher with better error handling"""
    if headers is None:
        headers = {}

    # Default headers that work with most sites
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
    }
    
    # Merge headers
    merged_headers = {**default_headers, **headers}
    
    # Add Referer if missing for cross-domain requests
    if 'Referer' not in merged_headers and 'watchanimeworld' not in url:
        merged_headers['Referer'] = 'https://watchanimeworld.net/'
    
    for attempt in range(3):
        try:
            # DEBUG: Print request info
            print(f"DEBUG: Fetching {url} (attempt {attempt + 1})")
            
            async with session.get(url, headers=merged_headers, timeout=TIMEOUT) as response:
                print(f"DEBUG: Response status: {response.status}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"DEBUG: Received {len(content)} bytes")
                    return content
                elif response.status in [403, 429]:
                    # Forbidden or rate limited
                    print(f"DEBUG: Status {response.status}, waiting...")
                    await asyncio.sleep(2)
                    
                    # Try different User-Agent
                    merged_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    continue
                else:
                    print(f"DEBUG: Unexpected status {response.status}")
                    continue
                    
        except asyncio.TimeoutError:
            print(f"DEBUG: Timeout on attempt {attempt + 1}")
            if attempt == 2:
                raise
            await asyncio.sleep(1)
        except Exception as e:
            print(f"DEBUG: Error on attempt {attempt + 1}: {str(e)}")
            if attempt == 2:
                raise
            await asyncio.sleep(1)
    
    print(f"DEBUG: All attempts failed for {url}")
    return None

def get_temp_path(filename):
    """Get path in temp directory"""
    return os.path.join(TEMP_DIR, filename)

def cleanup_temp(file_path):
    """Cleanup temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"DEBUG: Cleaned up {file_path}")
    except Exception as e:
        print(f"DEBUG: Failed to cleanup {file_path}: {str(e)}")
