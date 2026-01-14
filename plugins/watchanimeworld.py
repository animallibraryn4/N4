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
        """Main scraping function with multiple fallbacks"""
        try:
            # Try Method 1: Direct ZephyrFlick extraction
            result = await self.scrape_direct_zephyr(url)
            if result and "error" not in result:
                return result
            
            # Try Method 2: Iframe analysis
            result = await self.scrape_via_iframe(url)
            if result and "error" not in result:
                return result
            
            # Try Method 3: Player script analysis
            result = await self.scrape_via_player_scripts(url)
            if result and "error" not in result:
                return result
            
            # All methods failed
            return {"error": "Could not extract video source. Site might be blocking requests."}
            
        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}
    
    # ==================== METHOD 1: DIRECT ZEPHYR EXTRACTION ====================
    async def scrape_direct_zephyr(self, url):
        """Direct extraction from ZephyrFlick iframe"""
        try:
            # 1. Fetch episode page
            html = await fetch_url(self.session, url)
            if not html:
                return {"error": "Failed to fetch episode page"}
            
            soup = BeautifulSoup(html, 'lxml')
            
            # 2. Find ALL iframes and analyze them
            iframes = soup.find_all('iframe')
            zephyr_url = None
            
            for iframe in iframes:
                src = iframe.get('src', '')
                if src:
                    # Check for ZephyrFlick or similar video hosts
                    video_hosts = ['zephyrflick', 'play.', 'video.', 'stream.', 'embed.']
                    if any(host in src.lower() for host in video_hosts):
                        zephyr_url = src
                        break
            
            if not zephyr_url:
                return {"error": "No video iframe found"}
            
            # 3. Fix URL format
            if zephyr_url.startswith('//'):
                zephyr_url = f"https:{zephyr_url}"
            elif zephyr_url.startswith('/'):
                zephyr_url = f"https://{self.base_domain}{zephyr_url}"
            
            print(f"DEBUG: Found iframe URL: {zephyr_url}")
            
            # 4. Try to extract video from iframe URL directly
            # Sometimes the iframe URL itself contains the video ID
            video_data = await self.extract_from_zephyr_url(zephyr_url, url)
            if video_data and "error" not in video_data:
                episode_info = self.extract_episode_info(soup)
                return {
                    "success": True,
                    "episode_info": episode_info,
                    "player_data": video_data,
                    "source_url": url,
                    "method": "direct_zephyr"
                }
            
            # 5. If direct extraction failed, try to fetch iframe content
            print(f"DEBUG: Trying to fetch iframe content: {zephyr_url}")
            headers = {
                'User-Agent': USER_AGENT,
                'Referer': url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Origin': f'https://{self.base_domain}'
            }
            
            try:
                async with self.session.get(zephyr_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        iframe_html = await response.text()
                        iframe_soup = BeautifulSoup(iframe_html, 'lxml')
                        
                        # Try to extract video from iframe content
                        video_data = await self.extract_from_iframe_content(iframe_soup, zephyr_url)
                        if video_data and "error" not in video_data:
                            episode_info = self.extract_episode_info(soup)
                            return {
                                "success": True,
                                "episode_info": episode_info,
                                "player_data": video_data,
                                "source_url": url,
                                "method": "iframe_content"
                            }
            except Exception as e:
                print(f"DEBUG: Failed to fetch iframe: {str(e)}")
            
            return {"error": "Could not extract video from ZephyrFlick"}
            
        except Exception as e:
            print(f"DEBUG: Direct Zephyr method error: {str(e)}")
            return {"error": f"Direct extraction failed: {str(e)}"}
    
    async def extract_from_zephyr_url(self, zephyr_url, referer):
        """Extract video data from ZephyrFlick URL pattern"""
        try:
            # Pattern: https://play.zephyrflick.top/video/VIDEO_ID
            # Sometimes this is a direct m3u8 or mp4
            
            # Check if URL ends with common video extensions
            if any(ext in zephyr_url.lower() for ext in ['.m3u8', '.mp4', '.mkv']):
                return {
                    "type": "m3u8" if '.m3u8' in zephyr_url.lower() else "mp4",
                    "url": zephyr_url,
                    "referer": referer,
                    "quality": "auto"
                }
            
            # Try to construct m3u8 URL from video ID
            video_id_match = re.search(r'/video/([a-zA-Z0-9]+)', zephyr_url)
            if video_id_match:
                video_id = video_id_match.group(1)
                # Try common patterns
                possible_urls = [
                    f"https://play.zephyrflick.top/videos/{video_id}/playlist.m3u8",
                    f"https://play.zephyrflick.top/{video_id}/playlist.m3u8",
                    f"https://play.zephyrflick.top/stream/{video_id}/master.m3u8",
                    f"https://play.zephyrflick.top/hls/{video_id}/index.m3u8",
                ]
                
                # Test each URL
                for test_url in possible_urls:
                    try:
                        headers = {'User-Agent': USER_AGENT, 'Referer': referer}
                        async with self.session.head(test_url, headers=headers, timeout=5) as resp:
                            if resp.status == 200:
                                return {
                                    "type": "m3u8",
                                    "url": test_url,
                                    "referer": referer,
                                    "quality": "auto"
                                }
                    except:
                        continue
            
            return {"error": "Could not extract from URL pattern"}
        except Exception as e:
            return {"error": f"URL extraction failed: {str(e)}"}
    
    async def extract_from_iframe_content(self, soup, referer):
        """Extract video from iframe content"""
        try:
            # Method 1: Look for video.js player
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Look for video source URLs
                url_patterns = [
                    r'(https?://[^"\']+\.(?:m3u8|mp4|mkv)[^"\']*)',
                    r'["\'](//[^"\']+\.(?:m3u8|mp4|mkv))["\']',
                    r'file\s*[=:]\s*["\']([^"\']+\.(?:m3u8|mp4|mkv))["\']',
                    r'src\s*[=:]\s*["\']([^"\']+\.(?:m3u8|mp4|mkv))["\']',
                    r'url\s*[=:]\s*["\']([^"\']+\.(?:m3u8|mp4|mkv))["\']',
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, script_text, re.IGNORECASE)
                    for match in matches:
                        url = match if isinstance(match, str) else match[0]
                        if url:
                            # Fix URL if needed
                            if url.startswith('//'):
                                url = f"https:{url}"
                            
                            return {
                                "type": "m3u8" if '.m3u8' in url.lower() else "mp4",
                                "url": url,
                                "referer": referer,
                                "quality": "auto"
                            }
            
            # Method 2: Look for JSON configuration
            for script in scripts:
                if not script.string:
                    continue
                
                # Try to find JSON data
                json_patterns = [
                    r'(\{.*?"sources".*?\})',
                    r'(\{.*?"file".*?\})',
                    r'(\{.*?"src".*?\})',
                    r'playerConfig\s*=\s*(\{.*?\})',
                    r'config\s*=\s*(\{.*?\})',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, script.string, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            # Check for video sources
                            if isinstance(data, dict):
                                # Sources array
                                if data.get("sources") and isinstance(data["sources"], list):
                                    for source in data["sources"]:
                                        if source.get("file"):
                                            url = source["file"]
                                            return {
                                                "type": "m3u8" if '.m3u8' in url.lower() else "mp4",
                                                "url": url,
                                                "referer": referer,
                                                "quality": source.get("label", "auto")
                                            }
                                
                                # Direct file
                                if data.get("file"):
                                    url = data["file"]
                                    return {
                                        "type": "m3u8" if '.m3u8' in url.lower() else "mp4",
                                        "url": url,
                                        "referer": referer,
                                        "quality": "auto"
                                    }
                        except json.JSONDecodeError:
                            continue
            
            # Method 3: Look for video tags
            video_tags = soup.find_all('video')
            for video in video_tags:
                # Check source tags
                sources = video.find_all('source')
                for source in sources:
                    src = source.get('src')
                    if src:
                        return {
                            "type": "m3u8" if '.m3u8' in src.lower() else "mp4",
                            "url": src,
                            "referer": referer,
                            "quality": source.get('label', 'auto')
                        }
                
                # Check video src directly
                if video.get('src'):
                    src = video.get('src')
                    return {
                        "type": "m3u8" if '.m3u8' in src.lower() else "mp4",
                        "url": src,
                        "referer": referer,
                        "quality": "auto"
                    }
            
            return {"error": "No video source found in iframe"}
            
        except Exception as e:
            return {"error": f"Iframe extraction failed: {str(e)}"}
    
    # ==================== METHOD 2: IFRAME ANALYSIS ====================
    async def scrape_via_iframe(self, url):
        """Alternative iframe analysis method"""
        try:
            html = await fetch_url(self.session, url)
            if not html:
                return {"error": "Failed to fetch page"}
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for iframes with video content
            iframes = soup.find_all('iframe')
            
            for iframe in iframes:
                src = iframe.get('src', '')
                if not src:
                    continue
                
                # Fix URL
                if src.startswith('//'):
                    src = f"https:{src}"
                
                print(f"DEBUG: Analyzing iframe: {src}")
                
                # Try to extract video from this iframe
                video_data = await self.analyze_iframe_for_video(src, url)
                if video_data and "error" not in video_data:
                    episode_info = self.extract_episode_info(soup)
                    return {
                        "success": True,
                        "episode_info": episode_info,
                        "player_data": video_data,
                        "source_url": url,
                        "method": "iframe_analysis"
                    }
            
            return {"error": "No video found in iframes"}
        except Exception as e:
            return {"error": f"Iframe analysis failed: {str(e)}"}
    
    async def analyze_iframe_for_video(self, iframe_url, referer):
        """Analyze iframe URL for video sources"""
        try:
            headers = {
                'User-Agent': USER_AGENT,
                'Referer': referer,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            async with self.session.get(iframe_url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}"}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Try multiple extraction methods
                methods = [
                    self.extract_from_scripts,
                    self.extract_from_video_tags,
                    self.extract_from_json_ld,
                ]
                
                for method in methods:
                    try:
                        result = method(soup, iframe_url)
                        if result and "error" not in result:
                            return result
                    except:
                        continue
                
                return {"error": "No video found"}
                
        except Exception as e:
            return {"error": f"Iframe analysis error: {str(e)}"}
    
    # ==================== METHOD 3: PLAYER SCRIPT ANALYSIS ====================
    async def scrape_via_player_scripts(self, url):
        """Extract from player scripts on main page"""
        try:
            html = await fetch_url(self.session, url)
            if not html:
                return {"error": "Failed to fetch page"}
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for player-related scripts
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Look for player initialization
                player_keywords = ['videojs', 'jwplayer', 'clappr', 'flowplayer', 'player']
                if any(keyword in script_text.lower() for keyword in player_keywords):
                    # Extract video URLs
                    url_patterns = [
                        r'(https?://[^"\']+\.(?:m3u8|mp4|mkv)[^"\']*)',
                        r'["\'](//[^"\']+\.(?:m3u8|mp4|mkv))["\']',
                    ]
                    
                    for pattern in url_patterns:
                        matches = re.findall(pattern, script_text, re.IGNORECASE)
                        for match in matches:
                            url_found = match if isinstance(match, str) else match[0]
                            if url_found:
                                # Fix URL
                                if url_found.startswith('//'):
                                    url_found = f"https:{url_found}"
                                
                                episode_info = self.extract_episode_info(soup)
                                return {
                                    "success": True,
                                    "episode_info": episode_info,
                                    "player_data": {
                                        "type": "m3u8" if '.m3u8' in url_found.lower() else "mp4",
                                        "url": url_found,
                                        "referer": url,
                                        "quality": "auto"
                                    },
                                    "source_url": url,
                                    "method": "player_script"
                                }
            
            return {"error": "No player scripts found"}
        except Exception as e:
            return {"error": f"Script analysis failed: {str(e)}"}
    
    # ==================== HELPER EXTRACTION METHODS ====================
    def extract_from_scripts(self, soup, referer):
        """Extract video from scripts"""
        scripts = soup.find_all('script')
        
        for script in scripts:
            if not script.string:
                continue
            
            # Look for m3u8 URLs
            m3u8_pattern = r'(https?://[^"\']+\.m3u8[^"\']*)'
            matches = re.findall(m3u8_pattern, script.string, re.IGNORECASE)
            
            for match in matches:
                if match:
                    return {
                        "type": "m3u8",
                        "url": match,
                        "referer": referer,
                        "quality": "auto"
                    }
        
        return {"error": "No video in scripts"}
    
    def extract_from_video_tags(self, soup, referer):
        """Extract video from video tags"""
        video_tags = soup.find_all('video')
        
        for video in video_tags:
            # Check source tags
            sources = video.find_all('source')
            for source in sources:
                src = source.get('src')
                if src:
                    return {
                        "type": "m3u8" if '.m3u8' in src.lower() else "mp4",
                        "url": src,
                        "referer": referer,
                        "quality": source.get('label', 'auto')
                    }
            
            # Check video src directly
            if video.get('src'):
                src = video.get('src')
                return {
                    "type": "m3u8" if '.m3u8' in src.lower() else "mp4",
                    "url": src,
                    "referer": referer,
                    "quality": "auto"
                }
        
        return {"error": "No video tags found"}
    
    def extract_from_json_ld(self, soup, referer):
        """Extract from JSON-LD structured data"""
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            if not script.string:
                continue
            
            try:
                data = json.loads(script.string)
                # Check for video content
                if isinstance(data, dict) and data.get('contentUrl'):
                    url = data['contentUrl']
                    if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.mkv']):
                        return {
                            "type": "m3u8" if '.m3u8' in url.lower() else "mp4",
                            "url": url,
                            "referer": referer,
                            "quality": "auto"
                        }
            except:
                continue
        
        return {"error": "No JSON-LD video found"}
    
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
