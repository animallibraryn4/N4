from pyrogram import Client, filters
from pyrogram.types import Message
import re
import json
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from plugins.utils import is_valid_url, extract_domain
from database import db
from plugins.debug import debug_url
import asyncio

@Client.on_message(filters.command("test_api") & filters.private)
async def test_api_command(client, message: Message):
    """Test direct API approach"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /test_api <url>")
        return
    
    url = message.command[1]
    msg = await message.reply_text(f"🔍 Testing direct API method on {url}...")
    
    try:
        # Manual test to see what's happening
        import aiohttp
        from bs4 import BeautifulSoup
        
        async with aiohttp.ClientSession() as session:
            # Fetch episode page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://watchanimeworld.net/'
            }
            
            async with session.get(url, headers=headers) as response:
                html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Find iframe
            iframes = soup.find_all('iframe')
            video_iframe = None
            
            for iframe in iframes:
                src = iframe.get('src', '')
                if src and 'zephyrflick' in src.lower():
                    video_iframe = src
                    break
            
            if not video_iframe:
                await msg.edit_text("❌ No ZephyrFlick iframe found")
                return
            
            # Extract video ID
            import re
            video_id_match = re.search(r'/video/([a-zA-Z0-9]+)', video_iframe)
            
            if not video_id_match:
                await msg.edit_text(f"❌ Could not extract video ID from: {video_iframe}")
                return
            
            video_id = video_id_match.group(1)
            
            # Try different API endpoints
            api_endpoints = [
                f"https://play.zephyrflick.top/api/video/{video_id}",
                f"https://play.zephyrflick.top/api/player/{video_id}",
                f"https://play.zephyrflick.top/api/source/{video_id}",
                f"https://play.zephyrflick.top/embed/{video_id}",
            ]
            
            results = []
            for api_url in api_endpoints:
                try:
                    api_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://watchanimeworld.net/',
                        'Accept': 'application/json, text/plain, */*',
                    }
                    
                    async with session.get(api_url, headers=api_headers, timeout=10) as api_response:
                        status = api_response.status
                        content_type = api_response.headers.get('Content-Type', '')
                        
                        if status == 200:
                            if 'application/json' in content_type:
                                data = await api_response.json()
                                results.append(f"✅ {api_url}\n   Status: {status}\n   Type: JSON\n   Data: {str(data)[:100]}...")
                            else:
                                text = await api_response.text()
                                results.append(f"✅ {api_url}\n   Status: {status}\n   Type: {content_type}\n   Length: {len(text)} chars")
                        else:
                            results.append(f"❌ {api_url}\n   Status: {status}")
                            
                except Exception as e:
                    results.append(f"❌ {api_url}\n   Error: {str(e)}")
            
            # Also try to fetch iframe directly
            try:
                iframe_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': url,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                
                async with session.get(video_iframe, headers=iframe_headers, timeout=10) as iframe_response:
                    iframe_status = iframe_response.status
                    if iframe_status == 200:
                        iframe_html = await iframe_response.text()
                        results.append(f"\n📺 Iframe Direct:\n   Status: {iframe_status}\n   Length: {len(iframe_html)} chars")
                    else:
                        results.append(f"\n📺 Iframe Direct:\n   Status: {iframe_status}")
            except Exception as e:
                results.append(f"\n📺 Iframe Direct:\n   Error: {str(e)}")
            
            # Send results
            response_text = (
                f"🔍 **Test Results**\n\n"
                f"📺 Iframe URL: {video_iframe}\n"
                f"🎬 Video ID: {video_id}\n\n"
                f"**API Tests:**\n{chr(10).join(results)}"
            )
            
            await msg.edit_text(response_text)
            
    except Exception as e:
        await msg.edit_text(f"❌ Test failed: {str(e)}")

@Client.on_message(filters.command("test_zephyr") & filters.private)
async def test_zephyr_command(client, message: Message):
    """Test ZephyrFlick extraction specifically"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /test_zephyr <url>")
        return
    
    url = message.command[1]
    msg = await message.reply_text(f"🔍 Testing ZephyrFlick extraction on {url}")
    
    try:
        # Manual test without the class
        async with aiohttp.ClientSession() as session:
            # 1. Fetch episode page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://watchanimeworld.net/'
            }
            
            async with session.get(url, headers=headers) as response:
                html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            # 2. Find iframes
            iframes = soup.find_all('iframe')
            iframe_info = []
            
            for i, iframe in enumerate(iframes, 1):
                src = iframe.get('src', 'NO SRC')
                iframe_info.append(f"{i}. {src[:80]}...")
            
            # 3. Find player divs
            player_divs = []
            for div in soup.find_all('div'):
                classes = div.get('class', [])
                if isinstance(classes, str):
                    classes = [classes]
                if any(keyword in ' '.join(classes).lower() for keyword in ['player', 'video', 'stream']):
                    player_divs.append(div)
            
            # 4. Send detailed info
            await msg.edit_text(
                f"📊 Page Analysis:\n\n"
                f"📺 Iframes found: {len(iframes)}\n"
                f"{chr(10).join(iframe_info[:5]) if iframe_info else 'None'}\n\n"
                f"🎬 Player divs: {len(player_divs)}\n"
                f"🔍 First player classes: {player_divs[0].get('class') if player_divs else 'None'}"
            )
            
    except Exception as e:
        await msg.edit_text(f"❌ Test failed: {str(e)}")

