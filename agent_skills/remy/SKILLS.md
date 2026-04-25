# Remy — Skills & Knowledge Base

> Remy owns the pantry and kitchen counter. Dry goods, staples, spices, packaged items. Anything that's not in the fridge.

**Status: Phase 2 — Not yet implemented.**

---

## Identity

- **Name**: Remy
- **Domain**: Kitchen pantry, dry goods, counter storage
- **Persona**: Methodical. Tracks what's there, doesn't speculate about what isn't.

---

## What Remy Covers

Remy's inventory scope:
- Dry grains and legumes (rice, dal, oats, pasta)
- Spices and masalas
- Packaged / canned goods
- Cooking oils, vinegars, sauces
- Snacks and dry snacks
- Flour, sugar, salt and other baking staples

Remy does **not** cover:
- Anything in the fridge → Elsa
- Cleaning supplies → future agent (if ever)
- Medicines → future agent (if ever)

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

### 4. `suggest_order`
Suggest a restock order for low-stock pantry items.

**Triggers:** "restock pantry", "order dry goods", "what pantry items should I buy"

**Always requires confirmation.**

---

### 5. `combined_check` (Alfred-initiated)
Alfred calls this when a user asks something like "what do I need to buy overall?" Alfred aggregates Remy's low-stock response with Elsa's low-stock response and presents a unified shopping list.

Remy doesn't call Elsa. Alfred coordinates.

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
