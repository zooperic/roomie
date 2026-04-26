#!/bin/bash
# ─── Project Roomy — Dev Launcher ────────────────────────────────────────────
# Starts Alfred and all configured Telegram bots in parallel.
# Prerequisites: pip install -r requirements.txt, .env filled in

set -e

echo "🏠 Starting Project Roomy..."

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Initialize DB if not exists
python -c "from shared.db import init_db; init_db()"

# Kill any existing process on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "🔄 Port 8000 in use - killing existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start Alfred (orchestrator API) in background
echo "▶ Starting Alfred on :8000"
uvicorn agent_skills.alfred.main:app --host 0.0.0.0 --port 8000 --reload &
ALFRED_PID=$!

# Wait for Alfred to be ready
sleep 2

# Start Telegram bots (only if tokens are configured)
PIDS=()

if [ ! -z "$TELEGRAM_TOKEN_ALFRED" ]; then
    echo "▶ Starting Alfred bot"
    python -m interfaces.telegram.alfred_bot &
    PIDS+=($!)
else
    echo "⏭  Skipping Alfred bot (no token)"
fi

if [ ! -z "$TELEGRAM_TOKEN_ELSA" ]; then
    echo "▶ Starting Elsa bot"
    python -m interfaces.telegram.elsa_bot &
    PIDS+=($!)
else
    echo "⏭  Skipping Elsa bot (no token)"
fi

if [ ! -z "$TELEGRAM_TOKEN_REMY" ]; then
    echo "▶ Starting Remy bot"
    python -m interfaces.telegram.remy_bot &
    PIDS+=($!)
else
    echo "⏭  Skipping Remy bot (no token)"
fi

if [ ! -z "$TELEGRAM_TOKEN_LEBOWSKI" ]; then
    echo "▶ Starting Lebowski bot"
    python -m interfaces.telegram.lebowski_bot &
    PIDS+=($!)
else
    echo "⏭  Skipping Lebowski bot (no token)"
fi

echo ""
echo "✅ All services running."
echo "   Alfred API  → http://localhost:8000"
echo "   Alfred docs → http://localhost:8000/docs"
echo "   Active bots → ${#PIDS[@]}"
echo ""
echo "Press Ctrl+C to stop all services."

# Trap handler function
cleanup() {
    echo "Shutting down..."
    kill $ALFRED_PID 2>/dev/null || true
    for pid in "${PIDS[@]}"; do
        kill $pid 2>/dev/null || true
    done
}

trap cleanup EXIT INT TERM
wait
