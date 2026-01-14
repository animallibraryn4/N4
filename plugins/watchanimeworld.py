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
    
    async def scrape_episode(self, url):
        """Main scraping function - UPDATED for new structure"""
        try:
            # Step 1: Fetch episode page with proper headers
            headers = {
                'User-Agent': USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': f'https://{self.base_domain}/',
                'Upgrade-Insecure-Requests': '1',
            }
            
            html = await fetch_url(self.session, url, headers)
            if not html:
                return {"error": "Failed to fetch episode page"}
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Step 2: MULTIPLE METHODS to find video source
            
            # Method 1: Look for video player div with data-video-src
            video_data = await self.extract_from_player_div(soup, url)
            if video_data and "error" not in video_data:
                return self.prepare_success_response(video_data, soup, url)
            
            # Method 2: Look for iframes (old method)
            iframe_data = await self.extract_from_iframes(soup, url)
            if iframe_data and "error" not in iframe_data:
                return self.prepare_success_response(iframe_data, soup, url)
            
            # Method 3: Look for script variables
            script_data = await self.extract_from_scripts(soup, url)
            if script_data and "error" not in script_data:
                return self.prepare_success_response(script_data, soup, url)
            
            # Method 4: Look for direct video sources
            direct_data = await self.extract_direct_sources(soup, url)
            if direct_data and "error" not in direct_data:
                return self.prepare_success_response(direct_data, soup, url)
            
            # If all methods fail, try debug output
            debug_info = await self.debug_page_structure(soup, url)
            return {
                "error": f"No video source found. Debug: {debug_info}",
                "debug_html": html[:500] if len(html) > 500 else html
            }
            
        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}
    
    async def extract_from_player_div(self, soup, referer_url):
        """Extract from player container with data attributes"""
        try:
            # Look for video player container
            player_div = soup.find('div', {'id': 'load_player'})
            if not player_div:
                player_div = soup.find('div', {'class': 'player'})
            if not player_div:
                player_div = soup.find('div', {'class': 'video-player'})
            
            if player_div:
                # Check for data attributes
                if player_div.get('data-video-src'):
                    video_url = player_div['data-video-src']
                    return await self.process_video_url(video_url, referer_url)
                
                # Check for embedded script
                script_tag = player_div.find('script')
                if script_tag and script_tag.string:
                    return await self.parse_player_script(script_tag.string, referer_url)
            
            return {"error": "No player div found"}
        except Exception as e:
            return {"error": f"Player div extraction failed: {str(e)}"}
    
    async def extract_from_iframes(self, soup, referer_url):
        """Extract from iframes"""
        try:
            iframes = soup.find_all('iframe')
            
            for iframe in iframes:
                src = iframe.get('src')
                if src:
                    # Clean URL
                    if src.startswith('//'):
                        src = f"https:{src}"
                    elif src.startswith('/'):
                        src = f"https://{self.base_domain}{src}"
                    
                    # Check if it's a video iframe
                    if any(keyword in src.lower() for keyword in ['video', 'player', 'stream', 'embed']):
                        # Fetch iframe content
                        iframe_headers = {
                            'User-Agent': USER_AGENT,
                            'Referer': referer_url
                        }
                        
                        iframe_html = await fetch_url(self.session, src, iframe_headers)
                        if iframe_html:
                            iframe_soup = BeautifulSoup(iframe_html, 'lxml')
                            
                            # Look for video sources in iframe
                            source_tags = iframe_soup.find_all('source')
                            for source in source_tags:
                                src_url = source.get('src')
                                if src_url:
                                    result = await self.process_video_url(src_url, src)
                                    if "error" not in result:
                                        return result
                            
                            # Look for m3u8 in iframe scripts
                            scripts = iframe_soup.find_all('script')
                            for script in scripts:
                                if script.string:
                                    m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', script.string)
                                    if m3u8_match:
                                        m3u8_url = m3u8_match.group(1)
                                        return {
                                            "type": "m3u8",
                                            "url": m3u8_url,
                                            "referer": src,
                                            "quality": "auto"
                                        }
            
            return {"error": "No video iframes found"}
        except Exception as e:
            return {"error": f"Iframe extraction failed: {str(e)}"}
    
    async def extract_from_scripts(self, soup, referer_url):
        """Extract video URLs from JavaScript variables"""
        try:
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Pattern 1: Look for video URL variables
                patterns = [
                    r'video_url\s*[=:]\s*["\'](https?://[^"\']+)["\']',
                    r'videoUrl\s*[=:]\s*["\'](https?://[^"\']+)["\']',
                    r'src\s*[=:]\s*["\'](https?://[^"\']+)["\']',
                    r'file\s*[=:]\s*["\'](https?://[^"\']+)["\']',
                    r'["\'](https?://[^"\']+\.(?:m3u8|mp4|mkv|webm)[^"\']*)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, script_text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]
                        
                        if any(ext in match.lower() for ext in ['.m3u8', '.mp4', '.mkv', '.webm']):
                            return await self.process_video_url(match, referer_url)
            
            return {"error": "No video URLs in scripts"}
        except Exception as e:
            return {"error": f"Script extraction failed: {str(e)}"}
    
    async def extract_direct_sources(self, soup, referer_url):
        """Extract direct video source tags"""
        try:
            # Look for video tags
            video_tags = soup.find_all('video')
            for video in video_tags:
                # Check source tags inside video
                source_tags = video.find_all('source')
                for source in source_tags:
                    src = source.get('src')
                    if src:
                        return await self.process_video_url(src, referer_url)
                
                # Check src attribute directly on video tag
                if video.get('src'):
                    return await self.process_video_url(video['src'], referer_url)
            
            return {"error": "No direct video sources"}
        except Exception as e:
            return {"error": f"Direct source extraction failed: {str(e)}"}
    
    async def process_video_url(self, video_url, referer_url):
        """Process and validate video URL"""
        try:
            # Clean URL
            if video_url.startswith('//'):
                video_url = f"https:{video_url}"
            elif video_url.startswith('/'):
                video_url = f"https://{self.base_domain}{video_url}"
            
            # Determine type
            if '.m3u8' in video_url.lower():
                video_type = "m3u8"
            elif '.mp4' in video_url.lower():
                video_type = "mp4"
            elif any(ext in video_url.lower() for ext in ['.mkv', '.webm', '.avi']):
                video_type = "direct"
            else:
                # Try to detect by checking headers
                try:
                    headers = {'User-Agent': USER_AGENT, 'Referer': referer_url}
                    async with self.session.head(video_url, headers=headers, timeout=5) as resp:
                        content_type = resp.headers.get('Content-Type', '')
                        if 'application/vnd.apple.mpegurl' in content_type or 'mpegurl' in content_type:
                            video_type = "m3u8"
                        elif 'video/mp4' in content_type:
                            video_type = "mp4"
                        else:
                            video_type = "unknown"
                except:
                    video_type = "unknown"
            
            return {
                "type": video_type,
                "url": video_url,
                "referer": referer_url,
                "quality": "auto"
            }
            
        except Exception as e:
            return {"error": f"URL processing failed: {str(e)}"}
    
    async def parse_player_script(self, script_text, referer_url):
        """Parse player JavaScript for video data"""
        try:
            # Look for JSON-like structures
            json_patterns = [
                r'(\{.*?"sources".*?\})',
                r'(\{.*?"file".*?\})',
                r'(\{.*?"src".*?\})'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, script_text, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        
                        # Check for sources array
                        if 'sources' in data and isinstance(data['sources'], list):
                            for source in data['sources']:
                                if 'file' in source:
                                    return await self.process_video_url(source['file'], referer_url)
                        
                        # Check for direct file
                        if 'file' in data:
                            return await self.process_video_url(data['file'], referer_url)
                        if 'src' in data:
                            return await self.process_video_url(data['src'], referer_url)
                            
                    except json.JSONDecodeError:
                        continue
            
            # Look for JW Player setup
            if 'jwplayer(' in script_text:
                # Extract setup data
                setup_match = re.search(r'jwplayer\([^)]+\)\.setup\((\{.*?\})\);', script_text, re.DOTALL)
                if setup_match:
                    try:
                        setup_data = json.loads(setup_match.group(1))
                        if 'sources' in setup_data:
                            for source in setup_data['sources']:
                                if 'file' in source:
                                    return await self.process_video_url(source['file'], referer_url)
                    except:
                        pass
            
            return {"error": "Could not parse player script"}
        except Exception as e:
            return {"error": f"Script parsing failed: {str(e)}"}
    
    def extract_episode_info(self, soup):
        """Extract episode title and information"""
        try:
            # Try multiple selectors for title
            selectors = [
                'h1.entry-title',
                'h1.title',
                'h1',
                '.episode-title',
                '.video-title',
                'title'
            ]
            
            title = "Unknown Episode"
            for selector in selectors:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    title = element.text.strip()
                    break
            
            # Clean title
            title = re.sub(r'\s*\|\s*.*$', '', title)  # Remove after |
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Try to extract episode number
            episode_num = "01"
            ep_match = re.search(r'Episode\s*(\d+)', title, re.IGNORECASE)
            if ep_match:
                episode_num = ep_match.group(1).zfill(2)
            
            return {
                "title": title,
                "cleaned_title": self.clean_filename(title),
                "episode_number": episode_num
            }
        except:
            return {
                "title": "Episode",
                "cleaned_title": "episode",
                "episode_number": "01"
            }
    
    async def debug_page_structure(self, soup, url):
        """Debug function to see page structure"""
        try:
            debug_info = []
            
            # Count elements
            debug_info.append(f"Iframes: {len(soup.find_all('iframe'))}")
            debug_info.append(f"Video tags: {len(soup.find_all('video'))}")
            debug_info.append(f"Scripts: {len(soup.find_all('script'))}")
            
            # Check for common player divs
            player_divs = []
            for div in soup.find_all('div', {'class': True}):
                if any(keyword in div['class'] for keyword in ['player', 'video', 'stream']):
                    player_divs.append(div['class'])
            
            debug_info.append(f"Player divs: {len(player_divs)}")
            
            # Check meta tags
            meta_refresh = soup.find('meta', {'http-equiv': 'refresh'})
            if meta_refresh:
                debug_info.append("Has meta refresh")
            
            return "; ".join(debug_info)
        except:
            return "Debug failed"
    
    def clean_filename(self, text):
        """Clean text for filename"""
        # Remove invalid characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Remove special characters
        text = re.sub(r'[^\w\s\-.,!]', '', text)
        # Replace multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Trim
        return text.strip()[:100]  # Limit length
    
    def prepare_success_response(self, video_data, soup, url):
        """Prepare success response"""
        episode_info = self.extract_episode_info(soup)
        
        return {
            "success": True,
            "episode_info": episode_info,
            "player_data": video_data,
            "source_url": url
        }
