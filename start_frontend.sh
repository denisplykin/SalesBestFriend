#!/bin/bash
# Start Trial Class Assistant Frontend

echo "🚀 Starting Trial Class Assistant Frontend..."
echo ""

cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules not found!"
    echo "Running npm install..."
    npm install
    echo ""
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Copying from env.example..."
    cp env.example .env
    echo "✅ Created .env with default settings"
    echo ""
fi

echo "✅ Starting frontend..."
echo "🌐 Frontend will run on: http://localhost:5173 (or similar)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev

