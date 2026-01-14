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
    """Async URL fetcher with anti-bot bypass"""
    if headers is None:
        headers = {}

    # Advanced headers that mimic real browser
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }
    
    # Merge headers
    merged_headers = {**default_headers, **headers}
    
    # Rotate User-Agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    ]
    
    for attempt in range(3):
        try:
            # Rotate User-Agent
            merged_headers['User-Agent'] = user_agents[attempt % len(user_agents)]
            
            print(f"DEBUG: Fetching {url} with User-Agent: {merged_headers['User-Agent'][:50]}...")
            
            async with session.get(url, headers=merged_headers, timeout=15) as response:
                print(f"DEBUG: Response status: {response.status}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"DEBUG: Success - {len(content)} bytes")
                    return content
                elif response.status in [403, 429]:
                    # Anti-bot detection
                    print(f"DEBUG: Blocked with status {response.status}")
                    await asyncio.sleep(3)  # Wait longer
                    continue
                else:
                    print(f"DEBUG: Unexpected status {response.status}")
                    await asyncio.sleep(1)
                    
        except asyncio.TimeoutError:
            print(f"DEBUG: Timeout on attempt {attempt + 1}")
            if attempt == 2:
                raise
            await asyncio.sleep(2)
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

