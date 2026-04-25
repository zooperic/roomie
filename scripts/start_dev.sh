#!/bin/bash
# ─── Project Roomy — Dev Launcher ────────────────────────────────────────────
# Starts Alfred and the Telegram bot in parallel.
# Prerequisites: pip install -r requirements.txt, .env filled in

set -e

echo "🏠 Starting Project Roomy..."

# Initialize DB if not exists
python -c "from shared.db import init_db; init_db()"

# Start Alfred (orchestrator API) in background
echo "▶ Starting Alfred on :8000"
uvicorn alfred.main:app --host 0.0.0.0 --port 8000 --reload &
ALFRED_PID=$!

# Wait for Alfred to be ready
sleep 2

# Start Telegram bot
echo "▶ Starting Telegram bot"
python -m interfaces.telegram.bot &
TELEGRAM_PID=$!

echo ""
echo "✅ All services running."
echo "   Alfred API  → http://localhost:8000"
echo "   Alfred docs → http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait and handle shutdown
trap "echo 'Shutting down...'; kill $ALFRED_PID $TELEGRAM_PID 2>/dev/null" EXIT
wait
