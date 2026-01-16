import os
import asyncio
from typing import List, Dict, Optional
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from loguru import logger

from config import config
from plugins.utils import (
    extract_anime_info,
    get_anime_details,
    generate_random_hash,
    encode_video_file
)

class AnimeHandler:
    def __init__(self, main_bot: Bot, file_bot: Bot, database):
        self.main_bot = main_bot
        self.file_bot = file_bot
        self.db = database
        self.processing = False
        
        # Try to initialize torrent handler
        self.torrent_handler = None
        self._init_torrent_handler()
        
        # Initialize other components
        from plugins.web_scraper import WebScraper
        self.scraper = WebScraper()
    
    def _init_torrent_handler(self):
        """Initialize torrent handler with error handling"""
        try:
            from plugins.torrent_handler import TorrentHandler
            self.torrent_handler = TorrentHandler()
            logger.info("Torrent handler initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to initialize torrent handler: {e}")
            self.torrent_handler = None
        except Exception as e:
            logger.error(f"Error initializing torrent handler: {e}")
            self.torrent_handler = None
    
    async def check_new_anime(self):
        """Check for new anime from RSS feed"""
        if self.processing:
            logger.info("Already processing, skipping check...")
            return
        
        try:
            self.processing = True
            logger.info("Checking for new anime...")
            
            last_hash = await self.db.get_last_hash()
            new_anime = await self.scraper.get_latest_anime(last_hash, limit=30)
            
            if not new_anime or not new_anime.get("array"):
                logger.info("No new anime found.")
                return
            
            # Add new anime to queue
            await self.db.add_remaining_anime(new_anime["array"])
            
            # Update last hash
            if new_anime.get("hash"):
                await self.db.update_last_hash(new_anime["hash"])
            
            # Log and notify
            count = len(new_anime["array"])
            logger.info(f"Added {count} new anime to queue")
            
            # Send notification
            await self._send_notification(count)
        
        except Exception as e:
            logger.error(f"Error checking new anime: {e}")
        finally:
            self.processing = False
    
    async def _send_notification(self, count: int):
        """Send notification about new anime"""
        try:
            await self.main_bot.send_message(
                chat_id=config.PRODUCTION_CHAT,
                text=f"📥 {count} new anime added to queue"
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def process_anime_queue(self):
        """Process anime from the queue"""
        if await self.db.is_worker_busy():
            logger.info("Worker is already busy, skipping...")
            return
        
        if self.processing:
            logger.info("Already processing queue, skipping...")
            return
        
        # Check if torrent handler is available
        if not self.torrent_handler:
            logger.error("Torrent handler not available. Skipping queue processing.")
            return
        
        try:
            await self.db.set_worker_status(True)
            self.processing = True
            
            anime_list = await self.db.get_remaining_anime()
            
            if not anime_list:
                logger.info("Anime queue is empty")
                return
            
            logger.info(f"Processing {len(anime_list)} anime in queue")
            
            # Process first anime in queue
            anime_item = anime_list[0]
            await self._process_anime_item(anime_item)
            
            # Remove processed item from queue
            if len(anime_item.get('magnets', [])) > 1:
                # If multiple qualities, remove first quality
                anime_item['magnets'].pop(0)
                anime_item['hashes'].pop(0)
                anime_item['qualities'].pop(0)
                anime_item['titles'].pop(0)
                anime_list[0] = anime_item
            else:
                # Remove entire anime
                anime_list.pop(0)
            
            # Update queue in database
            await self.db.update_remaining_anime(anime_list)
            
        except Exception as e:
            logger.error(f"Error processing anime queue: {e}")
        finally:
            await self.db.set_worker_status(False)
            self.processing = False
    
    async def _process_anime_item(self, anime_item: Dict):
        """Process a single anime item"""
        try:
            if not anime_item.get('titles'):
                logger.error("No titles in anime item")
                return
            
            # Extract info from first title
            title = anime_item['titles'][0]
            info = extract_anime_info(title)
            
            if not info:
                logger.error(f"Could not extract info from title: {title}")
                return
            
            # Get anime details from AniList
            anime_details = await get_anime_details(info["search_query"])
            
            # Create and send post
            await self._upload_anime_files(anime_item, info, anime_details)
        
        except Exception as e:
            logger.error(f"Error processing anime item: {e}")
    
    async def _upload_anime_files(self, anime_item: Dict, info: Dict, anime_details: Dict):
        """Upload anime files to channel"""
        try:
            # Prepare caption
            caption = config.POST_TEMPLATE.format(
                info["display_name"],
                info.get("episode", "N/A"),
                anime_details.get("status", "Unknown")
            )
            
            # Send initial post
            message = await self.main_bot.send_photo(
                chat_id=config.MAIN_CHANNEL,
                photo=anime_details.get("image", config.THUMBNAIL_URL),
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⏳ Uploading...", callback_data="uploading")
                ]])
            )
            
            # Process each quality version
            for i in range(len(anime_item['magnets'])):
                await self._process_quality(
                    anime_item, i, info, message, anime_details
                )
        
        except Exception as e:
            logger.error(f"Error uploading anime files: {e}")
    
    async def _process_quality(self, anime_item: Dict, index: int, info: Dict, 
                               message, anime_details: Dict):
        """Process a specific quality version"""
        try:
            quality = anime_item['qualities'][index]
            magnet = anime_item['magnets'][index]
            
            # Check if torrent handler is available
            if not self.torrent_handler:
                logger.error("Torrent handler not available for download")
                return
            
            # Send download start message
            download_msg = await self.main_bot.send_message(
                config.PRODUCTION_CHAT,
                f"📥 Downloading {anime_item['name']} ({quality})..."
            )
            
            # Define progress callback
            async def update_progress(progress):
                try:
                    text = (
                        f"📥 Downloading {anime_item['name']} ({quality})\n"
                        f"Progress: {progress['progress']:.1f}%\n"
                        f"Speed: {progress['download_rate'] / 1024:.1f} KB/s\n"
                        f"Peers: {progress['num_peers']}\n"
                        f"Status: {progress['state']}"
                    )
                    await download_msg.edit_text(text)
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
            
            # Download torrent
            downloaded_file = await self.torrent_handler.download(magnet, update_progress)
            
            if not downloaded_file:
                await download_msg.edit_text("❌ Download failed")
                return
            
            # Upload original file
            await download_msg.edit_text(f"📤 Uploading {anime_item['name']}...")
            
            with open(downloaded_file["file"], 'rb') as file:
                file_msg = await self.file_bot.send_document(
                    chat_id=config.FILES_CHANNEL,
                    document=file,
                    filename=f"{info['display_name']} - Episode {info['episode']} ({quality})",
                    caption=anime_item['titles'][index],
                    thumbnail=config.THUMBNAIL_URL if config.THUMBNAIL_URL else None
                )
            
            # Add to database
            file_hash = generate_random_hash(20)
            await self.db.add_file_record(
                anime_item['titles'][index],
                file_hash,
                file_msg.message_id
            )
            
            # Update post with download button
            await self._update_post_buttons(
                message, quality, file_msg.message_id, file_hash
            )
            
            # Process encoding for 720p files
            if "720" in quality:
                await self._encode_and_upload(
                    downloaded_file["file"], anime_item, info, index, message
                )
            
            # Clean up downloaded files
            await self._cleanup_files(downloaded_file)
            
            await download_msg.edit_text(f"✅ Completed: {anime_item['name']} ({quality})")
            
        except Exception as e:
            logger.error(f"Error processing quality: {e}")
            try:
                await download_msg.edit_text(f"❌ Error: {str(e)[:100]}")
            except:
                pass
    
    async def _cleanup_files(self, downloaded_file: Dict):
        """Clean up downloaded files"""
        try:
            # Clean main file
            if os.path.exists(downloaded_file["file"]):
                os.remove(downloaded_file["file"])
                logger.info(f"Cleaned up file: {downloaded_file['file']}")
            
            # Clean other files if they exist
            if "all_files" in downloaded_file:
                for file_path in downloaded_file["all_files"]:
                    if file_path != downloaded_file["file"] and os.path.exists(file_path):
                        os.remove(file_path)
                        
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
    
    async def _update_post_buttons(self, message, quality: str, msg_id: int, file_hash: str):
        """Update post with download buttons"""
        try:
            # Get current bot username
            bot_info = await self.main_bot.get_me()
            bot_username = bot_info.username
            
            # Create new button
            new_button = InlineKeyboardButton(
                text=f"⬇️ {quality}",
                url=f"https://t.me/{bot_username}?start={msg_id}_{file_hash}"
            )
            
            # Get current keyboard or create new one
            if message.reply_markup:
                keyboard = message.reply_markup.inline_keyboard
                # Remove uploading button if present
                keyboard = [
                    row for row in keyboard 
                    if not (row and row[0].callback_data == "uploading")
                ]
                keyboard.append([new_button])
            else:
                keyboard = [[new_button]]
            
            await message.edit_reply_markup(InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            logger.error(f"Error updating post buttons: {e}")
    
    async def _encode_and_upload(self, file_path: str, anime_item: Dict, 
                                 info: Dict, index: int, message):
        """Encode and upload encoded version"""
        try:
            # Send encoding message
            encode_msg = await self.main_bot.send_message(
                config.PRODUCTION_CHAT,
                f"🔧 Encoding {anime_item['name']}..."
            )
            
            # Encode file
            encoded_file = await encode_video_file(file_path)
            
            if not encoded_file or not os.path.exists(encoded_file):
                await encode_msg.edit_text("❌ Encoding failed")
                return
            
            await encode_msg.edit_text("📤 Uploading encoded version...")
            
            # Upload encoded file
            with open(encoded_file, 'rb') as file:
                encoded_msg_obj = await self.file_bot.send_document(
                    chat_id=config.FILES_CHANNEL,
                    document=file,
                    filename=f"[ENCODED] {info['display_name']} - Episode {info['episode']}",
                    caption=f"[ENCODED] {anime_item['titles'][index]}",
                    thumbnail=config.THUMBNAIL_URL if config.THUMBNAIL_URL else None
                )
            
            # Add to database
            enc_hash = generate_random_hash(20)
            await self.db.add_file_record(
                f"[ENCODED] {anime_item['titles'][index]}",
                enc_hash,
                encoded_msg_obj.message_id
            )
            
            # Get bot username
            bot_info = await self.main_bot.get_me()
            bot_username = bot_info.username
            
            # Update post with encoded button
            if message.reply_markup:
                keyboard = message.reply_markup.inline_keyboard
                keyboard.append([InlineKeyboardButton(
                    text="🎬 ENCODED",
                    url=f"https://t.me/{bot_username}?start={encoded_msg_obj.message_id}_{enc_hash}"
                )])
                await message.edit_reply_markup(InlineKeyboardMarkup(keyboard))
            
            # Clean up encoded file
            try:
                os.remove(encoded_file)
                logger.info(f"Cleaned up encoded file: {encoded_file}")
            except Exception as e:
                logger.error(f"Error cleaning up encoded file: {e}")
            
            await encode_msg.edit_text(f"✅ Encoding completed: {anime_item['name']}")
            
        except Exception as e:
            logger.error(f"Error in encoding: {e}")
            try:
                await encode_msg.edit_text(f"❌ Encoding error: {str(e)[:100]}")
            except:
                pass
