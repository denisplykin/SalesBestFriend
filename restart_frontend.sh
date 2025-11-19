#!/bin/bash
# Restart frontend with clean cache

echo "🔄 Restarting frontend with clean cache..."
echo ""

cd "$(dirname "$0")/frontend"

# Kill any running dev servers
echo "Stopping any running dev servers..."
pkill -f "vite" 2>/dev/null || true
sleep 1

# Clean cache and dist
echo "Cleaning cache..."
rm -rf node_modules/.vite
rm -rf dist

echo ""
echo "✅ Starting fresh frontend..."
echo "🌐 Frontend will run on: http://localhost:5173 (or similar)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev

