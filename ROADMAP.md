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

## ✅ Phase 2: Recipe & Procurement (COMPLETE)

**Goal:** Recipe → Missing ingredients → Swiggy cart (all in Telegram)  
**Status:** Complete with mock Swiggy MCP integration  
**Actual time:** 6 hours

### 2.1 Remy Agent - Recipe Parsing ✅ COMPLETE
**Status:** Implemented with 3 parsing modes  
**Actual time:** 2.5 hours

**Features:**
- ✅ Parse recipe from URL (web_fetch → LLM extract)
- ✅ Parse recipe from copy-paste text
- ✅ Parse recipe from dish name (LLM generates ingredients)
- ✅ Check Elsa (fridge) + Remy (pantry) for available ingredients
- ✅ Return missing items list
- ✅ Pantry inventory management (CRUD operations)
- ✅ Meal suggestions based on available ingredients

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

### 2.2 Lebowski Agent - Catalog Matching ✅ COMPLETE
**Status:** Implemented with mock Swiggy MCP  
**Actual time:** 3 hours

**Features:**
- ✅ Hinglish translation (54 translations: haldi → turmeric, etc.)
- ✅ IDF-weighted catalog search (no external fuzzy libraries)
- ✅ Smart pack size rounding (need 10g → match 25g pack)
- ✅ SKU matching with mock Swiggy catalog (34 products)
- ✅ Cart building with category grouping + pricing
- ✅ Mock order placement (ready for real Swiggy API)

**Implementation:** 
- ✅ Simple token search + IDF scoring (no vendor lock-in)
- ✅ Hinglish dictionary JSON (`hinglish_dict.json` - 54 translations)
- ✅ Mock catalog JSON (`mock_catalog.json` - 34 products across 7 categories)
- ✅ **Mock Swiggy MCP** for development (switch to real API when credentials available)

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
- `agent_skills/lebowski/mock_catalog.json` - Mock Swiggy catalog

**Note:** Currently using mock MCP - switch to real Swiggy credentials when available

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

### 2.4 Multi-Platform Comparison (Future Enhancement)
**Goal:** Compare prices across Swiggy Instamart, Zomato, and Zepto  
**Estimated time:** 2-3 hours per platform

**Features:**
- **Zomato MCP Integration** - Access Zomato Instamart catalog and pricing
- **Zepto MCP Integration** - Access Zepto catalog and pricing
- **Price Comparison** - Side-by-side comparison across platforms
- **Best Deal Recommendation** - Highlight cheapest option per item
- **Platform Switching** - Allow user to select preferred platform

**Example:**
```
User: "Compare prices for milk and eggs"
Lebowski: "Price comparison across platforms:
           
           Amul Milk 1L:
           • Swiggy: ₹60 (15min delivery)
           • Zomato: ₹58 (12min delivery) ✅ Cheapest
           • Zepto: ₹62 (10min delivery)
           
           Eggs (6pc):
           • Swiggy: ₹42 (15min) ✅ Cheapest
           • Zomato: ₹45 (12min)
           • Zepto: ₹44 (10min)
           
           Recommendation: Order milk from Zomato, eggs from Swiggy
           Total savings: ₹5"
```

**Implementation Strategy:**
- Same catalog matching logic for all platforms
- Standardize product data across platforms
- Cache catalog data to minimize API calls
- Let user set platform preferences (default, preferred brands)

**Files:**
- `agent_skills/lebowski/zomato_mcp.py` - Zomato MCP client
- `agent_skills/lebowski/zepto_mcp.py` - Zepto MCP client
- `agent_skills/lebowski/price_comparator.py` - Multi-platform comparison logic

**Note:** Implement after Swiggy integration is stable. Check for Zomato & Zepto MCP availability.

---

### End-to-End Test (30 min)
1. User shares recipe URL → Remy parses
2. Remy checks Elsa for availability → Returns missing items
3. User: "Order missing items" → Lebowski matches catalog
4. Lebowski presents cart → User confirms
5. Order placed via Swiggy API (or manual for now)

**Phase 2 Complete:** Recipe-to-cart workflow functional in Telegram

---

## 🌐 Phase 3: Next.js Web Dashboard (NEXT)

**When:** Now that all agents work end-to-end  
**Why:** Backend API exists, just need frontend UI  
**Estimated time:** 12-15 hours total

