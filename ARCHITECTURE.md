# Architecture — Project Roomy

Last updated: April 2026 — reflects Phase 2 implementation (complete)

---

## Current State

Phase 2 complete. All backend agents operational with mock Swiggy MCP integration.

```
✅ shared/          Core contracts and utilities
✅ agent_skills/    Alfred, Elsa, Remy, Lebowski (all operational)
✅ interfaces/      Telegram bots (4 bots active)
📋 roomie-web/      Next.js dashboard (Phase 3 - next)
```

---

## Agents — Responsibility Matrix

| Agent | Domain | Core Responsibilities | Phase |
|-------|--------|----------------------|-------|
| **Alfred** | Orchestration | Intent routing, multi-agent coordination, confirmation gate, session management, conversational interface | 1-2 ✅ |
| **Elsa** | Fridge inventory | Stock tracking, low stock alerts, inventory queries, CRUD operations | 1 ✅ |
| **Remy** | Kitchen operations | Recipe parsing (3 modes), meal planning, missing ingredient compilation, pantry inventory | 2 ✅ |
| **Lebowski** | Procurement | Catalog matching (Hinglish → SKU), pricing, cart building, order placement (mock MCP ready) | 2 ✅ |
| **Finn** | Analytics | Household spend, savings vs retail, purchase patterns, budget alerts | 4 🔜 |
| **Iris** | Smart home | Device control, automation rules, energy monitoring | 4 🔜 |

### Inter-Agent Communication Pattern

**Recipe-to-Cart Flow (Target Architecture):**
```
User: "I want to make Paneer Lababdar tonight"
  ↓
Alfred: routes intent to Remy (kitchen domain)
  ↓
Remy: parses recipe → extracts ingredients
  ↓ asks Elsa
Elsa: "Here's what's in the fridge: paneer (200g), tomatoes (4)"
  ↓ asks self (Remy's pantry)
Remy: "Pantry has: onions, ginger. Missing: kasuri methi, cream"
  ↓ compiles missing items
Remy → Lebowski: "Need: kasuri methi (10g), cream (200ml)"
  ↓
Lebowski: matches to Swiggy catalog using Hinglish translation + IDF search
          → "MDH Kasuri Methi 25g ₹35" + "Amul Fresh Cream 250ml ₹65"
          → builds cart with pack-size rounding
  ↓
Lebowski → Alfred: cart ready for confirmation
  ↓
Alfred → User: "Cart ready: 2 items, ₹100. Confirm?"
```

**Phase 1 Shortcut (POC):**  
Elsa handles recipe parsing directly (no Remy, no Lebowski) to validate the full flow.  
Refactor in Phase 2 when Remy + Lebowski ship.

