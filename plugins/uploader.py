import os
import asyncio
from typing import Optional
from pyrogram import Client
from pyrogram.types import Message, InputMediaVideo
from plugins.utils import cleanup_temp
from database import db

class Uploader:
    @staticmethod
    async def upload_video(
        client: Client,
        chat_id: int,
        file_path: str,
        caption: str = "",
        message: Optional[Message] = None
    ) -> dict:
        """Upload video to Telegram"""
        try:
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            file_size = os.path.getsize(file_path)
            
            # Check file size (Telegram limit is 2GB for bots)
            if file_size > 2 * 1024 * 1024 * 1024:
                return {"error": "File too large for Telegram (max 2GB)"}
            
            # If we have a status message, update it
            status_msg = None
            if message:
                status_msg = await message.reply_text("📤 Uploading to Telegram...")
            
            # Upload progress callback
            def progress(current, total):
                if status_msg and total > 0:
                    percent = (current / total) * 100
                    asyncio.create_task(
                        status_msg.edit_text(f"📤 Uploading: {percent:.1f}%")
                    )
            
            # Upload video
            try:
                sent_message = await client.send_video(
                    chat_id=chat_id,
                    video=file_path,
                    caption=caption[:1024],  # Telegram caption limit
                    supports_streaming=True,
                    progress=progress
                )
            except Exception as e:
                if "file too large" in str(e).lower():
                    return {"error": "File too large for Telegram"}
                raise e
            
            # Update status
            if status_msg:
                await status_msg.delete()
            
            # Clean up temp file
            cleanup_temp(file_path)
            
            # Log successful upload
            db.log_action(
                user_id=chat_id,
                action="upload_success",
                details=f"File: {os.path.basename(file_path)}"
            )
            
            return {
                "success": True,
                "message_id": sent_message.id,
                "file_size": file_size
            }
            
        except Exception as e:
            # Clean up on error
            cleanup_temp(file_path)
            return {"error": f"Upload failed: {str(e)}"}
