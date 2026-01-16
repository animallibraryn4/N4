#!/bin/bash

# AutoAnimeBot Installation Script
# Run: bash install.sh

set -e

echo "🚀 Starting AutoAnimeBot installation..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "🐍 Python version: $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION 3.8" | awk '{print ($1 < $2)}') -eq 1 ]]; then
    echo "❌ Python 3.8 or higher is required"
    exit 1
fi

# Create virtual environment
echo "📁 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install libtorrent
echo "⚡ Installing libtorrent..."
SYSTEM=$(uname -s)

if [[ "$SYSTEM" == "Linux" ]]; then
    echo "📥 Installing system dependencies for libtorrent..."
    
    # Debian/Ubuntu
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            python3-dev \
            libboost-python-dev \
            libboost-system-dev \
            libssl-dev
    # Fedora/RHEL
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y \
            python3-devel \
            boost-python3-devel \
            boost-system-devel \
            openssl-devel
    # Arch
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm \
            python \
            boost-libs \
            openssl
    fi
    
    # Install python-libtorrent via pip
    pip install python-libtorrent==2.0.9
    
elif [[ "$SYSTEM" == "Darwin" ]]; then
    echo "🍎 Installing for macOS..."
    
    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        brew install boost-python3
    fi
    
    pip install python-libtorrent==2.0.9
    
elif [[ "$SYSTEM" == "Windows" ]] || [[ "$SYSTEM" == "MINGW"* ]]; then
    echo "🪟 Installing for Windows..."
    pip install python-libtorrent==2.0.9
else
    echo "❓ Unknown system: $SYSTEM"
    echo "⚠️ Trying generic installation..."
    pip install python-libtorrent==2.0.9
fi

# Check if libtorrent installed successfully
python3 -c "import libtorrent; print(f'✅ libtorrent installed: {libtorrent.__version__}')" && \
echo "✅ libtorrent installation successful!" || \
echo "❌ libtorrent installation failed!"

# Install FFmpeg
echo "🎬 Checking/Installing FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ FFmpeg not found. Video encoding will be disabled."
    echo "   Install FFmpeg manually:"
    echo "   - Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "   - macOS: brew install ffmpeg"
    echo "   - Windows: Download from https://ffmpeg.org/download.html"
else
    echo "✅ FFmpeg is installed"
    ffmpeg -version | head -n 1
fi

# Create necessary directories
echo "📂 Creating directories..."
mkdir -p downloads
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file template..."
    cat > .env << EOF
# Telegram Configuration
API_ID=22299340
API_HASH=your_api_hash_here
MAIN_BOT_TOKEN=your_main_bot_token_here
CLIENT_BOT_TOKEN=your_client_bot_token_here

# Database
DATABASE_URL=mongodb+srv://mikota4432:jkJDQuZH6o8pxxZe@cluster0.2vngilq.mongodb.net/?retryWrites=true&w=majority

# Optional: Override other settings if needed
# MAIN_CHANNEL=-1001896877147
# FILES_CHANNEL=-1001896877147
# PRODUCTION_CHAT=-1001925970923
EOF
    echo "⚠️ Please edit .env file with your actual credentials!"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit the .env file with your Telegram API credentials"
echo "2. Configure your database connection if needed"
echo "3. Run the bot: python bot.py"
echo ""
echo "For help, check the README.md file"
