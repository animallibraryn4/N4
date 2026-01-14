import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
API_ID = int(os.getenv("API_ID", 22299340))
API_HASH = os.getenv("API_HASH", "09b09f3e2ff1306da4a19888f614d937")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Owner Settings
OWNER_ID = int(os.getenv("OWNER_ID", 5380609667))

# Queue Settings
MAX_CONCURRENT = 1  # Maximum concurrent downloads
QUEUE_ENABLED = True

# Download Settings
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB
TIMEOUT = 30  # Request timeout in seconds

# FFmpeg Settings
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
DEFAULT_QUALITY = "1080p"
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

# Paths
TEMP_DIR = "temp"
LOGS_DIR = "logs"

# User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