### 3.1 Dashboard Foundation (2 hours)
**Features:**
- Next.js 14 setup with App Router
- API client for Alfred communication
- Dashboard home with system status
- Quick stats (fridge items, pantry items, recent orders)
- Quick action buttons (Add Item, Parse Recipe, Build Cart)

**Tech Stack:**
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS + shadcn/ui
- React Query for API state
- Connects to Alfred API (:8000)

---

### 3.2 Inventory Managers (2 hours)
**Features:**
- **Fridge Manager** - Visual inventory grid with CRUD operations
- **Pantry Manager** - Similar to fridge for dry goods
- Search/filter capabilities
- Category grouping
- Low stock indicators
- Expiry warnings (fridge only)

---

### 3.3 Recipe Parser Interface (2 hours)
**Features:**
- 3 input modes (tabs): URL, Text, Dish Name
- Parse button with loading state
- Ingredient display with availability check
- Missing items highlighted
- "Shop Now" button → redirects to cart with missing items

---

### 3.4 Shopping Cart Builder (2 hours)
**Features:**
- Accept items from recipe parser
- Display matched products from catalog
- Group by category (dairy, spices, etc.)
- Show pack sizes, prices, SKUs
- Calculate subtotal + delivery fee
- "Place Order" button (mock Swiggy)
- Order confirmation modal

---

### 3.5 Real Swiggy Integration (2 hours)
**When:** Swiggy credentials available  
**Changes Required:**
- Update `.env` with real Swiggy API key
- Replace mock MCP calls in `lebowski/main.py`:
  - `_match_catalog()` → real product search
  - `_place_order()` → real order API
- Test with small orders first
- Error handling for API failures

**Files to Update:**
- `agent_skills/lebowski/main.py`
- `.env` (add SWIGGY_API_KEY, SWIGGY_MCP_URL)

---

### 3.6 Multi-Platform Comparison (2 hours)
**Goal:** Compare prices across Swiggy, Zomato, Zepto  
**Features:**
- Create new `ShopperAgent` for multi-platform logic
- Price comparison table
- Best deal recommendations
- User preference system (price vs speed)

**Files to Create:**
- `agent_skills/shopper/main.py`
- `.env` additions: ZOMATO_API_KEY, ZEPTO_API_KEY

---

### 3.7 Polish & Deploy (2 hours)
**Features:**
- UI/UX improvements
- Performance optimization
- Docker setup
- Production deployment
- Error tracking (Sentry)

### Architecture
```
Next.js Frontend (:3000)
       ↓
  Alfred API (:8000)
       ↓
  Agents (Alfred, Elsa, Remy, Lebowski)
       ↓
  Database (SQLite → PostgreSQL in prod)
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
│  • Alfred (orchestrator)│  • Dashboard    🔄     │
│  • Elsa (fridge) ✅     │  • Recipe Search 🔄    │
│  • Remy (pantry) ✅     │  • Meal Planner  🔄    │
│  • Lebowski (shop) ✅   │  • Shopping Cart 🔄    │
└──────────────┬──────────┴───────────────────────┘
               │
         Alfred API (:8000) ✅
               │
        ┌──────┴──────┐
        │   Agents    │
        ├─────────────┤
        │ • Alfred ✅ │ ← Conversational + Router
        │ • Elsa ✅   │ ← Fridge inventory
        │ • Remy ✅   │ ← Recipe parser + Pantry
        │ • Lebowski✅│ ← Procurement + Catalog
        └──────┬──────┘
               │
        ┌──────┴──────┐
        │  Database   │
        │  SQLite ✅  │
        └─────────────┘
```

**Phase 2 Status:** All agents operational with mock Swiggy MCP

---

## Timeline Estimate

- **Phase 1:** ✅ Complete (Telegram bots + Elsa agent)
- **Phase 2:** ✅ Complete (~6 hours) - Recipe + procurement with mock MCP
- **Phase 3:** 🔄 Next (~12-15 hours) - Next.js dashboard + real Swiggy integration
- **Phase 4:** Optional - Hardware integration
- **Phase 5:** Future (~4-6 hours) - Deployment & polish

**Total to production MVP:** Phase 1 + 2 complete ✅  
**Remaining for web interface:** Phase 3 (~12-15 hours)
