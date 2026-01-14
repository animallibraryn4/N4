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
        """Main scraping function - optimized for ZephyrFlick"""
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
                return {"error": "No ZephyrFlick iframe found"}
            
            print(f"DEBUG: Found iframe URL: {iframe_url}")
            
            # 3️⃣ Fetch and parse the embed page directly
            embed_url = iframe_url.replace('/video/', '/embed/')
            print(f"DEBUG: Trying embed URL: {embed_url}")
            
            video_data = await self.parse_embed_page(embed_url, url)
            if "error" in video_data:
                # Fallback to original iframe URL
                print(f"DEBUG: Embed failed, trying original iframe")
                video_data = await self.parse_embed_page(iframe_url, url)
            
            if "error" in video_data:
                return video_data
            
            # 4️⃣ Extract episode info
            episode_info = self.extract_episode_info(soup)
            
            # ✅ SUCCESS
            return {
                "success": True,
                "episode_info": episode_info,
                "player_data": video_data,
                "source_url": url,
                "method": "embed_parser"
            }
            
        except Exception as e:
            print(f"DEBUG: Scraping failed with error: {str(e)}")
            return {"error": f"Scraping failed: {str(e)}"}
    
    # ==================== EMBED PAGE PARSER ====================
    async def parse_embed_page(self, embed_url, referer):
        """Parse ZephyrFlick embed page to extract video URL"""
        try:
            # Headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': referer,
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'iframe',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
            }
            
            print(f"DEBUG: Fetching embed page: {embed_url}")
            async with self.session.get(embed_url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    return {"error": f"Embed page returned {response.status}"}
                
                html = await response.text()
                print(f"DEBUG: Received {len(html)} bytes from embed page")
                
                # Save for debugging
                with open('debug_embed.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"DEBUG: Saved embed HTML to debug_embed.html")
                
                soup = BeautifulSoup(html, 'lxml')
                
                # METHOD 1: Look for video source in scripts
                video_url = await self.extract_from_embed_scripts(soup, embed_url)
                if video_url:
                    print(f"DEBUG: Found video URL in scripts: {video_url[:100]}...")
                    return {
                        "type": "m3u8" if '.m3u8' in video_url.lower() else "mp4",
                        "url": video_url,
                        "referer": embed_url,
                        "quality": "auto"
                    }
                
                # METHOD 2: Look for video element
                video_url = await self.extract_from_video_element(soup, embed_url)
                if video_url:
                    print(f"DEBUG: Found video URL in video element: {video_url[:100]}...")
                    return {
                        "type": "m3u8" if '.m3u8' in video_url.lower() else "mp4",
                        "url": video_url,
                        "referer": embed_url,
                        "quality": "auto"
                    }
                
                # METHOD 3: Look for iframe within embed (nested)
                video_url = await self.extract_from_nested_iframe(soup, embed_url)
                if video_url:
                    print(f"DEBUG: Found video URL in nested iframe: {video_url[:100]}...")
                    return {
                        "type": "m3u8" if '.m3u8' in video_url.lower() else "mp4",
                        "url": video_url,
                        "referer": embed_url,
                        "quality": "auto"
                    }
                
                # METHOD 4: Try to find any video URL in the entire HTML
                video_url = self.find_any_video_url(html)
                if video_url:
                    print(f"DEBUG: Found video URL in raw HTML: {video_url[:100]}...")
                    return {
                        "type": "m3u8" if '.m3u8' in video_url.lower() else "mp4",
                        "url": video_url,
                        "referer": embed_url,
                        "quality": "auto"
                    }
                
                print(f"DEBUG: Could not find video URL in embed page")
                print(f"DEBUG: First 500 chars of HTML: {html[:500]}")
                return {"error": "Could not extract video URL from embed page"}
                
        except Exception as e:
            print(f"DEBUG: Embed parsing failed: {str(e)}")
            return {"error": f"Embed parsing failed: {str(e)}"}
    
    async def extract_from_embed_scripts(self, soup, referer):
        """Extract video URL from scripts in embed page"""
        try:
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Pattern 1: Look for m3u8 URLs
                m3u8_patterns = [
                    r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
                    r'["\'](//[^"\']+\.m3u8)["\']',
                    r'file\s*[=:]\s*["\']([^"\']+\.m3u8)["\']',
                    r'src\s*[=:]\s*["\']([^"\']+\.m3u8)["\']',
                    r'url\s*[=:]\s*["\']([^"\']+\.m3u8)["\']',
                ]
                
                for pattern in m3u8_patterns:
                    matches = re.findall(pattern, script_text, re.IGNORECASE)
                    for match in matches:
                        url = match if isinstance(match, str) else match[0]
                        if url:
                            if url.startswith('//'):
                                url = f"https:{url}"
                            return url
                
                # Pattern 2: Look for JW Player configuration
                if 'jwplayer(' in script_text:
                    jw_pattern = r'jwplayer\([^)]+\)\.setup\((\{.*?\})\);'
                    match = re.search(jw_pattern, script_text, re.DOTALL)
                    if match:
                        try:
                            config = json.loads(match.group(1))
                            if config.get("sources"):
                                for source in config["sources"]:
                                    if source.get("file") and ('.m3u8' in source["file"].lower() or '.mp4' in source["file"].lower()):
                                        return source["file"]
                        except:
                            pass
                
                # Pattern 3: Look for video.js configuration
                if 'videojs(' in script_text:
                    sources_pattern = r'sources\s*:\s*\[(.*?)\]'
                    match = re.search(sources_pattern, script_text, re.DOTALL)
                    if match:
                        sources_text = match.group(1)
                        url_match = re.search(r'["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', sources_text)
                        if url_match:
                            return url_match.group(1)
            
            return None
        except Exception as e:
            print(f"DEBUG: Script extraction error: {str(e)}")
            return None
    
    async def extract_from_video_element(self, soup, referer):
        """Extract video URL from video elements"""
        try:
            video_tags = soup.find_all('video')
            
            for video in video_tags:
                # Check source tags
                sources = video.find_all('source')
                for source in sources:
                    src = source.get('src')
                    if src and ('.m3u8' in src.lower() or '.mp4' in src.lower()):
                        if src.startswith('//'):
                            src = f"https:{src}"
                        return src
                
                # Check video src directly
                src = video.get('src')
                if src and ('.m3u8' in src.lower() or '.mp4' in src.lower()):
                    if src.startswith('//'):
                        src = f"https:{src}"
                    return src
            
            return None
        except Exception as e:
            print(f"DEBUG: Video element extraction error: {str(e)}")
            return None
    
    async def extract_from_nested_iframe(self, soup, referer):
        """Extract from nested iframes within embed"""
        try:
            iframes = soup.find_all('iframe')
            
            for iframe in iframes:
                src = iframe.get('src')
                if src:
                    # This is a nested iframe, try to fetch it
                    if src.startswith('//'):
                        src = f"https:{src}"
                    elif src.startswith('/'):
                        src = f"https://play.zephyrflick.top{src}"
                    
                    print(f"DEBUG: Found nested iframe: {src}")
                    
                    # Fetch nested iframe
                    headers = {
                        'User-Agent': USER_AGENT,
                        'Referer': referer,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    }
                    
                    try:
                        async with self.session.get(src, headers=headers, timeout=10) as nested_response:
                            if nested_response.status == 200:
                                nested_html = await nested_response.text()
                                nested_soup = BeautifulSoup(nested_html, 'lxml')
                                
                                # Look for video in nested iframe
                                video_url = await self.extract_from_video_element(nested_soup, src)
                                if video_url:
                                    return video_url
                                
                                # Look for scripts in nested iframe
                                video_url = await self.extract_from_embed_scripts(nested_soup, src)
                                if video_url:
                                    return video_url
                    except:
                        continue
            
            return None
        except Exception as e:
            print(f"DEBUG: Nested iframe extraction error: {str(e)}")
            return None
    
    def find_any_video_url(self, html):
        """Find any video URL in raw HTML"""
        try:
            # Look for any video URL pattern
            patterns = [
                r'(https?://[^\s"\']+\.(?:m3u8|mp4|mkv|webm)[^\s"\']*)',
                r'["\'](//[^"\']+\.(?:m3u8|mp4|mkv|webm))["\']',
                r'file\s*[=:]\s*["\']([^"\']+\.(?:m3u8|mp4|mkv|webm))["\']',
                r'src\s*[=:]\s*["\']([^"\']+\.(?:m3u8|mp4|mkv|webm))["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    url = match if isinstance(match, str) else match[0]
                    if url:
                        if url.startswith('//'):
                            url = f"https:{url}"
                        return url
            
            return None
        except Exception as e:
            print(f"DEBUG: Raw HTML extraction error: {str(e)}")
            return None
    
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
