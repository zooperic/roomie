# Lebowski — Skills & Knowledge Base

> Lebowski owns procurement. Catalog matching, cart building, order placement, price tracking. The procurement specialist.

**Status: Phase 2 — Not yet implemented.**

---

## Identity

- **Name**: Lebowski
- **Domain**: Procurement — catalog matching, pricing, cart building, order placement
- **Persona**: Methodical shopper. Matches ingredients to real SKUs, rounds pack sizes, tracks prices.

---

## What Lebowski Covers

**Procurement Operations:**
- Hinglish → SKU matching (haldi → turmeric → "Everest Turmeric Powder 100g")
- Pack-size rounding (recipe needs 10g → match 25g pack)
- Cart building and optimization
- Order placement via Swiggy MCP
- Price tracking and best-time-to-buy suggestions

Lebowski does **not** cover:
- Inventory tracking → Elsa (fridge), Remy (pantry)
- Recipe parsing → Remy
- Spend analytics → Finn (Phase 4)

---

## Planned Skills

### 1. `match_catalog(items)`
Match a list of ingredient names to Swiggy catalog SKUs.

**Triggers:** Internal — called by Alfred after Remy compiles missing items

**Input:** `["kasuri methi 10g", "cream 200ml", "paneer 200g"]`

**Flow:**
1. For each item:
   - Hinglish translation: `kasuri methi → dried fenugreek leaves`
   - Tokenize query
   - IDF-weighted search across catalog (200+ items)
   - Primary noun tiebreaking: "butter" in "Amul butter" scores higher than "butter" in "butter spread"
   - Pack-size rounding: if recipe needs 10g, match smallest pack ≥10g (e.g., 25g)
2. Return matched SKUs with prices

**Returns:** 
```json
[
  {
    "query": "kasuri methi 10g",
    "matched": "MDH Kasuri Methi 25g",
    "sku": "MDH-KM-25",
    "price": 35,
    "quantity": 1
  },
  {
    "query": "cream 200ml",
    "matched": "Amul Fresh Cream 250ml",
    "sku": "AMUL-FC-250",
    "price": 65,
    "quantity": 1
  }
]
```

