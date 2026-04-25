# Project Roadmap

## ✅ Phase 1: Multi-Agent Telegram Bot System (COMPLETE)

**Status:** Working with polish items remaining

### Achievements
- 4 Telegram bots operational (Alfred, Elsa, Remy, Lebowski)
- Force-agent routing with action classification
- Greeting optimization (no LLM call)
- Photo inventory scanning with vision LLM
- Group chat support with @mention
- Inventory add/check operations

### Known Issues (FINAL_FIXES.md)
- [ ] Math operations (add/set/subtract) - need 3 operation types
- [ ] Image import error - InventoryDB → InventoryItemDB
- [ ] JSON formatting - need format_result() update
- [ ] Remove "— agent" signatures
- [ ] Group chat case sensitivity
- [ ] Model selection - use qwen2.5:7b for chat, qwen2.5vl:7b for photos

**Estimated fix time:** 25 minutes

### Next Immediate Enhancements (Phase 1.5)
- [ ] **Item expiry tracking** - Add expiry_date field to inventory
- [ ] **Natural language improvements** - Less rigid interaction
  - Alert when items expire in <3 days
  - Prioritize expiring items in meal suggestions
  - Weekly "use soon" notifications
  - Example: "Milk expires in 2 days, eggs in 5 days"

- [ ] **Intent-based photo captions** - Use caption to determine operation
  - "Adding these" → Add detected items to inventory
  - "Using these" / "Took these" → Subtract from inventory
  - "Scan everything" / No caption → Full inventory sync (current behavior)
  - Reduces LLM complexity for simple operations
  - Example: Send photo + "Using these" → Only subtracts detected items

---

## 🔄 Phase 2: Recipe & Procurement (NEXT SESSION)

**Goal:** Recipe → Missing ingredients → Swiggy cart (all in Telegram)  
**Estimated time:** 6-7 hours

### 2.1 Remy Agent - Recipe Parsing (2-3 hours)
**Features:**
- Parse recipe from URL (web_fetch → LLM extract)
- Parse recipe from copy-paste text
- Parse recipe from dish name (web_search → fetch → parse)
- Check Elsa for available ingredients
- Return missing items list

**Example:**
```
User: "Can I make this? https://recipe.com/pasta"
Remy: "Spaghetti Carbonara needs:
       ✅ Have: eggs (10), bacon (200g), parmesan
       ❌ Need: spaghetti (500g), black pepper (50g)"
```

**Files:**
- `agent_skills/remy/main.py` - New agent implementation
- `agent_skills/remy/skills.py` - Recipe parsing skills
- Register with Alfred on startup

---

### 2.2 Lebowski Agent - Catalog Matching (3-4 hours)
**Features:**
- Hinglish translation (haldi → turmeric)
- IDF-weighted catalog search (~100 lines)
- Pack size rounding (need 50g → match 100g pack)
- SKU matching to Swiggy Instamart
- Cart building with prices

**Strategy:** 
- No fuzzy-match libraries (vendor lock-in)
- Simple token search + primary noun tiebreaking
- Hinglish dictionary JSON (curated list)

**Example:**
```
Remy: "Need: spaghetti (500g), black pepper (50g)"
Lebowski: "Found on Instamart:
           • Barilla Spaghetti 500g - ₹180
           • Catch Black Pepper 100g - ₹95
           Total: ₹275"
User: "Add to cart"
Lebowski: "Cart ready. Confirm order? (₹275 + delivery)"
```

**Files:**
- `agent_skills/lebowski/main.py` - Catalog matching agent
- `agent_skills/lebowski/hinglish_dict.json` - Translation dictionary
- `agent_skills/lebowski/catalog.py` - Search logic

---

### 2.3 Meal Planning (Remy Extension) (1-2 hours)
**Features:**
- Weekly meal suggestions based on fridge inventory
- Optimize for minimal new purchases
- Balance nutrition + variety

**Example:**
```
User: "Plan this week's dinners"
Remy: "Based on your fridge:
       Mon: Pasta carbonara (have eggs, bacon, need pasta)
       Tue: Stir-fry (have veggies, need soy sauce)
       Wed: Omelette (have eggs, cheese)
       
       Missing for week: pasta, soy sauce (₹200 total)"
```

---

### End-to-End Test (30 min)
1. User shares recipe URL → Remy parses
2. Remy checks Elsa for availability → Returns missing items
3. User: "Order missing items" → Lebowski matches catalog
4. Lebowski presents cart → User confirms
5. Order placed via Swiggy API (or manual for now)

**Phase 2 Complete:** Recipe-to-cart workflow functional in Telegram

---

## 🌐 Phase 3: Next.js Web Dashboard (After Phase 2)

**When:** Once all agents work end-to-end in Telegram  
**Why:** Backend API exists, just need frontend UI  
**Estimated time:** 4-6 hours

### Features
1. **Dashboard** - Fridge inventory, recent events, low stock alerts
2. **Recipe Search** - URL input → ingredient check → cart
3. **Shopping Cart** - Review items, prices before ordering
4. **Meal Planner** - Calendar view, drag-drop meals

### Tech Stack
- Next.js 14 (App Router)
- Tailwind CSS + shadcn/ui
- Connects to Alfred API (:8000)

### Architecture
```
Next.js Frontend (:3000)
       ↓
  Alfred API (:8000)
       ↓
  Agents (Elsa, Remy, Lebowski)
```

**Phase 3 Complete:** Web + Telegram interfaces both working

---

## 🔌 Phase 4: Hardware Integration (Future)

**Features:**
- Raspberry Pi with weight sensors
- Barcode scanner for quick add
- RFID tags for containers
- Auto-detect when items run low

**Hardware:**
- Load cells (HX711) for weight
- USB barcode scanner
- Camera module for OCR
- LED indicators

**Estimated time:** 8-10 hours (hardware setup + software integration)

---

## 🚀 Phase 5: Deployment & Polish (Future)

**Features:**
- Alfred API on cloud (Railway/Render)
- Telegram bots running 24/7
- Database migration to PostgreSQL
- Webhook mode for Telegram (instead of polling)
- Monitoring & logging
- Budget tracking & analytics

**Estimated time:** 4-6 hours

---

## Current Architecture

```
┌─────────────────────────────────────────────────┐
│                   INTERFACES                     │
├─────────────────────────────────────────────────┤
│  Telegram Bots          │  Next.js Web (Phase 3)│
│  • Alfred (orchestrator)│  • Dashboard           │
│  • Elsa (fridge) ✅     │  • Recipe Search       │
│  • Remy (kitchen) 🔄    │  • Meal Planner       │
│  • Lebowski (shop) 🔄   │  • Shopping Cart      │
└──────────────┬──────────┴───────────────────────┘
               │
         Alfred API (:8000)
               │
        ┌──────┴──────┐
        │   Agents    │
        ├─────────────┤
        │ • Elsa ✅   │
        │ • Remy 🔄   │ ← Phase 2
        │ • Lebowski🔄│ ← Phase 2
        └─────────────┘
```

---

## Timeline Estimate

- **Phase 1:** ✅ Complete (Telegram bots + Elsa agent)
- **Phase 2:** 1 session (~6-7 hours) - Recipe + procurement
- **Phase 3:** 1 session (~4-6 hours) - Next.js dashboard
- **Phase 4:** Optional - Hardware integration
- **Phase 5:** 1 session (~4-6 hours) - Deployment

**Total to working MVP:** 2-3 sessions (~15-20 hours)
