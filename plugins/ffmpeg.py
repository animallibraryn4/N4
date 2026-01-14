import os
import asyncio
import subprocess
from typing import Optional
from config import FFMPEG_PATH, VIDEO_CODEC, AUDIO_CODEC
from plugins.utils import get_temp_path, cleanup_temp

class FFmpegProcessor:
    @staticmethod
    async def process_video(input_path: str, output_path: str = None) -> dict:
        """
        Process video file
        Currently does minimal processing - just ensures proper format
        """
        try:
            if not os.path.exists(input_path):
                return {"error": "Input file not found"}
            
            # If no output path specified, create one
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = get_temp_path(f"processed_{os.path.basename(base)}.mp4")
            
            # Clean up if exists
            cleanup_temp(output_path)
            
            # Simple copy for now (can be extended for multi-audio, subtitles)
            cmd = [
                FFMPEG_PATH,
                '-i', input_path,
                '-c:v', 'copy',  # Copy video codec
                '-c:a', 'aac',   # Convert audio to AAC
                '-b:a', '192k',  # Audio bitrate
                output_path,
                '-y'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {"error": f"FFmpeg processing failed: {stderr.decode()[:200]}"}
            
            # Check output
            if not os.path.exists(output_path):
                return {"error": "Processed file not created"}
            
            return {
                "success": True,
                "output_path": output_path,
                "input_path": input_path
            }
            
        except Exception as e:
            return {"error": f"Processing error: {str(e)}"}
    
    @staticmethod
    async def get_video_info(file_path: str) -> dict:
        """Get video information using FFprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {"error": "Failed to get video info"}
            
            import json
            info = json.loads(stdout.decode())
            
            return {
                "success": True,
                "info": info,
                "duration": float(info.get('format', {}).get('duration', 0)),
                "size": int(info.get('format', {}).get('size', 0))
            }
            
        except Exception as e:
            return {"error": f"Info error: {str(e)}"}
