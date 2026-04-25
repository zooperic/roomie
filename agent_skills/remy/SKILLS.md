# Remy — Skills & Knowledge Base

> Remy owns the kitchen: pantry inventory, recipe parsing, meal planning. The kitchen master.

**Status: Phase 2 — Not yet implemented.**

---

## Identity

- **Name**: Remy
- **Domain**: Kitchen operations — pantry inventory, recipe parsing, meal planning
- **Persona**: Methodical culinary planner. Knows what's in the pantry, parses recipes, compiles shopping lists.

---

## What Remy Covers

**Inventory Scope:**
- Dry grains and legumes (rice, dal, oats, pasta)
- Spices and masalas
- Packaged / canned goods
- Cooking oils, vinegars, sauces
- Snacks and dry snacks
- Flour, sugar, salt and other baking staples

**Kitchen Operations:**
- Recipe parsing and ingredient extraction
- Meal planning and recipe suggestions
- Missing ingredient compilation (cross-checks fridge + pantry)

Remy does **not** cover:
- Anything in the fridge → Elsa
- Order placement / procurement → Lebowski
- Cleaning supplies, medicines → out of scope

---

## Planned Skills

### 1. `check_inventory`
Check what's in the pantry or if a specific dry good is available.

**Triggers:** "do I have rice", "is there pasta", "pantry inventory", "what dry goods do I have"

**Returns:** Item name, quantity, unit. "Not tracked" if item isn't in DB — not "not available."

---

### 2. `update_inventory`
Add, update, or remove items from pantry inventory.

**Triggers:** "I bought a 5kg bag of rice", "add turmeric", "I finished the pasta", "update pantry"

**Rules:**
- Same as Elsa's update logic — quantity replaces existing, not added, unless message implies addition
- Does not require confirmation

---

### 3. `low_stock_check`
Identify pantry staples running low.

**Triggers:** "what pantry items are low", "what staples do I need", "pantry restock"

---

### 4. `parse_recipe(input)` **[NEW — Phase 2]**
Extract ingredients from various recipe inputs.

**Triggers:** 
- User pastes recipe URL
- User says dish name ("I want to make Paneer Lababdar")
- User copy-pastes recipe text
- User shares video link (Phase 3+)

**Supported Ingestion Modes:**

| Mode | Example Input | How It Works | Effort | Phase |
|------|---------------|--------------|--------|-------|
| **URL** | `https://recipe-blog.com/paneer` | `web_fetch(url)` → parse HTML → extract ingredients | **LOW** ✅ | 1 POC |
| **Copy-Paste Text** | User pastes full recipe | Direct LLM parsing (no fetch) | **LOW** ✅ | 1 POC |
| **Dish Name** | "Paneer Lababdar" | `web_search` → pick top recipe → fetch → parse | **MEDIUM** 🟡 | 1-2 |
| **Video/Reels** | `youtube.com/shorts/abc` | Transcript API OR vision frame analysis | **HIGH** ⚠️ | 3+ |

**Flow (URL mode):**
1. Detect input type (URL, text, dish name)
2. If URL: `web_fetch(url)` to get recipe HTML
3. If dish name: `web_search("dish_name recipe")` → pick top result → fetch
4. If copy-paste text: skip fetch, parse directly
5. LLM extracts structured ingredients: name, quantity, unit
6. Returns ingredient list to Alfred

**Returns:** `[{name: "paneer", quantity: 200, unit: "g"}, {name: "kasuri methi", quantity: 10, unit: "g"}, ...]`

**Video mode (Phase 3+ only):**
- Requires YouTube transcript API or vision model frame analysis
- High effort (~300 lines + dependencies)
- Implement only if heavily requested by users

---

### 5. `compile_missing_items(recipe)` **[NEW — Phase 2]**
Cross-check recipe ingredients against fridge (Elsa) + pantry (self), return missing items.

**Triggers:** Internal — called by Alfred after `parse_recipe`

**Flow:**
1. Receives parsed ingredient list
2. Asks Elsa: "Do you have paneer, tomatoes?"
3. Checks self (Remy's pantry): "Do I have kasuri methi, cream?"
4. Compiles missing items list
5. Returns to Alfred → Alfred hands off to Lebowski for procurement

**Returns:** `{missing: ["kasuri methi 10g", "cream 200ml"], have: ["paneer", "tomatoes"]}`

---

### 6. `suggest_meal(preferences)` **[NEW — Phase 2]**
Suggest recipes based on current fridge + pantry inventory and user preferences.

**Triggers:** "what can I cook tonight", "suggest a recipe", "meal ideas"

**Flow:**
1. Query Elsa for fridge contents
2. Query self for pantry contents
3. LLM suggests 2-3 recipes that can be made with available ingredients
4. Returns recipe suggestions with missing item count

**Returns:** `["Paneer Tikka Masala (2 items missing)", "Dal Tadka (all available)", ...]`

---

### 7. `combined_check` (Alfred-initiated)
Alfred calls this when a user asks something like "what do I need to buy overall?" Alfred aggregates Remy's low-stock response with Elsa's low-stock response and presents a unified shopping list.

Remy doesn't call Elsa. Alfred coordinates.

---

## Recipe-to-Cart Flow (Phase 2)

**User:** "I want to make Paneer Lababdar tonight"

```
Alfred routes to Remy
  ↓
Remy: parse_recipe(url) → extracts ingredients
  ↓
Remy: compile_missing_items(ingredients)
  → asks Elsa for fridge check
  → checks self for pantry
  → returns missing items list
  ↓
Alfred receives missing items
  ↓
Alfred hands off to Lebowski
  ↓
Lebowski: match_catalog(missing_items) → builds Swiggy cart
  ↓
Alfred presents cart to user for confirmation
```

---

## Data Remy Owns

| Table | Filter |
|-------|--------|
| `inventory` | `agent_owner = 'remy'` |
| `agent_events` | `agent = 'remy'` |

---

## Hardware Consideration (Phase 3+)

Options for passive pantry monitoring (in order of complexity):

1. **Manual input (Phase 2 default)** — You tell Remy what you bought. No hardware.
2. **Barcode scanner** — Scan items when adding/removing. USB scanner reads into a simple input form.
3. **Weight sensors** — Load cell under storage containers for staples (rice, dal, etc.). Most accurate for bulk items. Requires ESP32 + HX711 module.
4. **Shelf camera** — Similar to Elsa's fridge camera but harder — pantry shelves have more variety, more occlusion, and inconsistent lighting.

Recommended path: Start with manual input. Add barcode scanning if you find manual input annoying. Skip camera unless you've validated it works for Elsa first.

---

## Known Differences from Elsa

| Aspect | Elsa (Fridge) | Remy (Pantry) |
|--------|--------------|--------------|
| Environment | Cold, humid | Dry, room temp |
| Item turnover | Faster (perishables) | Slower (staples) |
| Hardware complexity | Higher (cold battery concern) | Lower |
| Vision viability | Moderate (few large items) | Lower (many small items, labels vary) |
| Low stock urgency | Higher (food spoils) | Lower (pantry staples last longer) |

---

## Implementation Notes (for when Phase 2 starts)

- Remy's `ElsaAgent` equivalent will be `RemyAgent` in `remy/main.py`
- Same `BaseAgent` interface, same REST contract
- Register in `alfred/main.py` with one line: `register_agent(RemyAgent())`
- Alfred's routing will automatically discover Remy's skills — no Alfred code changes
