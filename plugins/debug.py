import aiohttp
from bs4 import BeautifulSoup
from config import USER_AGENT

async def debug_url(url):
    """Debug function to see what's on the page"""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()
    
    soup = BeautifulSoup(html, 'lxml')
    
    print("\n" + "="*50)
    print(f"DEBUGGING: {url}")
    print("="*50)
    
    # Find all iframes
    iframes = soup.find_all('iframe')
    print(f"\nFound {len(iframes)} iframes:")
    for i, iframe in enumerate(iframes, 1):
        print(f"  {i}. src: {iframe.get('src', 'NO SRC')}")
        print(f"     id: {iframe.get('id', 'NO ID')}")
        print(f"     class: {iframe.get('class', 'NO CLASS')}")
    
    # Find video tags
    videos = soup.find_all('video')
    print(f"\nFound {len(videos)} video tags:")
    for i, video in enumerate(videos, 1):
        print(f"  {i}. src: {video.get('src', 'NO SRC')}")
        sources = video.find_all('source')
        for j, source in enumerate(sources, 1):
            print(f"     source {j}: {source.get('src', 'NO SRC')}")
    
    # Find player divs
    player_keywords = ['player', 'video', 'stream', 'embed']
    player_divs = []
    for div in soup.find_all('div'):
        classes = div.get('class', [])
        if isinstance(classes, str):
            classes = [classes]
        if any(keyword in ' '.join(classes).lower() for keyword in player_keywords):
            player_divs.append(div)
    
    print(f"\nFound {len(player_divs)} player divs:")
    for i, div in enumerate(player_divs[:5], 1):  # Show first 5
        print(f"  {i}. class: {div.get('class')}")
        print(f"     id: {div.get('id')}")
        if div.get('data-video-src'):
            print(f"     data-video-src: {div.get('data-video-src')}")
    
    # Find important scripts
    scripts = soup.find_all('script')
    print(f"\nFound {len(scripts)} script tags")
    
    # Look for video URLs in scripts
    video_urls = []
    for script in scripts:
        if script.string:
            import re
            urls = re.findall(r'https?://[^\s"\']+\.(?:m3u8|mp4|mkv|webm)[^\s"\']*', script.string)
            video_urls.extend(urls)
    
    print(f"\nFound {len(video_urls)} video URLs in scripts:")
    for url in video_urls[:10]:  # Show first 10
        print(f"  - {url}")
    
    return {
        'iframes': len(iframes),
        'videos': len(videos),
        'player_divs': len(player_divs),
        'video_urls_in_scripts': len(video_urls)
    }

# To run debug:
# python -c "import asyncio; from plugins.debug import debug_url; asyncio.run(debug_url('https://watchanimeworld.net/episode/gachiakuta-1x1/'))"
