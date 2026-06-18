#!/bin/bash

echo "🚀 Setting up Myanmar Address Parser..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv myenv
source myenv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set your environment variables:"
echo "   export TELEGRAM_TOKEN='your_bot_token'"
echo "   export GROQ_API_KEY='your_groq_key'"
echo ""
echo "2. Run the pipeline:"
echo "   python get_csv.py    # Upload CSV via Telegram"
echo "   python script.py     # Process addresses"
