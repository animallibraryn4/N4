import os
import re
import random
import string
import requests
import subprocess
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

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
    }
}
'''

def extract_anime_info(title: str) -> Optional[Dict]:
    """Extract information from anime title"""
    # Multiple patterns to handle different title formats
    patterns = [
        r"\[SubsPlease\] (.+?) - (\d+)(?:v\d+)?(?: \((\d+p)\))? \[.+?\]",
        r"\[SubsPlease\] (.+?) (\d+)(?: \(\d+p\))? \[.+?\]",
        r"\[SubsPlease\] (.+?) - (\d+)(?:\.\d+)?(?: \(\d+p\))?",
    ]
    
    for pattern in patterns:
        match = re.match(pattern, title)
        if match:
            anime_name = match.group(1).strip()
            episode = match.group(2)
            quality = match.group(3) if len(match.groups()) > 2 else "Unknown"
            
            # Check for season marker
            season_match = re.search(r"S(\d+)", anime_name)
            if season_match:
                season = season_match.group(1)
                display_name = re.sub(r'S\d+', f'Season {season}', anime_name)
                search_query = re.sub(r'S\d+', f'Season {season}', anime_name)
            else:
                display_name = anime_name
                search_query = anime_name
            
            return {
                "display_name": display_name,
                "search_query": search_query,
                "episode": episode,
                "quality": quality,
                "original_title": title
            }
    
    logger.warning(f"Could not parse title: {title}")
    return None

def get_anime_details(anime_name: str) -> Dict:
    """Get anime details from AniList API"""
    try:
        # Clean the anime name for better search
        cleaned_name = re.sub(r'Season \d+', '', anime_name).strip()
        cleaned_name = re.sub(r'S\d+', '', cleaned_name).strip()
        
        variables = {'search': cleaned_name}
        response = requests.post(
            'https://graphql.anilist.co',
            json={'query': ANIME_QUERY, 'variables': variables},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            media = data.get('data', {}).get('Media', {})
            
            title = media.get('title', {})
            return {
                "name": title.get('english') or title.get('romaji') or anime_name,
                "status": media.get('status', 'Unknown'),
                "image": media.get('coverImage', {}).get('extraLarge')
            }
        else:
            logger.error(f"AniList API error: {response.status_code}")
    
    except Exception as e:
        logger.error(f"Error fetching anime details: {e}")
    
    return {
        "name": anime_name,
        "status": "Unknown",
        "image": None
    }

def generate_random_hash(length: int = 20) -> str:
    """Generate a random hash string"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def encode_video_file(input_path: str) -> Optional[str]:
    """Encode video file to compressed format"""
    try:
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return None
        
        # Extract filename without extension
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"./downloads/{base_name}_encoded.mp4"
        
        # Clean output path if it already exists
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # Build FFmpeg command
        command = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "libx264",
            "-crf", "23",  # Good quality to size ratio
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",  # Overwrite output file
            output_path
        ]
        
        logger.info(f"Encoding video: {input_path}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            logger.info(f"Video encoded successfully: {output_path}")
            return output_path
        else:
            logger.error(f"Encoding failed: {result.stderr}")
            return None
    
    except Exception as e:
        logger.error(f"Error encoding video: {e}")
        return None

def progress_callback(current: int, total: int):
    """Progress callback for uploads/downloads"""
    if total > 0:
        percentage = (current / total) * 100
        logger.debug(f"Progress: {percentage:.1f}%")
