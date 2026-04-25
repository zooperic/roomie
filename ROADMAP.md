# Roadmap — Project Roomy

Last updated: April 2026

---

## Status Legend
- ✅ Done
- 🔄 In progress
- 📋 Scoped / next
- 🔜 Planned
- ❌ Not started

---

## Phase 0 — Foundation ✅ COMPLETE

- ✅ Monorepo structure (`agent_skills/`, `shared/`, `interfaces/`, `scripts/`)
- ✅ `shared/base_agent.py` — BaseAgent contract
- ✅ `shared/models.py` — AgentResponse, Intent, InventoryItem, SkillDefinition schemas
- ✅ `shared/llm_provider.py` — Provider abstraction (Claude, OpenAI, Ollama) behind one function
- ✅ `shared/db.py` — SQLite, all tables defined (inventory, orders, agent_events, price_comparisons)
- ✅ `.env.example` — All environment variables documented
- ✅ Planning docs: README, ARCHITECTURE, ROADMAP, HARDWARE_CHECKLIST
- ✅ Agent SKILLS.md files: Alfred, Elsa, Remy (stub), Finn (stub), Iris (stub)
- ✅ Alfred boots, registers Elsa, starts without errors
- ✅ DB initializes correctly

---

## Phase 1 — Alfred + Elsa + Interfaces

### Backend ✅ COMPLETE
- ✅ Elsa fully implemented: check_inventory, update_inventory, low_stock_check, parse_recipe, suggest_order
- ✅ Alfred intent routing — LLM classifies and dispatches to correct agent + skill
- ✅ Alfred parameter extraction from natural language messages
- ✅ Confirmation gate — requires_confirmation flow working end to end
- ✅ End-to-end loop validated: natural language → Alfred → Elsa → DB → response

### Telegram 🔄 IN PROGRESS
- ✅ Bot created: `alfred_roomie_bot`
- 📋 Add bot token to `.env` and test `/start`
- 📋 Validate full conversation loop via Telegram
- 📋 Test confirm/cancel inline buttons
- 📋 Group chat support — bot responds when tagged in a group (`@alfred_roomie_bot`)

### Dashboard 📋 SCOPED FOR P1
Full dashboard to be built as a **Next.js project** in `roomie-web/`.

**Views to build:**

| View | Description | Priority |
|------|-------------|----------|
| **Overview** | Alfred + agent status, low stock alerts, pending confirmations banner | P1 |
| **Inventory** | Live fridge items, stock bars, category filter, manual add/edit | P1 |
| **Chat** | Full Alfred chat panel with confirm/cancel actions inline | P1 |
| **Event Log** | Real-time agent activity feed (what each agent did and when) | P1 |
| **Analytics** | Spend over time, most ordered items, savings vs retail | P1 (basic) |
| **Task Board** | Pending actions per agent — Jira-style card view of what's queued | P1 |

**Tech decisions:**
- Next.js App Router in `roomie-web/`
- Tailwind CSS — monochromatic design system
- SWR for data fetching + auto-revalidation (no manual refresh needed)
- shadcn/ui for base components — override with custom styles
- No separate backend — dashboard calls Alfred's REST API directly

**What analytics can show in P1** (without Finn, just from existing DB):
- Items added/removed per day (from `agent_events`)
- Order suggestions made and confirmed/cancelled ratio
- Low stock frequency per item
- Most commonly checked items

Full spend analytics (₹ amounts, savings vs retail) come in Phase 2 when Swiggy MCP is live.


### Elsa — Full Phase 1 Scope (Fridge Agent)

#### Inventory Model
Each fridge item tracks:
- `name` — item name
- `brand` — optional (e.g. Amul, Britannia)
- `type` — category (dairy, produce, beverage, etc.)
- `quantity` — numeric count
- `volume` — size per unit (e.g. 1L, 500ml, 250g)
- `is_purchasable` — bool: whether this goes through Swiggy pipeline
- `container_label` — for home-cooked items (e.g. "Eric's Dal", "Eric's Chicken Curry")
- `container_count` — number of containers for cooked food

Home-cooked / curry items are tracked as named containers with a count only.
Only `is_purchasable=True` items enter the Swiggy order pipeline.

#### Input Methods
Two ways to update Elsa's inventory:

**1. Photo pipeline (primary)**
- You click a photo of fridge contents (nightly or as needed)
- Send photo to Alfred via Telegram or dashboard upload
- Vision LLM (`qwen2.5vl:7b` — already available locally) analyses contents
- Elsa calculates delta: what appeared, what disappeared vs last known state
- Delta presented to you for review before DB is updated
- You can manually override any item in the diff (name, quantity, volume, brand)
- Confirmed diff written to inventory

