# 🏠 Project R.O.O.M.I.E

> A modular multi-agent home assistant. Each agent owns a domain of your home. Alfred ties them together (Random Operators On My Individual Errands)

---

## Current Status — Phase 2 Complete ✅

| Component | Status |
|-----------|--------|
| Backend (Alfred, Elsa, Remy, Lebowski) | ✅ All Operational |
| Telegram bots (4 bots) | ✅ Running |
| Recipe-to-Cart Flow | ✅ Working (mock MCP) |
| Multi-LLM Routing | ✅ Implemented |
| Dashboard (Next.js) | 📋 Phase 3 (next) |
| Real Swiggy Integration | 📋 Ready (pending credentials) |

---

## Agents

| Agent | Domain | Phase | Status |
|-------|--------|-------|--------|
| **Alfred** | Orchestrator — routes intent, conversation, multi-LLM routing | 1-2 | ✅ Live |
| **Elsa** | Fridge inventory — stock tracking, low stock alerts, CRUD ops | 1 | ✅ Live |
| **Remy** | Kitchen — recipe parsing (3 modes), meal planning, pantry inventory | 2 | ✅ Live |
| **Lebowski** | Procurement — catalog matching, Hinglish translation, cart building, mock orders | 2 | ✅ Live |
| **Finn** | Household spend analytics | 4 | Future |
| **Iris** | Smart home device control | 4 | Future |

### Recipe-to-Cart Flow ✅ WORKING

User: "Can I make Paneer Tikka?"  
→ **Remy** parses recipe ingredients  
→ Checks **Elsa** (fridge) + **Remy** (pantry)  
→ Returns missing items: "kasuri methi 10g, cream 200ml"  
→ **Lebowski** translates Hinglish + matches catalog  
→ Builds cart: "MDH Kasuri Methi 25g (₹35), Amul Cream 250ml (₹65)"  
→ User confirms → Mock order placed (ready for real Swiggy API)

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
| Agents | Alfred, Elsa, Remy, Lebowski | ✅ |
| LLM (local) | Ollama (multi-model routing) | ✅ |
| LLM (cloud) | Claude Haiku / GPT-4o-mini | swap via `.env` |
| Database | SQLite | ✅ |
| Telegram | python-telegram-bot (4 bots) | ✅ |
| Dashboard | Next.js + Tailwind (roomie-web/) | 📋 Phase 3 |
| Hosting | Local (development) | ✅ |

---

## Quickstart

```bash
cd ~/Desktop/meh/roomie

# Start everything (Alfred API + all 4 Telegram bots)
bash scripts/start_dev.sh
```

This starts:
- **Alfred API** on port 8000
- **Telegram bots:** Alfred, Elsa, Remy, Lebowski (if tokens configured)
- **All agents:** Registered and operational

**Verify health:**
```bash
python3 scripts/health_check.py
```

**Run tests:**
```bash
python3 scripts/test_all.py
```

**Endpoints:**
- Health check: `http://localhost:8000/`
- API explorer: `http://localhost:8000/docs`
- Message endpoint: `POST http://localhost:8000/message`

---

## Environment Variables (`.env`)

```bash
# LLM Provider (Multi-model routing in Phase 2)
LLM_PROVIDER=ollama                    # ollama | claude | openai
OLLAMA_MODEL=qwen2.5:7b               # Default chat model
OLLAMA_URL=http://localhost:11434

# For cloud LLM (set LLM_PROVIDER=claude or LLM_PROVIDER=openai)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Telegram Bots (get tokens from @BotFather)
TELEGRAM_TOKEN_ALFRED=                 # Main orchestrator bot
TELEGRAM_TOKEN_ELSA=                   # Fridge inventory bot
TELEGRAM_TOKEN_REMY=                   # Recipe & pantry bot (optional)
TELEGRAM_TOKEN_LEBOWSKI=               # Shopping bot (optional)
ALLOWED_TELEGRAM_USER_IDS=            # Your Telegram user ID from @userinfobot

# Database
DATABASE_URL=sqlite:///./data/roomy.db

# Swiggy MCP (for real integration - Phase 3)
SWIGGY_API_KEY=                       # Pending credentials
SWIGGY_MCP_BASE_URL=https://mcp.swiggy.com/im
```

---

## Project Structure

```
roomie/
├── agent_skills/
│   ├── alfred/        main.py, router.py, SKILLS.md
│   ├── elsa/          main.py, SKILLS.md (fridge inventory)
│   ├── remy/          main.py, SKILLS.md (kitchen + pantry) — Phase 2
│   ├── lebowski/      main.py, catalog_matcher.py, SKILLS.md (procurement) — Phase 2
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
