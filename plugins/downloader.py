import os
import aiohttp
import asyncio
import subprocess
from typing import Dict, Any
from plugins.utils import get_temp_path, cleanup_temp
from config import USER_AGENT, FFMPEG_PATH, TEMP_DIR

class Downloader:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def download(self, player_data: Dict[str, Any], episode_info: Dict[str, Any]):
        """Download video based on player data"""
        try:
            if player_data.get("type") == "m3u8":
                return await self.download_m3u8(player_data, episode_info)
            elif player_data.get("type") == "mp4":
                return await self.download_mp4(player_data, episode_info)
            else:
                return {"error": f"Unsupported type: {player_data.get('type')}"}
        except Exception as e:
            return {"error": f"Download failed: {str(e)}"}
    
    async def download_m3u8(self, player_data: Dict[str, Any], episode_info: Dict[str, Any]):
        """Download m3u8 using FFmpeg"""
        m3u8_url = player_data["url"]
        referer = player_data.get("referer", "")
        output_filename = f"{episode_info['cleaned_title']}.mp4"
        output_path = get_temp_path(output_filename)
        
        # Clean up if exists
        cleanup_temp(output_path)
        
        # Prepare headers for FFmpeg
        headers = f"Referer: {referer}\r\nUser-Agent: {USER_AGENT}"
        
        # FFmpeg command
        cmd = [
            FFMPEG_PATH,
            '-headers', headers,
            '-i', m3u8_url,
            '-c', 'copy',  # Copy without re-encoding
            '-bsf:a', 'aac_adtstoasc',
            output_path,
            '-y'  # Overwrite output
        ]
        
        # Run FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return {"error": f"FFmpeg failed: {stderr.decode()[:200]}"}
        
        # Check if file was created
        if not os.path.exists(output_path):
            return {"error": "Output file not created"}
        
        return {
            "success": True,
            "file_path": output_path,
            "filename": output_filename,
            "type": "m3u8"
        }
    
    async def download_mp4(self, player_data: Dict[str, Any], episode_info: Dict[str, Any]):
        """Download direct MP4"""
        mp4_url = player_data["url"]
        referer = player_data.get("referer", "")
        output_filename = f"{episode_info['cleaned_title']}.mp4"
        output_path = get_temp_path(output_filename)
        
        # Clean up if exists
        cleanup_temp(output_path)
        
        headers = {
            'Referer': referer,
            'User-Agent': USER_AGENT,
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Range': 'bytes=0-'
        }
        
        try:
            async with self.session.get(mp4_url, headers=headers, timeout=300) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}"}
                
                total_size = int(response.headers.get('content-length', 0))
                
                # Check file size
                if total_size > 2 * 1024 * 1024 * 1024:  # 2GB
                    return {"error": "File too large (max 2GB)"}
                
                # Download
                with open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                return {
                    "success": True,
                    "file_path": output_path,
                    "filename": output_filename,
                    "type": "mp4"
                }
                
        except Exception as e:
            cleanup_temp(output_path)
            return {"error": f"MP4 download failed: {str(e)}"}
