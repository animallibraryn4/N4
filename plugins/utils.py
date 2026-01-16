import re
import random
import string
import aiohttp
import subprocess
import os
import asyncio
from typing import Optional, Dict
from loguru import logger

# AniList GraphQL query
ANIME_QUERY = '''
query ($search: String) { 
    Media (type: ANIME, search: $search) { 
        title {
            english
            romaji
        }
        status
        coverImage {
            extraLarge
        }
        episodes
    }
}
'''

def extract_anime_info(title: str) -> Optional[Dict]:
    """
    Extract information from anime title
    
    Args:
        title: Anime title string
        
    Returns:
        Dictionary with extracted info or None
    """
    try:
        # Various patterns for SubsPlease releases
        patterns = [
            # Pattern 1: [SubsPlease] Show Name - Episode (Quality) [Release Info]
            r'\[SubsPlease\]\s+(.+?)\s+-\s+(\d+)\s+\((\d+p)\)\s+\[.+?\]',
            # Pattern 2: [SubsPlease] Show Name Episode (Quality) [Release Info]
            r'\[SubsPlease\]\s+(.+?)\s+(\d+)\s+\((\d+p)\)\s+\[.+?\]',
            # Pattern 3: Show Name - Episode (Quality) [SubsPlease]
            r'(.+?)\s+-\s+(\d+)\s+\((\d+p)\)\s+\[SubsPlease\]',
            # Pattern 4: Simple pattern for fallback
            r'\[SubsPlease\]\s+(.+?)\s+-?\s*(\d+)\s*[\(\[]'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                anime_name = match.group(1).strip()
                episode = match.group(2)
                quality = match.group(3) if len(match.groups()) > 2 else "1080p"
                
                # Clean anime name
                if 'Season' in anime_name:
                    parts = anime_name.split('Season')
                    base_name = parts[0].strip()
                    season = parts[1].strip()
                    display_name = f"{base_name} Season {season}"
                    search_query = f"{base_name} Season {season}"
                else:
                    display_name = anime_name
                    search_query = anime_name
                    season = None
                
                return {
                    "display_name": display_name,
                    "search_query": search_query,
                    "episode": episode,
                    "season": season,
                    "quality": quality,
                    "original_title": title
                }
        
        logger.warning(f"Could not parse title: {title}")
        
        # Fallback: extract any information we can
        if 'SubsPlease' in title:
            # Try to extract episode number
            episode_match = re.search(r'(\d{2,3})', title)
            episode = episode_match.group(1) if episode_match else "01"
            
            # Try to extract quality
            quality_match = re.search(r'(\d{3,4}p)', title, re.IGNORECASE)
            quality = quality_match.group(1) if quality_match else "1080p"
            
            # Extract name (everything before episode number)
            name_parts = title.split(str(episode))[0]
            anime_name = name_parts.replace('[SubsPlease]', '').strip(' -')
            
            return {
                "display_name": anime_name,
                "search_query": anime_name,
                "episode": episode,
                "season": None,
                "quality": quality,
                "original_title": title
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting anime info: {e}")
        return None

async def get_anime_details(anime_name: str) -> Dict:
    """
    Get anime details from AniList API asynchronously
    
    Args:
        anime_name: Name of anime to search
        
    Returns:
        Dictionary with anime details
    """
    try:
        url = 'https://graphql.anilist.co'
        variables = {'search': anime_name}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, json={'query': ANIME_QUERY, 'variables': variables}) as response:
                if response.status == 200:
                    data = await response.json()
                    media = data.get('data', {}).get('Media', {})
                    
                    title_obj = media.get('title', {})
                    name = title_obj.get('english') or title_obj.get('romaji') or anime_name
                    
                    return {
                        "name": name,
                        "status": media.get('status', 'Unknown'),
                        "image": media.get('coverImage', {}).get('extraLarge'),
                        "episodes": media.get('episodes', 0)
                    }
                else:
                    logger.error(f"AniList API error: {response.status}")
    
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching anime details for: {anime_name}")
    except Exception as e:
        logger.error(f"Error fetching anime details: {e}")
    
    # Return default values on error
    return {
        "name": anime_name,
        "status": "Unknown",
        "image": None,
        "episodes": 0
    }

def generate_random_hash(length: int = 20) -> str:
    """
    Generate a random hash string
    
    Args:
        length: Length of hash
        
    Returns:
        Random hash string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

async def encode_video_file(input_path: str) -> Optional[str]:
    """
    Encode video file to compressed format asynchronously
    
    Args:
        input_path: Path to input video file
        
    Returns:
        Path to encoded file or None if failed
    """
    try:
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return None
        
        # Extract filename without extension
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"{os.path.dirname(input_path)}/{base_name}_encoded.mp4"
        
        # Check if output already exists
        if os.path.exists(output_path):
            logger.info(f"Encoded file already exists: {output_path}")
            return output_path
        
        # Check if ffmpeg is available
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("FFmpeg not available. Skipping encoding.")
            return None
        
        # Encode video using ffmpeg
        logger.info(f"Starting encoding: {input_path}")
        
        # Basic encoding command (adjust as needed)
        command = [
            "ffmpeg", "-i", input_path,
            "-c:v", "libx264",
            "-crf", "23",  # Quality level (lower = better quality, larger file)
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
        
        # Run encoding asynchronously
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Video encoded successfully: {output_path} ({os.path.getsize(output_path) / (1024*1024):.1f} MB)")
                return output_path
            else:
                logger.error("Encoding produced empty file")
                return None
        else:
            logger.error(f"Encoding failed. Return code: {process.returncode}")
            logger.error(f"FFmpeg stderr: {stderr.decode()[:500]}")
            return None
    
    except Exception as e:
        logger.error(f"Error encoding video: {e}")
        return None

async def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available on the system"""
    try:
        result = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