**2. Manual text input**
- Tell Alfred directly: "add 2L Amul milk", "I finished the curd"
- Elsa updates DB immediately, no confirmation needed for local writes

#### Routine Purchases
- Set recurring purchase rules per item: "buy milk every 5 days" or "reorder when quantity < 1"
- Elsa checks rules daily and surfaces due items as a suggested cart
- You confirm once → Swiggy order placed
- Manual one-off orders also supported: "order X from InstaMart now"

#### Pricing Intelligence (Dashboard Analytics)
Per purchasable item, Elsa tracks and displays:
- Price history over time (fetched from Swiggy MCP each time item is ordered or checked)
- Best time to buy — day-of-week or time-of-day pricing patterns
- Estimated days remaining based on current quantity + average usage rate
- Suggested reorder date: when to buy next given usage + price trend
- Cost per unit trend — flag when price spikes above 30-day average

Dashboard view: per-item pricing chart (line graph, price over time) + usage vs stock overlay.

#### Phase 1 Limitation (honest)
- Photo pipeline requires vision LLM. `qwen2.5vl:7b` is available locally but accuracy on fridge photos with mixed items varies. Expect manual corrections frequently until Phase 3 hardware (fixed camera angle, controlled lighting) improves consistency.
- Pricing trends need at least 2–3 weeks of order data before patterns are meaningful.
- Swiggy MCP pricing is Phase 2. Phase 1 pricing chart uses placeholder / manually entered prices.


---

### Exit Criteria for Phase 1 Complete
- [ ] Can add items, query fridge, get low stock alerts via Telegram
- [ ] Can share a recipe link → get missing ingredients → confirm order suggestion via Telegram
- [ ] Group chat: tag @alfred_roomie_bot in a group, get a response
- [ ] Dashboard: all 6 views functional, pulling live data from Alfred API
- [ ] Dashboard: chat panel works, confirm/cancel buttons function
- [ ] Dashboard: deployed to Vercel (free) for always-on access, Alfred stays local

---

## Phase 2 — Real Orders + Remy

- [ ] Swiggy MCP integration in Elsa — real prices, real order placement on confirmation
- [ ] Price comparison across platforms (InstaMart vs Blinkit)
- [ ] Remy agent — pantry/dry goods inventory (same pattern as Elsa)
- [ ] Alfred multi-agent queries — aggregates Elsa + Remy for combined shopping list
- [ ] Alfred persistent memory — dietary preferences, saved delivery address
- [ ] Dashboard analytics: real spend data, price trend charts, savings tracker
- [ ] Separate agent bots (elsa_roomie_bot etc.) — direct access bypassing Alfred
  - Refactor `TELEGRAM_TOKEN` → `TELEGRAM_TOKEN_ALFRED`, add `TELEGRAM_TOKEN_ELSA`, `TELEGRAM_TOKEN_REMY`
  - Split `interfaces/telegram/bot.py` → `alfred_bot.py`, `elsa_bot.py`, `base_bot.py` (shared logic)
  - `start_dev.sh` skips bots with blank tokens silently

---

## Phase 3 — Hardware (Fridge Camera)

- [ ] ESP32-CAM hardware setup (see HARDWARE_CHECKLIST.md)
- [ ] Vision LLM integration — `qwen2.5vl:7b` already available on Ollama
- [ ] MQTT bridge for hardware events
- [ ] Elsa `/scan` endpoint — image → inventory diff → confirmation
- [ ] Scheduled scans

---

## Phase 4 — New Agents + Scale

- [ ] Finn — household spend analytics agent
- [ ] Iris — smart home device control (requires hardware)
- [ ] SQLite → PostgreSQL migration if needed
- [ ] VPS deployment (Hetzner CX11 ~₹500/mo) when local isn't enough

---

## Agent Bot Strategy

Each agent can have its own Telegram bot for direct access:

| Bot | Talks to | When to create |
|-----|---------|----------------|
| `alfred_roomie_bot` ✅ | Alfred (all agents) | Phase 1 — primary interface |
| `elsa_roomie_bot` | Elsa directly | Phase 2 — when you want fridge queries without Alfred routing |
| `remy_roomie_bot` | Remy directly | Phase 2 — alongside Remy agent |

Direct agent bots bypass Alfred's LLM routing call — cheaper and faster for simple queries you know the destination of.
