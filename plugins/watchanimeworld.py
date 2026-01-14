import re
import json
import aiohttp
from bs4 import BeautifulSoup
from plugins.utils import fetch_url
from config import USER_AGENT

class WatchAnimeWorldScraper:
    def __init__(self):
        self.session = None
        self.base_domain = "watchanimeworld.net"
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    # ==================== CORE FUNCTION ====================
    async def scrape_episode(self, url):
        """Main scraping function with direct API approach"""
        try:
            print(f"DEBUG: Starting scrape for {url}")
            
            # 1️⃣ Fetch episode page
            html = await fetch_url(self.session, url)
            if not html:
                return {"error": "Failed to fetch episode page"}
            
            soup = BeautifulSoup(html, 'lxml')
            
            # 2️⃣ Extract ZephyrFlick iframe URL
            iframe_url = None
            iframes = soup.find_all('iframe')
            
            for iframe in iframes:
                src = iframe.get('src', '')
                if src and 'zephyrflick' in src.lower():
                    iframe_url = src
                    break
            
            if not iframe_url:
                # Try to find any video iframe
                for iframe in iframes:
                    src = iframe.get('src', '')
                    if src and ('play.' in src.lower() or 'video.' in src.lower()):
                        iframe_url = src
                        break
            
            if not iframe_url:
                return {"error": "No video iframe found"}
            
            print(f"DEBUG: Found iframe URL: {iframe_url}")
            
            # 3️⃣ Extract video ID from iframe URL
            video_id = self.extract_video_id(iframe_url)
            if not video_id:
                return {"error": f"Could not extract video ID from: {iframe_url}"}
            
            print(f"DEBUG: Extracted video ID: {video_id}")
            
            # 4️⃣ Try multiple methods to get video URL
            video_data = await self.get_video_url_by_id(video_id, url)
            if "error" in video_data:
                # Try alternative methods
                video_data = await self.get_video_url_direct(iframe_url, url)
            
            if "error" in video_data:
                return video_data
            
            # 5️⃣ Extract episode info
            episode_info = self.extract_episode_info(soup)
            
            # ✅ SUCCESS
            return {
                "success": True,
                "episode_info": episode_info,
                "player_data": video_data,
                "source_url": url,
                "method": "direct_api"
            }
            
        except Exception as e:
            print(f"DEBUG: Scraping failed with error: {str(e)}")
            return {"error": f"Scraping failed: {str(e)}"}
    
    # ==================== VIDEO ID EXTRACTION ====================
    def extract_video_id(self, iframe_url):
        """Extract video ID from iframe URL"""
        patterns = [
            r'/video/([a-zA-Z0-9]+)',
            r'v=([a-zA-Z0-9]+)',
            r'id=([a-zA-Z0-9]+)',
            r'embed/([a-zA-Z0-9]+)',
            r'/([a-zA-Z0-9]{20,})',  # Long alphanumeric IDs
        ]
        
        for pattern in patterns:
            match = re.search(pattern, iframe_url)
            if match:
                return match.group(1)
        
        return None
    
    # ==================== METHOD 1: DIRECT API CALL ====================
    async def get_video_url_by_id(self, video_id, referer):
        """Get video URL by calling ZephyrFlick API directly"""
        try:
            # Common ZephyrFlick API endpoints
            api_endpoints = [
                f"https://play.zephyrflick.top/api/video/{video_id}",
                f"https://play.zephyrflick.top/api/player/{video_id}",
                f"https://play.zephyrflick.top/api/source/{video_id}",
                f"https://play.zephyrflick.top/embed/{video_id}",
                f"https://play.zephyrflick.top/v/{video_id}",
            ]
            
            headers = {
                'User-Agent': USER_AGENT,
                'Referer': 'https://watchanimeworld.net/',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://play.zephyrflick.top',
                'X-Requested-With': 'XMLHttpRequest',
            }
            
            for api_url in api_endpoints:
                print(f"DEBUG: Trying API endpoint: {api_url}")
                
                try:
                    async with self.session.get(api_url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            content_type = response.headers.get('Content-Type', '')
                            
                            if 'application/json' in content_type:
                                data = await response.json()
                                print(f"DEBUG: API response: {json.dumps(data, indent=2)[:200]}...")
                                
                                # Parse JSON response
                                video_url = self.extract_url_from_json(data)
                                if video_url:
                                    return {
                                        "type": "m3u8" if '.m3u8' in video_url.lower() else "mp4",
                                        "url": video_url,
                                        "referer": referer,
                                        "quality": "auto"
                                    }
                            else:
                                # HTML response, try to extract from it
                                html = await response.text()
                                soup = BeautifulSoup(html, 'lxml')
                                
                                # Try to find video sources in the HTML
                                video_url = await self.extract_from_html_response(soup)
                                if video_url:
                                    return {
                                        "type": "m3u8" if '.m3u8' in video_url.lower() else "mp4",
                                        "url": video_url,
                                        "referer": referer,
                                        "quality": "auto"
                                    }
                                
                except Exception as e:
                    print(f"DEBUG: API call failed for {api_url}: {str(e)}")
                    continue
            
            return {"error": "All API endpoints failed"}
            
        except Exception as e:
            print(f"DEBUG: API method error: {str(e)}")
            return {"error": f"API method failed: {str(e)}"}
    
    def extract_url_from_json(self, data):
        """Extract video URL from JSON response"""
        try:
            # Try different JSON structures
            if isinstance(data, dict):
                # Direct URL
                if data.get("url") and ('.m3u8' in data["url"].lower() or '.mp4' in data["url"].lower()):
                    return data["url"]
                
                if data.get("file") and ('.m3u8' in data["file"].lower() or '.mp4' in data["file"].lower()):
                    return data["file"]
                
                if data.get("source") and ('.m3u8' in data["source"].lower() or '.mp4' in data["source"].lower()):
                    return data["source"]
                
                # Sources array
                if data.get("sources") and isinstance(data["sources"], list):
                    for source in data["sources"]:
                        if source.get("file") and ('.m3u8' in source["file"].lower() or '.mp4' in source["file"].lower()):
                            return source["file"]
                
                # Data field
                if data.get("data"):
                    if isinstance(data["data"], str):
                        # Try to find URL in string
                        url_match = re.search(r'(https?://[^\s"\']+\.(?:m3u8|mp4)[^\s"\']*)', data["data"])
                        if url_match:
                            return url_match.group(1)
            
            return None
        except:
            return None
    
    async def extract_from_html_response(self, soup):
        """Extract video URL from HTML API response"""
        try:
            # Look for script tags with video data
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Look for JW Player
                if 'jwplayer(' in script_text:
                    jw_pattern = r'jwplayer\([^)]+\)\.setup\((\{.*?\})\);'
                    match = re.search(jw_pattern, script_text, re.DOTALL)
                    if match:
                        try:
                            config = json.loads(match.group(1))
                            if config.get("sources"):
                                for source in config["sources"]:
                                    if source.get("file"):
                                        return source["file"]
                        except:
                            pass
                
                # Look for video.js
                if 'videojs(' in script_text:
                    sources_pattern = r'sources\s*:\s*\[(.*?)\]'
                    match = re.search(sources_pattern, script_text, re.DOTALL)
                    if match:
                        sources_text = match.group(1)
                        url_match = re.search(r'["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', sources_text)
                        if url_match:
                            return url_match.group(1)
            
            # Look for video tags
            video_tags = soup.find_all('video')
            for video in video_tags:
                sources = video.find_all('source')
                for source in sources:
                    src = source.get('src')
                    if src and ('.m3u8' in src.lower() or '.mp4' in src.lower()):
                        return src
            
            return None
        except Exception as e:
            print(f"DEBUG: HTML extraction error: {str(e)}")
            return None
    
    # ==================== METHOD 2: DIRECT IFRAME FETCH ====================
    async def get_video_url_direct(self, iframe_url, referer):
        """Try to fetch iframe directly with bypass headers"""
        try:
            print(f"DEBUG: Trying direct iframe fetch: {iframe_url}")
            
            # Use browser-like headers to bypass anti-bot
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': referer,
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'iframe',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
            }
            
            async with self.session.get(iframe_url, headers=headers, timeout=15) as response:
                print(f"DEBUG: Direct fetch status: {response.status}")
                
                if response.status == 200:
                    html = await response.text()
                    print(f"DEBUG: Received {len(html)} bytes from iframe")
                    
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Try to extract video URL
                    video_url = await self.extract_from_html_response(soup)
                    if video_url:
                        return {
                            "type": "m3u8" if '.m3u8' in video_url.lower() else "mp4",
                            "url": video_url,
                            "referer": iframe_url,
                            "quality": "auto"
                        }
                    
                    # Try to find in scripts
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if not script.string:
                            continue
                        
                        # Look for m3u8 URL
                        m3u8_pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                        match = re.search(m3u8_pattern, script.string)
                        if match:
                            return {
                                "type": "m3u8",
                                "url": match.group(1),
                                "referer": iframe_url,
                                "quality": "auto"
                            }
                
                elif response.status == 403:
                    return {"error": "Access forbidden (403). Site is blocking requests."}
                elif response.status == 404:
                    return {"error": "Video not found (404)."}
                else:
                    return {"error": f"HTTP {response.status} from iframe"}
            
            return {"error": "Direct fetch failed"}
            
        except Exception as e:
            print(f"DEBUG: Direct fetch error: {str(e)}")
            return {"error": f"Direct fetch failed: {str(e)}"}
    
    # ==================== EPISODE INFO ====================
    def extract_episode_info(self, soup):
        """Extract episode title and info"""
        try:
            title_selectors = [
                'h1.entry-title', 'h1.title', 'h1',
                '.episode-title', '.video-title', 'title'
            ]
            
            title = "Unknown Episode"
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    title = element.text.strip()
                    break
            
            # Clean title
            title = re.sub(r'\s*\|\s*.*$', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Episode number
            episode_num = "01"
            ep_match = re.search(r'Episode\s*(\d+)', title, re.IGNORECASE)
            if ep_match:
                episode_num = ep_match.group(1).zfill(2)
            
            # Clean filename
            cleaned = self.clean_filename(title)
            
            return {
                "title": title,
                "cleaned_title": cleaned,
                "episode_number": episode_num
            }
        except:
            return {
                "title": "Episode",
                "cleaned_title": "episode",
                "episode_number": "01"
            }
    
    def clean_filename(self, text):
        """Create safe filename"""
        if not text:
            return "episode"
        
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        text = re.sub(r'[^\w\s\-.,!&]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()[:80]
