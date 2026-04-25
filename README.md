# 🏠 Project R.O.O.M.I.E

> A modular multi-agent home assistant. Each agent owns a domain of your home. Alfred ties them together (Random Operators On My Individual Errands)

---

## Current Status — Phase 1 (In Progress)

| Component | Status |
|-----------|--------|
| Backend (Alfred + Elsa) | ✅ Running |
| Telegram bot (`alfred_roomie_bot`) | 🔄 Token setup |
| Dashboard (Next.js) | 📋 Scoped |
| Swiggy MCP integration | 🔜 Phase 2 |

---

## Agents

| Agent | Domain | Phase | Status |
|-------|--------|-------|--------|
| **Alfred** | Orchestrator — routes all intent, confirmation gate | 1 | ✅ Live |
| **Elsa** | Fridge inventory, recipe parsing, order suggestions | 1 | ✅ Live |
| **Remy** | Pantry / dry goods inventory | 2 | Stub |
| **Finn** | Household spend analytics | 4 | Stub |
| **Iris** | Smart home device control | 4 | Stub |

---

## How to Talk to Roomie

- **Telegram** — Primary interface. Message `@alfred_roomie_bot` directly, or tag it in a group.
- **Web Dashboard** — Inventory, event log, analytics, task board, chat panel.
- **Direct REST** — `POST localhost:8000/message` for anything.

---

## Stack

| Layer | Tech | Status |
|-------|------|--------|
| Backend | Python + FastAPI | ✅ |
| LLM (local) | Ollama + qwen2.5:7b | ✅ |
| LLM (cloud) | Claude Haiku / GPT-4o-mini | swap via `.env` |
| Database | SQLite → PostgreSQL | ✅ SQLite |
| Telegram | python-telegram-bot | 🔄 |
| Dashboard | Next.js + Tailwind (roomie-web/) | 📋 |
| Hosting | Local + ngrok → Vercel (dashboard) + Fly.io (API) | local now |

---

## Quickstart

```bash
cd ~/Desktop/meh/roomie
source .venv/bin/activate          # or skip if using system Python

# Set env vars (only needed once per terminal session)
export PYTHONPATH=/Users/ericbrian/Desktop/meh/roomie

# Start Alfred
uvicorn agent_skills.alfred.main:app --reload --port 8000

# Start Telegram bot (new terminal tab)
export PYTHONPATH=/Users/ericbrian/Desktop/meh/roomie
python -m interfaces.telegram.bot
```

Dashboard: open `http://localhost:8000` in browser.
API explorer: `http://localhost:8000/docs`

---

## Environment Variables (`.env`)

```bash
LLM_PROVIDER=ollama                    # ollama | claude | openai
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_URL=http://localhost:11434

# For cloud LLM (swap LLM_PROVIDER above)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Telegram
TELEGRAM_TOKEN=                        # from @BotFather
ALLOWED_TELEGRAM_USER_IDS=            # your Telegram user ID from @userinfobot

# DB (SQLite default, no changes needed for Phase 1)
DATABASE_URL=sqlite:///./data/roomy.db
```

---

## Project Structure

```
roomie/
├── agent_skills/
│   ├── alfred/        main.py, router.py, SKILLS.md
│   ├── elsa/          main.py, SKILLS.md
│   ├── remy/          SKILLS.md (stub)
│   ├── finn/          SKILLS.md (stub)
│   └── iris/          SKILLS.md (stub)
├── shared/            base_agent.py, models.py, llm_provider.py, db.py
├── interfaces/
│   └── telegram/      bot.py
├── roomie-web/        Next.js dashboard (Phase 1, TBD)
├── scripts/           start_dev.sh
├── data/              roomy.db
└── dashboard.html     Interim dashboard (served at localhost:8000)
```

---

## Adding a New Agent

1. Create `agent_skills/your_agent/` with `__init__.py` and `main.py`
2. Implement `BaseAgent` from `shared/base_agent.py`
3. Write `SKILLS.md`
4. In `agent_skills/alfred/main.py` lifespan, add: `register_agent(YourAgent())`
5. Done — Alfred discovers skills automatically, no other changes

---

## API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Dashboard HTML |
| `/message` | POST | Send a message to Alfred |
| `/confirm` | POST | Confirm or cancel a pending action |
| `/status` | GET | Alfred + all agent health |
| `/events` | GET | Recent agent event log |
| `/agents` | GET | Registered agents + skills |
| `/docs` | GET | Interactive API explorer |

---

## Principles

1. **Alfred routes. Agents act.** Alfred owns no domain data.
2. **Confirm before real-world actions.** Always. Hard-wired into AgentResponse.
3. **Agents are independently callable.** Bypass Alfred via direct REST if needed.
4. **One env var to swap LLM.** Provider abstraction in `shared/llm_provider.py`.
5. **Cheap until proven necessary.** Local Ollama first, cloud API when quality demands it.

---

## Known Limitations (Phase 1)

- No persistent session memory — Alfred forgets context between conversations
- Pending confirmations lost on server restart (in-memory dict, not Redis yet)
- Price comparison not implemented — Swiggy MCP in Phase 2
- Dashboard is interim HTML file — Next.js build in progress
- Vision / camera not available until Phase 3 hardware setup
