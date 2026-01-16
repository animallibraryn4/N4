import asyncio
import os
import sys
import subprocess
import platform
import importlib
from loguru import logger
from telegram.ext import Application, ContextTypes
from telegram import Update
import aiohttp
from datetime import datetime

# Import modules
from config import config
from database import Database
from plugins.commands import setup_commands

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: | <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    config.LOG_FILE,
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: | <8} | {name}:{function}:{line} - {message}"
)

def check_and_install_libtorrent():
    """Check if libtorrent is installed and install if missing"""
    try:
        import libtorrent
        logger.info(f"libtorrent is already installed (version: {libtorrent.__version__})")
        return True
    except ImportError:
        logger.warning("libtorrent not found. Attempting to install...")
        
        system = platform.system().lower()
        
        try:
            if system == "linux":
                # Try to install via pip with system dependencies
                logger.info("Installing libtorrent for Linux...")
                
                # Install system dependencies first
                subprocess.run([
                    "apt-get", "update"
                ], capture_output=True)
                
                subprocess.run([
                    "apt-get", "install", "-y", 
                    "python3-dev", 
                    "libboost-python-dev", 
                    "libboost-system-dev"
                ], capture_output=True)
                
                # Install via pip
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "--no-cache-dir", "python-libtorrent==2.0.9"
                ])
                
            elif system == "windows":
                logger.info("Installing libtorrent for Windows...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install",
                    "--no-cache-dir", "python-libtorrent==2.0.9"
                ])
                
            elif system == "darwin":  # macOS
                logger.info("Installing libtorrent for macOS...")
                # Install Homebrew dependencies first if available
                try:
                    subprocess.run(["brew", "--version"], capture_output=True)
                    subprocess.run(["brew", "install", "boost-python3"], capture_output=True)
                except:
                    pass
                
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install",
                    "--no-cache-dir", "python-libtorrent==2.0.9"
                ])
            
            logger.info("libtorrent installed successfully!")
            
            # Verify installation
            import libtorrent
            logger.info(f"libtorrent verification successful (version: {libtorrent.__version__})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install libtorrent: {e}")
            
            # Try alternative installation method
            logger.info("Trying alternative installation method...")
            try:
                # Install from wheel if available
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install",
                    "python-libtorrent"
                ])
                import libtorrent
                logger.info(f"Alternative installation successful! (version: {libtorrent.__version__})")
                return True
            except Exception as e2:
                logger.error(f"Alternative installation also failed: {e2}")
                return False
    
    except Exception as e:
        logger.error(f"Error checking libtorrent: {e}")
        return False

def check_and_install_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        # Check if ffmpeg is available
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("FFmpeg is already installed")
            return True
        else:
            logger.warning("FFmpeg not found or not working properly")
            return False
    except FileNotFoundError:
        logger.warning("FFmpeg not found. Please install FFmpeg for video encoding.")
        
        system = platform.system().lower()
        installation_guide = {
            "linux": "sudo apt-get install ffmpeg",
            "darwin": "brew install ffmpeg",
            "windows": "Download from https://ffmpeg.org/download.html"
        }
        
        logger.info(f"Install FFmpeg using: {installation_guide.get(system, 'Visit https://ffmpeg.org/download.html')}")
        return False

class AutoAnimeBot:
    def __init__(self):
        self.db = Database()
        self.anime_handler = None
        self.main_bot_app = None
        self.file_bot_app = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Starting AutoAnimeBot initialization...")
        
        # Check and install dependencies
        if not check_and_install_libtorrent():
            logger.critical("libtorrent installation failed! Bot cannot function without it.")
            logger.info("You can manually install it with: pip install python-libtorrent")
            sys.exit(1)
        
        # Check for ffmpeg (optional but recommended)
        check_and_install_ffmpeg()
        
        # Create downloads directory
        os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)
        
        # Initialize database
        if not await self.db.test_connection():
            logger.critical("Database connection failed!")
            sys.exit(1)
        
        # Initialize Telegram bots
        self.main_bot_app = Application.builder().token(config.MAIN_BOT_TOKEN).build()
        self.file_bot_app = Application.builder().token(config.CLIENT_BOT_TOKEN).build()
        
        # Import anime_handler after libtorrent is confirmed to be installed
        from plugins.anime_handler import AnimeHandler
        
        # Initialize anime handler
        self.anime_handler = AnimeHandler(self.main_bot_app.bot, self.file_bot_app.bot, self.db)
        
        # Setup commands
        await setup_commands(self.main_bot_app, self.anime_handler)
        
        logger.info("Initialization completed successfully!")
    
    async def start_background_tasks(self):
        """Start periodic background tasks"""
        from aiocron import crontab
        
        # Check for new anime every 5 minutes
        @crontab('*/5 * * * *')
        async def check_new_anime():
            logger.info("Checking for new anime...")
            await self.anime_handler.check_new_anime()
        
        # Process queue every 5 minutes
        @crontab('*/5 * * * *')
        async def process_queue():
            logger.info("Processing anime queue...")
            await self.anime_handler.process_anime_queue()
        
        logger.info("Background tasks scheduled")
    
    async def send_startup_message(self):
        """Send startup notification"""
        try:
            await self.main_bot_app.bot.send_message(
                chat_id=config.PRODUCTION_CHAT,
                text="🤖 **AutoAnimeBot Started Successfully!**\n"
                     f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"👤 Author: {config.AUTHOR}\n"
                     f"📜 License: {config.LICENSED_UNDER}\n\n"
                     f"✅ libtorrent: Installed\n"
                     f"✅ Database: Connected\n"
                     f"✅ Bots: Ready"
            )
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")
    
    async def run(self):
        """Main run method"""
        try:
            await self.initialize()
            await self.send_startup_message()
            await self.start_background_tasks()
            
            # Start both bots
            await self.main_bot_app.initialize()
            await self.file_bot_app.initialize()
            
            logger.info("Bots are running. Press Ctrl+C to stop.")
            
            # Keep the bots running
            await asyncio.gather(
                self.main_bot_app.run_polling(),
                self.file_bot_app.run_polling(),
                return_exceptions=True
            )
            
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
        except Exception as e:
            logger.critical(f"Fatal error: {e}")
            sys.exit(1)
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Clean shutdown"""
        logger.info("Shutting down...")
        if self.main_bot_app:
            await self.main_bot_app.stop()
        if self.file_bot_app:
            await self.file_bot_app.stop()
        if self.db:
            await self.db.close()
        logger.info("Shutdown complete.")

async def main():
    """Entry point"""
    bot = AutoAnimeBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
