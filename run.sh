#!/bin/bash

# Recall Trading Agent - Run Script
# This script sets up and runs the trading agent

set -e  # Exit on any error

echo "🚀 Starting Recall Trading Agent Setup..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Please run this script from the recall-trading-agent directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing requirements..."
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API credentials before running!"
    echo "   You can get your API key from: https://register.recall.network"
    read -p "Press Enter after you've updated the .env file..."
fi

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
fi

# Validate configuration
echo "✅ Validating configuration..."
python3 -c "
import sys
sys.path.append('src')
try:
    from config import Config
    print('Configuration loaded successfully!')
    print(f'API URL: {Config.TRADING_SIM_API_URL}')
    has_key = bool(Config.TRADING_SIM_API_KEY and Config.TRADING_SIM_API_KEY != 'your_api_key_here')
    print(f'API Key configured: {has_key}')
    
    if not has_key:
        print()
        print('⚠️  Please update the .env file with your Recall API key!')
        print('   You can get your API key from: https://register.recall.network')
    
except Exception as e:
    print(f'Configuration error: {e}')
    sys.exit(1)
"

# Check API connectivity (skip if no API key configured)
echo "🌐 Testing API connectivity..."
python3 -c "
import sys
sys.path.append('src')
try:
    from config import Config
    if Config.TRADING_SIM_API_KEY and Config.TRADING_SIM_API_KEY != 'your_api_key_here':
        from trading_client import RecallTradingClient
        client = RecallTradingClient()
        if client.health_check():
            print('✅ API connection successful!')
        else:
            print('❌ API connection failed! Please check your API key.')
    else:
        print('⚠️  API key not configured, skipping connectivity test.')
except Exception as e:
    print(f'⚠️  API test skipped: {e}')
"

echo ""
echo "🎯 Setup complete! Choose how to run the agent:"
echo ""
echo "1. Run the trading agent (default)"
echo "2. Check portfolio status only"
echo "3. Generate daily report"
echo "4. Run in dry-run mode (no actual trades)"
echo ""

# Parse command line arguments or prompt user
if [ $# -eq 0 ]; then
    read -p "Enter your choice (1-4) [1]: " choice
    choice=${choice:-1}
else
    choice=$1
fi

case $choice in
    1)
        echo "🤖 Starting trading agent..."
        python3 main.py
        ;;
    2)
        echo "📊 Checking portfolio status..."
        python3 main.py --mode status
        ;;
    3)
        echo "📈 Generating daily report..."
        python3 main.py --mode report
        ;;
    4)
        echo "🧪 Running in dry-run mode..."
        python3 main.py --dry-run
        ;;
    "test")
        echo "🧪 Running tests..."
        python3 -m pytest tests/ -v
        ;;
    *)
        echo "❌ Invalid choice. Please run: $0 [1|2|3|4|test]"
        exit 1
        ;;
esac