**Catalog Matching Strategy (inspired by [Recipe-to-Cart](https://lnkd.in/gVwWnFJP)):**
- **No fuzzy-match library:** Pure tokenization + IDF-weighted scoring
- **Hinglish translation:** Pre-built dictionary (`haldi → turmeric`, `kasuri methi → dried fenugreek leaves`)
- **Primary noun tiebreaking:** Extract the main noun from query, boost matches where it appears early
- **Pack-size rounding:** Always round up to smallest available pack
- **Brand preference:** Favor popular brands (Amul, MDH, Everest) when multiple matches exist
- **~100 lines of code:** Zero vendor lock-in, pure Python logic

---

### 2. `build_cart(matched_items)`
Build a Swiggy cart from matched catalog items.

**Triggers:** Internal — called after `match_catalog`

**Flow:**
1. Group items by category (dairy, spices, produce)
2. Check for quantity discounts (e.g., buy 2 get 10% off)
3. Apply pack-size optimization (e.g., 2x100g vs 1x200g)
4. Calculate total price
5. Return cart summary

**Returns:**
```json
{
  "cart": [
    {"name": "MDH Kasuri Methi 25g", "qty": 1, "price": 35},
    {"name": "Amul Fresh Cream 250ml", "qty": 1, "price": 65}
  ],
  "total": 100,
  "savings": 0,
  "delivery_fee": 0
}
```

---

### 3. `place_order(cart)`
Place order via Swiggy MCP.

**Triggers:** Internal — called after user confirms cart

**Flow:**
1. Call Swiggy MCP `create_order` endpoint
2. Pass cart items, delivery address, payment method
3. Wait for order confirmation
4. Log order to `orders` table
5. Return order ID and estimated delivery time

**Returns:**
```json
{
  "order_id": "SWG-2026-12345",
  "status": "confirmed",
  "estimated_delivery": "2026-04-25T20:30:00Z",
  "total": 100
}
```

**Always requires confirmation before placing order.**

---

### 4. `track_prices(items)`
Track price history for frequently purchased items.

**Triggers:** "show price history for milk", "when should I buy eggs"

**Flow:**
1. Query `price_comparisons` table for item price history
2. Calculate 30-day average
3. Identify best day-of-week / time-of-day to buy
4. Flag current price as "good deal" or "wait"

**Returns:**
```json
{
  "item": "Amul Milk 1L",
  "current_price": 60,
  "avg_30d": 62,
  "recommendation": "Good time to buy (3% below average)",
  "best_day": "Monday",
  "best_time": "8-10 AM"
}
```

---

### 5. `compare_platforms(items)` **[Optional — Phase 2]**
Compare prices across InstaMart, Blinkit, Zepto.

**Triggers:** "compare prices for milk", "find cheapest eggs"

**Flow:**
1. Query multiple platform catalogs
2. Match item across platforms
3. Return price comparison table
4. Highlight cheapest option

**Returns:**
```json
{
  "item": "Amul Milk 1L",
  "platforms": [
    {"name": "Swiggy InstaMart", "price": 60, "delivery": "15 min"},
    {"name": "Blinkit", "price": 58, "delivery": "10 min"},
    {"name": "Zepto", "price": 62, "delivery": "12 min"}
  ],
  "cheapest": "Blinkit"
}
```

---

## Data Lebowski Owns

| Table | Purpose |
|-------|---------|
| `price_comparisons` | Price history per item per platform |
| `orders` | Order history (write-only, Finn reads for analytics) |
| `catalog_cache` | Local cache of Swiggy catalog (refreshed weekly) |

---

## Catalog Structure

Stored as JSON in `data/swiggy_catalog.json`:

```json
[
  {
    "sku": "MDH-KM-25",
    "name": "MDH Kasuri Methi",
    "brand": "MDH",
    "category": "spices",
    "weight": 25,
    "unit": "g",
    "price": 35,
    "aliases": ["kasuri methi", "dried fenugreek leaves", "methi leaves"],
    "last_updated": "2026-04-20T00:00:00Z"
  },
  ...
]
```

**Catalog refresh:** Weekly via Swiggy MCP `list_products` call. Scrapes 200+ most common Indian grocery items.

---

## Implementation Notes (for when Phase 2 starts)

- `lebowski/main.py` — `LebowskiAgent` class, implements `BaseAgent`
- `lebowski/catalog_matcher.py` — All matching logic (Hinglish, IDF, pack-size rounding)
- `lebowski/swiggy_mcp.py` — Swiggy MCP client wrapper
- Register in `alfred/main.py`: `register_agent(LebowskiAgent())`
- Alfred's routing will automatically discover Lebowski's skills

---

## Hinglish Translation Dictionary (Starter)

Expand this as you discover new mappings:

```python
HINGLISH_TO_ENGLISH = {
    "haldi": "turmeric",
    "dhaniya": "coriander",
    "jeera": "cumin",
    "kasuri methi": "dried fenugreek leaves",
    "methi": "fenugreek",
    "atta": "wheat flour",
    "besan": "chickpea flour",
    "maida": "all-purpose flour",
    "hing": "asafoetida",
    "imli": "tamarind",
    "kala namak": "black salt",
    "sendha namak": "rock salt",
    "chaat masala": "spice blend",
    # ... expand as needed
}
```

**Source:** Build this dictionary from user corrections. When a match fails, ask user for the correct mapping, store it.

---

## Known Challenges

| Challenge | Solution |
|-----------|----------|
| Pack-size variability | Always round up to smallest available pack, accept some waste |
| Brand preferences | Let user set preferred brands in Alfred's memory, Lebowski prioritizes those |
| Out-of-stock items | Fallback to second-best match, or suggest alternative brand |
| Price fluctuations | Track 30-day average, flag unusual spikes |
| Multi-platform comparison | Phase 2 feature, nice-to-have not blocker |

---

## Reference Implementation

[Recipe-to-Cart by Shubham Khatri](https://lnkd.in/gVwWnFJP):
- Built on Next.js 16 + Vercel AI Gateway (Claude Haiku)
- ~100 lines of TypeScript for catalog matching
- Deployed in a day
- Submitted to Swiggy Builders Club for real InstaMart MCP integration

**Key takeaways:**
1. No fuzzy-match library needed — tokenization + IDF scoring works
2. Hinglish translation is the hard part, but it's just a dictionary
3. Pack-size rounding is essential for groceries (nobody sells exactly 10g kasuri methi)
4. Primary noun tiebreaking prevents "butter" matching "butter spread"
5. Simple is better — 200-item catalog is plenty for POC

---

## Phase 2 Exit Criteria (Lebowski-specific)

- [ ] Catalog matcher handles Hinglish → SKU for 50+ common ingredients
- [ ] Pack-size rounding works correctly (always rounds up)
- [ ] Swiggy MCP integration: can place real order
- [ ] Price tracking: stores prices, calculates 30-day average
- [ ] Cart building: groups items, calculates total
- [ ] Full recipe-to-cart flow works end-to-end (Remy → Lebowski → order placed)
