import os
import sys
import subprocess
import platform
import asyncio
from datetime import datetime

# First, check and install all dependencies
def install_dependencies():
    """Install all required Python packages"""
    required_packages = [
        "python-telegram-bot==20.7",
        "httpx==0.27.0",
        "motor==3.3.2",
        "pymongo==4.6.1",
        "pydantic-settings==2.2.1",
        "aiofiles==23.2.1",
        "beautifulsoup4==4.12.3",
        "feedparser==6.0.11",
        "aiocron==1.8",
        "loguru==0.7.2",
        "python-libtorrent==2.0.9"
    ]
    
    print("🔧 Installing required dependencies...")
    
    for package in required_packages:
        try:
            # Extract package name for import test
            package_name = package.split('=')[0].replace('-', '_')
            
            # Try to import the package
            __import__(package_name)
            print(f"✅ {package_name} is already installed")
            
        except ImportError:
            print(f"📦 Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
                
                # Try alternative installation for libtorrent
                if "libtorrent" in package:
                    print("🔄 Trying alternative libtorrent installation...")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-libtorrent"])
                        print("✅ Alternative libtorrent installation successful")
                    except:
                        print("⚠️ Warning: libtorrent installation failed. Torrent downloads will not work.")

def check_and_install_ffmpeg():
    """Check if ffmpeg is installed and provide instructions"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("⚠️ FFmpeg is not installed")
        
        system = platform.system().lower()
        instructions = {
            "linux": "sudo apt-get update && sudo apt-get install -y ffmpeg",
            "darwin": "brew install ffmpeg",
            "windows": "Download from https://ffmpeg.org/download.html and add to PATH"
        }
        
        print(f"📝 Install FFmpeg using: {instructions.get(system, 'Visit https://ffmpeg.org/download.html')}")
        return False

# Install dependencies before importing anything else
install_dependencies()
check_and_install_ffmpeg()

# Now import the installed packages
from loguru import logger
from telegram.ext import Application, ContextTypes
from telegram import Update

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

class AutoAnimeBot:
    def __init__(self):
        self.db = Database()
        self.anime_handler = None
        self.main_bot_app = None
        self.file_bot_app = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Starting AutoAnimeBot initialization...")
        
        # Create downloads directory
        os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)
        
        # Initialize database
        if not await self.db.test_connection():
            logger.critical("Database connection failed!")
            sys.exit(1)
        
        # Initialize Telegram bots
        self.main_bot_app = Application.builder().token(config.MAIN_BOT_TOKEN).build()
        self.file_bot_app = Application.builder().token(config.CLIENT_BOT_TOKEN).build()
        
        # Import and initialize anime handler
        from plugins.anime_handler import AnimeHandler
        self.anime_handler = AnimeHandler(self.main_bot_app.bot, self.file_bot_app.bot, self.db)
        
        # Setup commands
        await setup_commands(self.main_bot_app, self.anime_handler)
        
        logger.info("Initialization completed successfully!")
    
    async def start_background_tasks(self):
        """Start periodic background tasks"""
        try:
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
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
    
    async def send_startup_message(self):
        """Send startup notification"""
        try:
            await self.main_bot_app.bot.send_message(
                chat_id=config.PRODUCTION_CHAT,
                text="🤖 **AutoAnimeBot Started Successfully!**\n"
                     f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"👤 Author: {config.AUTHOR}\n"
                     f"📜 License: {config.LICENSED_UNDER}"
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
    # Run the bot
    asyncio.run(main())