@Client.on_message(filters.command("debug") & filters.private)
async def debug_command(client, message: Message):
    """Debug command to test URLs"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /debug <url>")
        return
    
    url = message.command[1]
    msg = await message.reply_text(f"🔍 Debugging {url}...")
    
    try:
        result = await debug_url(url)
        await msg.edit_text(
            f"✅ Debug complete:\n"
            f"• Iframes: {result['iframes']}\n"
            f"• Video tags: {result['videos']}\n"
            f"• Player divs: {result['player_divs']}\n"
            f"• Video URLs in scripts: {result['video_urls_in_scripts']}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Debug failed: {str(e)}")

@Client.on_message(filters.command("test_scrape") & filters.private)
async def test_scrape_command(client, message: Message):
    """Test the new Meido-style scraper"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /test_scrape <url>")
        return
    
    url = message.command[1]
    msg = await message.reply_text(f"🔍 Testing new scraper on {url}")
    
    try:
        from plugins.watchanimeworld import WatchAnimeWorldScraper
        async with WatchAnimeWorldScraper() as scraper:
            result = await scraper.scrape_episode(url)
        
        if "error" in result:
            await msg.edit_text(f"❌ Error: {result['error']}")
        else:
            await msg.edit_text(
                f"✅ Success!\n\n"
                f"📺 Title: {result['episode_info']['title']}\n"
                f"🔗 m3u8 URL: {result['player_data']['url'][:80]}...\n"
                f"📊 Type: {result['player_data']['type']}\n\n"
                f"⚙️ Debug Info:\n"
                f"Episode ID: {result.get('debug', {}).get('episode_id', 'N/A')}\n"
                f"Response: {result.get('debug', {}).get('ajax_response_preview', 'N/A')}"
            )
    except Exception as e:
        await msg.edit_text(f"❌ Test failed: {str(e)}")

# Allowed domains
ALLOWED_DOMAINS = [
    "watchanimeworld.net",
    "www.watchanimeworld.net"
]

# Episode URL pattern
EPISODE_PATTERN = r'/episode/'

@Client.on_message(filters.private & ~filters.command(["start", "debug", "test_scrape"]))
async def link_handler(client, message: Message):
    """Handle incoming messages and validate URLs"""
    
    text = message.text or message.caption
    
    if not text:
        await message.reply_text("Please send a valid episode URL.")
        return
    
    # Extract URL from text
    urls = re.findall(r'https?://[^\s]+', text)
    
    if not urls:
        await message.reply_text("No valid URL found in your message.")
        return
    
    url = urls[0]
    
    # Validate URL
    if not is_valid_url(url):
        await message.reply_text("Invalid URL format.")
        return
    
    # Check domain
    domain = extract_domain(url)
    if domain not in ALLOWED_DOMAINS:
        await message.reply_text(
            f"❌ Domain not allowed.\n"
            f"Only links from watchanimeworld.net are supported."
        )
        return
    
    # Check if it's an episode URL
    if not re.search(EPISODE_PATTERN, url):
        await message.reply_text(
            "❌ This doesn't look like an episode URL.\n"
            "Please send a direct episode link (containing /episode/)."
        )
        return
    
    # Log URL reception
    db.log_action(
        user_id=message.from_user.id,
        action="url_received",
        details=f"URL: {url}"
    )
    
    # Add to queue
    from plugins.queue import add_to_queue
    await add_to_queue(client, message, url)