**Catalog Matching Strategy (Lebowski):**  
Inspired by [Recipe-to-Cart reference implementation](https://lnkd.in/gVwWnFJP):
- Hinglish translation: `haldi → turmeric`, `kasuri methi → dried fenugreek leaves`
- IDF-weighted token search across 200+ item catalog of real Indian brands
- Pack-size rounding: recipe needs 10g kasuri methi → match 25g pack (smallest available)
- Primary noun tiebreaking: "Amul butter" beats "Mother Dairy butter spread" for "butter"
- No fuzzy-match library, no vendor lock-in — pure tokenization + scoring in ~100 lines

---

## System Layers

```
┌─────────────────────────────────────────────────────┐
│                   INTERFACE LAYER                   │
│   Telegram Bots          │  Next.js Web (Phase 3)   │
│   • Alfred ✅            │  • Dashboard   📋        │
│   • Elsa ✅              │  • Recipe Search 📋       │
│   • Remy ✅              │  • Meal Planner  📋       │
│   • Lebowski ✅          │  • Shopping Cart 📋       │
│   polling mode, local    │  roomie-web/, Vercel     │
└───────────────────┬─────────────────────┬───────────┘
                    │ REST                │ REST + SWR
                    ▼                     ▼
┌─────────────────────────────────────────────────────┐
│              ORCHESTRATION LAYER                    │
│              Alfred  (:8000) ✅                     │
│   /message → route_intent → dispatch → confirm gate │
│   /confirm → execute or cancel pending action       │
│   /status  → aggregate all agent statuses           │
│   /events  → agent_events table (dashboard feed)    │
│   /agents  → registered agent registry              │
│   /        → health check                           │
└────────────┬────────────────────────────────────────┘
             │ in-process call (shared memory)
             ▼                    
┌────────────────────┐   ┌──────────────────────────┐
│  ELSA (:8001)      │   │  REMY (:8002)            │
│  Fridge inventory  │   │  Kitchen + pantry        │
│  ✅ Phase 1-2      │   │  ✅ Phase 2              │
└────────────────────┘   └──────────────────────────┘

┌────────────────────┐   ┌──────────────────────────┐
│ LEBOWSKI (:8003)   │   │  Future agents           │
│ Procurement        │   │  register via            │
│ ✅ Phase 2         │   │  register_agent()        │
└────────┬───────────┘   └──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│                  STORAGE LAYER                      │
│   SQLite: data/roomy.db ✅                          │
│   Tables: inventory_items, pantry_items,            │
│           agent_events                              │
└─────────────────────────────────────────────────────┘
```

---

## Folder Structure (Actual)

```
Desktop/meh/roomie/
├── dashboard.html              ← Interim dashboard (served by Alfred at GET /)
├── .env / .env.example
├── requirements.txt
├── ARCHITECTURE.md
├── ROADMAP.md
├── HARDWARE_CHECKLIST.md
├── README.md
│
├── agent_skills/               ← All agent code + skills docs
│   ├── __init__.py
│   ├── alfred/
│   │   ├── __init__.py
│   │   ├── main.py             ← FastAPI app, entry point
│   │   ├── router.py           ← Intent classification + agent dispatch
│   │   └── SKILLS.md
│   ├── elsa/
│   │   ├── __init__.py
│   │   ├── main.py             ← ElsaAgent implementation
│   │   └── SKILLS.md
│   ├── remy/                   ← Phase 2: Kitchen agent
│   │   ├── __init__.py
│   │   ├── main.py             ← Recipe parsing, meal planning, pantry
│   │   └── SKILLS.md
│   ├── lebowski/               ← Phase 2: Procurement agent
│   │   ├── __init__.py
│   │   ├── main.py             ← Catalog matching, cart building
│   │   ├── catalog_matcher.py  ← Hinglish translation + IDF search
│   │   └── SKILLS.md
│   ├── finn/   (stub Phase 4)
│   └── iris/   (stub Phase 4)
│
├── shared/                     ← Contracts used by all agents
│   ├── __init__.py
│   ├── base_agent.py           ← BaseAgent ABC
│   ├── models.py               ← AgentResponse, Intent, schemas
│   ├── llm_provider.py         ← LLM abstraction
│   └── db.py                   ← SQLAlchemy setup + all table models
│
├── interfaces/
│   ├── __init__.py
│   └── telegram/
│       ├── __init__.py
│       └── bot.py              ← alfred_roomie_bot
│
├── roomie-web/                 ← Next.js dashboard (to be initialized)
│
├── scripts/
│   └── start_dev.sh
│
└── data/
    └── roomy.db                ← SQLite database
```

---

## Key Design Decisions

### 1. agent_skills/ as the agent container
Agents live in `agent_skills/` rather than root-level folders. This keeps the root clean and makes the agent registry explicit — everything in `agent_skills/` is an agent.

### 2. In-process vs HTTP agent calls
In Phase 1, Alfred imports ElsaAgent directly and calls it in-process. This avoids running two servers during development. The same `BaseAgent` interface works for HTTP calls in Phase 2+ — only the dispatch mechanism in `router.py` changes, not the agents themselves.

### 3. LLM does two jobs in Alfred
- **Routing**: classify intent, pick target agent + skill, extract parameters
- **Agent tasks**: recipe parsing, natural language interpretation in Elsa

These are separate calls with separate prompts. Routing uses `json_mode=True` and a structured output prompt. Agent tasks use task-specific prompts.

### 4. Parameter extraction is in the routing prompt
Alfred's routing prompt explicitly tells the LLM to extract `item`, `quantity`, `unit`, `url` from the message and put them in `parameters`. This means agents receive structured data — they don't need to re-parse natural language.

This was a bug in the initial implementation (empty `{{}}` parameters template) that has been fixed.

### 5. Dashboard architecture decision
**Interim**: Single `dashboard.html` served by Alfred at `GET /`. Uses vanilla JS, calls Alfred API.

**Phase 1 target**: Next.js project in `roomie-web/`. Deployed to Vercel (free). Alfred stays local + ngrok for Telegram webhook. Dashboard on Vercel calls Alfred via ngrok URL.

This split means the dashboard is always accessible (Vercel CDN) even when Alfred is temporarily down — it just shows a "connecting" state.

### 6. Confirmation gate
`AgentResponse.needs_human()` returns True if `requires_confirmation=True` OR `confidence < 0.85`. Alfred parks the response in `pending_confirmations` dict (in-memory, Phase 1) and returns an `awaiting_confirmation` status. The interface (Telegram buttons or dashboard confirm modal) resolves it via `POST /confirm`.

Phase 2: Move `pending_confirmations` to Redis so confirmations survive server restarts.

---

## LLM Provider — Current Config

**Multi-LLM Routing (Phase 2):**

Alfred automatically selects the best model for each task:

| Task Type | Model | Use Case |
|-----------|-------|----------|
| `chat` | `qwen2.5:7b` | Conversations, routing, general queries |
| `vision` | `qwen2.5vl:7b` | Image analysis (photo inventory scanning) |
| `code` | `qwen2.5-coder:7b` | Code generation tasks |
| `reasoning` | `deepseek-r1:8b` | Complex logical reasoning |
| `fast` | `qwen2.5-coder:1.5b` | Quick responses where accuracy can trade for speed |

**Model Selection Logic:**
```python
# In shared/llm_provider.py
MODEL_ROUTING = {
    "chat": "qwen2.5:7b",
    "vision": "qwen2.5vl:7b",
    "code": "qwen2.5-coder:7b",
    "reasoning": "deepseek-r1:8b",
    "fast": "qwen2.5-coder:1.5b"
}

def select_model(task_type: str = "chat") -> str:
    return MODEL_ROUTING.get(task_type, MODEL_ROUTING["chat"])
```

**Provider:**  
- Primary: `ollama` (local, no API cost)
- Fallback: `claude-haiku-4-5-20251001` (set `LLM_PROVIDER=claude` in .env)

**Check logs for model selection:**
```
[LLM] Using model: qwen2.5:7b
```

Switch to Claude Haiku when:
- JSON routing misroutes more than ~1 in 15 messages
- Recipe parsing results are poor quality
- You want faster responses
- Ollama is unavailable

---

## API Surface (Alfred)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Serve dashboard HTML |
| POST | `/message` | Main entry — route message, return result or confirmation request |
| POST | `/confirm` | Resolve a pending confirmation (confirmed or cancelled) |
| GET | `/status` | Alfred health + all agent statuses |
| GET | `/events` | Recent agent_events (last 50, newest first) |
| GET | `/agents` | Registered agents + their skill definitions |
| GET | `/docs` | FastAPI auto-generated API explorer |

---

## Dashboard — Next.js Scope (Phase 1)

To be built in `roomie-web/`. Six views:

| View | Data source | Notes |
|------|------------|-------|
| Overview | `/status` | Agent health, low stock count, pending actions |
| Inventory | `/message` (check_inventory) | Live fridge items, stock bars |
| Chat | `/message`, `/confirm` | Alfred conversation + inline confirmations |
| Event Log | `/events` | Agent activity feed, auto-refreshes via SWR |
| Analytics | `/events` (aggregated) | Item frequency, action counts — no spend data until Phase 2 |
| Task Board | `/status` (pending_confirmations) | Pending actions per agent, Jira-style cards |

---

## Hosting Plan

| Component | Phase 1 | Phase 2+ |
|-----------|---------|---------|
| Alfred API | Local Mac + ngrok | Fly.io free tier or Hetzner |
| Dashboard | Vercel (free) | Same |
| DB | SQLite local | Stays local until concurrent writes needed |
| Telegram webhook | ngrok URL | Same public URL as Alfred |
