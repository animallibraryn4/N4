# uploader.py
import os
import urllib.parse
import time
import logging
from typing import Optional
from math import floor

import requests
from pyrogram import Client
from pyrogram.types import Message

logger = logging.getLogger(__name__)

class Uploader:
    def __init__(self):
        self.last_update = 0
        self.download_dir = "files"
        self.ensure_directory()
        
    def ensure_directory(self):
        """Ensure download directory exists."""
        try:
            os.makedirs(self.download_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create directory: {e}")
            raise

    async def download_file(self, url: str, proc: Message) -> Optional[str]:
        """Download a file with progress updates."""
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                
                total_size = floor(int(r.headers.get("content-length", 0)) / (1024 * 1024))
                ext = url.split(".")[-1][:4]  # Limit extension length
                temp_path = f"temp_{time.time()}.{ext}"
                
                start_time = time.time()
                mb_downloaded = 0
                
                with open(temp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            mb_downloaded += 1
                            
                            # Update progress every 5 seconds
                            if (time.time() - start_time) > 5:
                                try:
                                    await proc.edit_text(
                                        f"Downloading: {mb_downloaded}/{total_size} MB"
                                    )
                                    start_time = time.time()
                                except Exception as e:
                                    logger.warning(f"Progress update failed: {e}")
                
                return temp_path
                
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    def generate_filename(self, url: str) -> str:
        """Generate a clean filename from URL."""
        try:
            filename = urllib.parse.unquote(url.split("/")[-1])
            parts = filename.split("-AAT[")[0].strip()
            clean_name = parts.replace(".", " ").replace("-", " ")
            ext = filename.split(".")[-1][:4]  # Limit extension length
            
            return f"{clean_name} [@animestorys_1].{ext}"
            
        except Exception as e:
            logger.error(f"Filename generation failed: {e}")
            return f"file_{time.time()}.mp4"

    async def upload_progress(self, current: int, total: int, message: Message):
        """Handle upload progress updates."""
        current_time = time.time()
        if (current_time - self.last_update) > 5:
            try:
                await message.edit_text(
                    f"Uploading: {floor(current/(1024*1024))}/{floor(total/(1024*1024))} MB"
                )
                self.last_update = current_time
            except Exception as e:
                logger.warning(f"Upload progress update failed: {e}")

    async def start_uploader(self, client: Client, message: Message, url: str, proc: Message):
        """Main upload handler."""
        try:
            await proc.edit_text(f"Processing: {url}")
            
            # Download file
            temp_file = await self.download_file(url, proc)
            if not temp_file:
                raise Exception("Download failed")
                
            # Generate filename and move to download directory
            filename = self.generate_filename(url)
            final_path = os.path.join(self.download_dir, filename)
            os.rename(temp_file, final_path)
            
            # Upload file
            caption = f"🧿 **File:** `{filename}`"
            await client.send_document(
                chat_id="animestorys_1",
                document=final_path,
                thumb="thumb.jpeg",
                caption=caption,
                file_name=filename,
                force_document=True,
                progress=self.upload_progress,
                progress_args=(proc,),
            )
            
            # Clean up
            os.remove(final_path)
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# Global uploader instance
uploader = Uploader()

async def start_uploader(client: Client, message: Message, url: str, proc: Message):
    """Wrapper for the uploader instance."""
    await uploader.start_uploader(client, message, url, proc)
