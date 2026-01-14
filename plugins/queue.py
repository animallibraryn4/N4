import asyncio
import time
from pyrogram import Client
from pyrogram.types import Message
from config import MAX_CONCURRENT, QUEUE_ENABLED
from database import db
from plugins.watchanimeworld import WatchAnimeWorldScraper
from plugins.downloader import Downloader
from plugins.ffmpeg import FFmpegProcessor
from plugins.uploader import Uploader
from plugins.utils import cleanup_temp

# Queue state
queue_lock = asyncio.Lock()
current_processing = 0
queue_notifications = {}  # user_id: status_message

async def add_to_queue(client: Client, message: Message, url: str):
    """Add a new job to queue"""
    user_id = message.from_user.id
    
    # Add to database
    job_id = db.add_to_queue(user_id, url)
    
    # Send queue notification
    pending_jobs = db.get_pending_jobs()
    position = len([job for job in pending_jobs if job[1] == user_id])
    
    status_msg = await message.reply_text(
        f"✅ Added to queue!\n"
        f"📊 Position: {position}\n"
        f"⏳ Please wait..."
    )
    
    # Store notification message
    queue_notifications[user_id] = status_msg
    
    # Update user stats
    db.increment_request(user_id)
    
    # Log
    db.log_action(user_id, "added_to_queue", f"URL: {url}")

async def process_queue(client: Client):
    """Process queue items"""
    global current_processing
    
    while True:
        try:
            # Check if we can process more
            async with queue_lock:
                if current_processing >= MAX_CONCURRENT:
                    await asyncio.sleep(5)
                    continue
                
                # Get next job
                pending = db.get_pending_jobs()
                if not pending:
                    await asyncio.sleep(5)
                    continue
                
                # Get first job
                job_id, user_id, url = pending[0]
                current_processing += 1
                db.update_job_status(job_id, 'processing')
            
            # Process the job
            await process_single_job(client, job_id, user_id, url)
            
        except Exception as e:
            print(f"Queue processor error: {e}")
        finally:
            async with queue_lock:
                current_processing = max(0, current_processing - 1)
            
            await asyncio.sleep(2)

async def process_single_job(client: Client, job_id: int, user_id: int, url: str):
    """Process a single queue job"""
    try:
        # Get user's notification message
        status_msg = queue_notifications.get(user_id)
        if status_msg:
            await status_msg.edit_text("🔍 Processing your request...")
        
        # Step 1: Scrape
        if status_msg:
            await status_msg.edit_text("🌐 Fetching video information...")
        
        async with WatchAnimeWorldScraper() as scraper:
            result = await scraper.scrape_episode(url)
            
            if "error" in result:
                await send_error(client, user_id, f"Scraping failed: {result['error']}", status_msg)
                db.update_job_status(job_id, 'failed')
                return
            
            episode_info = result.get("episode_info", {})
            player_data = result.get("player_data", {})
        
        # Step 2: Download
        if status_msg:
            await status_msg.edit_text("📥 Downloading video...")
        
        async with Downloader() as downloader:
            download_result = await downloader.download(player_data, episode_info)
            
            if "error" in download_result:
                await send_error(client, user_id, f"Download failed: {download_result['error']}", status_msg)
                db.update_job_status(job_id, 'failed')
                return
        
        # Step 3: Process with FFmpeg
        if status_msg:
            await status_msg.edit_text("🎬 Processing video...")
        
        processor = FFmpegProcessor()
        process_result = await processor.process_video(download_result["file_path"])
        
        if "error" in process_result:
            # Try to upload original if processing fails
            output_path = download_result["file_path"]
        else:
            output_path = process_result["output_path"]
            # Clean up original download
            cleanup_temp(download_result["file_path"])
        
        # Step 4: Upload
        if status_msg:
            await status_msg.edit_text("📤 Preparing to upload...")
        
        caption = f"🎬 {episode_info.get('title', 'Episode')}"
        
        uploader = Uploader()
        upload_result = await uploader.upload_video(
            client=client,
            chat_id=user_id,
            file_path=output_path,
            caption=caption
        )
        
        if "error" in upload_result:
            await send_error(client, user_id, f"Upload failed: {upload_result['error']}", status_msg)
            db.update_job_status(job_id, 'failed')
        else:
            # Success
            if status_msg:
                await status_msg.delete()
            
            # Send success message
            await client.send_message(
                user_id,
                f"✅ **Download Complete!**\n\n"
                f"📹 **Title:** {episode_info.get('title', 'Episode')}\n"
                f"📦 **Size:** {upload_result.get('file_size', 0) // 1024 // 1024} MB\n\n"
                f"Enjoy watching! 🍿"
            )
            
            db.update_job_status(job_id, 'completed', output_path)
            
            # Clean up notification
            if user_id in queue_notifications:
                del queue_notifications[user_id]
            
            # Log success
            db.log_action(user_id, "job_completed")
    
    except Exception as e:
        await send_error(client, user_id, f"Processing error: {str(e)}", status_msg)
        db.update_job_status(job_id, 'failed')
    finally:
        # Cleanup
        pass

async def send_error(client: Client, user_id: int, error_msg: str, status_msg=None):
    """Send error message to user"""
    try:
        if status_msg:
            await status_msg.edit_text(f"❌ Error: {error_msg}")
        else:
            await client.send_message(user_id, f"❌ Error: {error_msg}")
    except:
        pass
