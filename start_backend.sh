#!/bin/bash
# Start Trial Class Assistant Backend

echo "🚀 Starting Trial Class Assistant Backend..."
echo ""

cd "$(dirname "$0")/backend"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Copying from env.example..."
    cp env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and add your OPENROUTER_API_KEY!"
    echo ""
fi

# Check for OPENROUTER_API_KEY
if grep -q "sk-or-v1-\.\.\." .env; then
    echo "⚠️  WARNING: OPENROUTER_API_KEY not configured in backend/.env"
    echo "Get your key at: https://openrouter.ai/keys"
    echo ""
fi

echo "✅ Starting Trial Class backend..."
echo "📡 Backend will run on: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main_trial_class.py

