# plugins/torrent_handler_fallback.py
import logging
import subprocess
import os
import time
from typing import Optional, Dict
from pyrogram.types import Message

logger = logging.getLogger(__name__)

class TorrentHandler:
    def __init__(self):
        self.download_dir = "./downloads"
        os.makedirs(self.download_dir, exist_ok=True)
    
    def download(self, magnet_link: str, status_message: Message = None) -> Optional[Dict]:
        """
        Download torrent using aria2c (fallback method)
        """
        try:
            logger.info(f"Starting download: {magnet_link[:50]}...")
            
            if status_message:
                status_message.edit_text("📥 Starting download...")
            
            # Use aria2c for torrent downloading
            import random
            import string
            
            # Generate random filename
            file_hash = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            output_file = f"{self.download_dir}/download_{file_hash}"
            
            # Build aria2c command
            command = [
                "aria2c",
                "--seed-time=0",  # Don't seed after download
                "--max-connection-per-server=16",
                "--split=16",
                "--min-split-size=1M",
                "--continue=true",
                f"--dir={self.download_dir}",
                f"--out={file_hash}",
                magnet_link
            ]
            
            logger.info(f"Running command: {' '.join(command)}")
            
            # Execute download
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Monitor progress
            start_time = time.time()
            last_update = time.time()
            
            for line in process.stdout:
                if status_message and time.time() - last_update > 5:
                    try:
                        status_message.edit_text(f"📥 Downloading...\n{line[:100]}")
                        last_update = time.time()
                    except:
                        pass
            
            process.wait()
            
            if process.returncode == 0:
                # Find the downloaded file
                for file in os.listdir(self.download_dir):
                    if file.startswith(file_hash):
                        file_path = os.path.join(self.download_dir, file)
                        elapsed = time.time() - start_time
                        logger.info(f"Download completed in {elapsed:.1f}s: {file_path}")
                        
                        if status_message:
                            status_message.edit_text("✅ Download completed, now uploading...")
                        
                        return {
                            "file": file_path,
                            "name": file
                        }
            
            logger.error("Download failed")
            if status_message:
                status_message.edit_text("❌ Download failed")
            return None
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            if status_message:
                status_message.edit_text(f"❌ Download failed: {e}")
            return None
    
    def cleanup(self):
        """Clean up"""
        logger.info("Torrent handler cleaned up")
