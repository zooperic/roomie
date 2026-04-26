# ROOMIE Development Roadmap

**Last Updated:** April 26, 2026

---

## Status Summary

| Phase | Name | Status |
|-------|------|--------|
| 1 | Core Foundation | ✅ Complete |
| 2 | Recipe & Procurement | ✅ Complete |
| 3 | Web Dashboard | ✅ Complete |
| **4** | **Recipe Ecosystem** | **🔨 Active** |
| 5 | Social Media Import | 📋 Next |
| 6 | Charlie — Places Agent | 📋 Planned |
| 7 | Nutrition Intelligence | 📋 Planned |
| 8 | Hardware Integration | 📋 Planned |
| 9 | Multi-User & Cloud | 💭 Future |

---

## Phase 1–3 ✅ Complete

Foundation (Alfred, Elsa, Remy, Lebowski, Iris, Finn), SQLite DB, FastAPI, Telegram bots, Next.js dashboard (9 tabs), Swiggy OAuth, photo scanning, analytics. See git history.

---

## Phase 4: Recipe Ecosystem 🔨 Active

### Done in Phase 4 so far

**Recipe pipeline rewrite (Remy):**
- `recipe_pipeline.py` — real HTTP scraping via httpx, schema.org JSON-LD extraction (covers Hebbars, Archana's, Substack, Delish, etc.), HTML fallback
- Pydantic v2 schema: permissive for LLM output → normalized to strict canonical units
- Unit normalization: "strand"→piece, "teaspoon"→tsp, "knob"→piece, etc. (20+ mappings)
- Post-processing: filter non-shoppable (water, ice), dedupe with quantity summing
- Two prompt tiers: slim (~395 tokens) for text/dish, full (~1499 tokens) for URL scraping
- DeepSeek thinking-tag stripping in `parse_json_response`

**Alfred routing fix:**
- `/recipes/parse` direct endpoint — bypasses LLM router entirely (was adding 30–120s)
- `parameters` field on `/message` — pre-extracted params skip `route_intent()` call
- 180s server-side timeout with clean error message
- `suggested_action_payload` now returned in all responses

**Remy agent:**
- Eliminated 2 unnecessary LLM calls per parse (Lebowski ask + error humanizer now use templates)
- Humane error messages without LLM (pattern-matched on error type)
- Servings scaling passed through full pipeline

**Lebowski:**
- Mock catalog expanded: 34 → 58 SKUs (added chicken, olive oil, parmesan, heavy cream, sun-dried tomatoes, herbs, stock, etc.)
- Cart response normalized: `matched_items` + `items` keys, `total_cost` + `total`, `successfully_matched`

**Web UI (RecipeParser.tsx):**
- Stage machine: idle → parsing → parsed → sending_to_lebowski → cart_ready → error
- Servings input inline
- Live progress bar with elapsed seconds + contextual messages (5s / 20s / 50s thresholds)
- Proper response reading from `/recipes/parse` (was reading wrong key)
- Timeout error distinguishes network failure vs slow model

**Telegram (remy_bot.py):**
- Servings extraction from natural language ("for 3 people")
- Ask-back with inline buttons (1 / 2 / 4 / 6 / Skip) before parsing
- Lebowski handoff confirm/deny inline buttons
- Recipe result formatted with available/missing breakdown

**Logging:**
- `httpx` logger set to WARNING in both Alfred and base_bot.py
- Telegram polling noise eliminated
- Server-side timing logs: `[Remy scrape]`, `[Remy pipeline]`, `[Remy]` with elapsed seconds

### Still to build in Phase 4

- **Recipe Library DB** — `RecipeDB` table (title, servings, ingredients JSON, tags, bookmarked, times_cooked)
- **5 API endpoints** — GET/POST/PATCH/DELETE /recipes
- **Recipes tab** in web dashboard — grid view, search, tag filter, bookmark star
- **"Save to Library"** button after any successful parse
- **Recipe detail panel** — servings scaler, ingredient list, "Cook now" CTA
- **LLM auto-tagging** on save (vegetarian, quick, Indian, etc.)
- **Telegram `/recipes` command** — browse bookmarked, re-cook

**Scope gate:** Phase 4 ships without social media ingestion. Those are Phase 5.

---

## Phase 5: Social Media Import 📋 Next

### Why yt-dlp and not a custom scraper

Instagram performs TLS fingerprinting — Python's `requests`/`httpx` are detected as bots at the handshake level, before headers are even read. Any DIY scraper breaks within hours. `yt-dlp` controls the TLS layer, is maintained by a large community, and updates automatically when platforms change. This is the same approach used by RecipeBro, ReciMe, CookingGuru, and the open-source `pickeld/social_recipes` (MIT licensed).

### Build order — easiest to hardest

| Source | Effort | Notes |
|--------|--------|-------|
| YouTube Shorts | Low | yt-dlp works perfectly, no auth |
| TikTok | Low | yt-dlp + caption usually complete |
| Pinterest | Low | Existing JSON-LD scraper likely works |
| Instagram caption-only | Low | yt-dlp `--skip-download`, needs cookies.txt |
| Photo/screenshot upload | Low | Vision LLM already in stack (qwen2.5vl) |
| Instagram Reel (video) | Medium | cookies.txt + faster-whisper transcription |

**Do not build Instagram first.** Start with YouTube + TikTok (no cookies needed).

### New dependencies

```
yt-dlp           # video/metadata download
faster-whisper   # local Whisper transcription
ffmpeg           # audio extraction (system package)
```

### New file: `agent_skills/remy/social_importer.py`

Wraps yt-dlp + Whisper. Called by `recipe_pipeline.py` when URL is a social media URL. Not a fork of `social_recipes` — borrows the pattern.

### Instagram cookies

Export logged-in cookies as `cookies.txt` (Netscape format) using "Get cookies.txt LOCALLY" browser extension. Personal use only.

---

## Phase 6: Charlie — Places Agent 📋 Planned

**Blocked on Phase 5** — Charlie reuses the social import pipeline.

Charlie manages saved dining places. Peer agent to Remy — same extraction machinery, different data model and UI.

**Ingestion:** Google Maps share links, Instagram restaurant posts, manual entry, shared Maps lists  
**Library:** cuisine tags, area, occasion, "want to try" / "been there", visit count, notes  
**Discovery:** "biryani places near Bandra", "that Lebanese place I saved", export as Maps list

**DB model:**
```
PlaceDB: id, name, cuisine_type, area, city, google_maps_url,
         instagram_url, tags(JSON), notes, price_range,
         status(want_to_try|been), times_visited, cover_image_url
```

**Why not in Remy:** shared pipeline code, entirely different data and intents. Alfred routes "save this restaurant" to Charlie, "parse this recipe" to Remy.

---

## Phase 7: Nutrition Intelligence 📋 Planned

**Data source:** Open Food Facts (free, no key, 3M+ products, decent Indian coverage) + USDA FoodData Central for raw ingredients.

**What to surface:**
- Per-serving macros on packaged inventory items
- Red flags: sodium >600mg, added sugar >15g, sat fat >5g
- Nutri-Score (A–E) where available
- Side-by-side brand comparison
- Recipe aggregate nutrition per serving

**Integration:** async background lookup on `update_inventory` for packaged goods. Nullable `nutrition_data` JSON column on `InventoryItemDB`. Nutrition card in web UI — hidden when data unavailable, never broken.

**Scope gate:** packaged goods only (named brands). Raw ingredients (onion, rice) are lower priority. Barcode accuracy improves in Phase 8 when scanner is live.

**Effort:** ~1 weekend. High value, low complexity.

---

## Phase 8: Hardware Integration 📋 Planned

- Raspberry Pi 4 + Pi Camera Module V2
- Auto-capture on fridge open (magnetic door sensor)
- Load cells + HX711 for bulk staple weight (rice, dal)
- Barcode scanner → exact Open Food Facts match (Phase 7 accuracy improves)
- Temperature monitoring

See `HARDWARE_CHECKLIST.md` for procurement.

---

## Phase 9: Multi-User & Cloud 💭 Future

- User auth (OAuth / JWT)
- PostgreSQL migration
- Multi-household, family sharing
- Historical consumption analytics
- Meal planning calendar
- Cloud deploy (Railway + Vercel)

---

## What to Build Next (Decision)

```
THIS WEEKEND — Phase 4 recipe library:
  RecipeDB table + 5 endpoints
  Save-from-parser button
  Recipes tab: browse, search, bookmark
  Recipe detail: servings scaler + Cook now
  Telegram /recipes command

AFTER THAT — Phase 7 nutrition (1 weekend, high value):
  Open Food Facts lookup
  Nutrition card component

THEN — Phase 5 social import (step by step):
  1. yt-dlp for YouTube + TikTok
  2. Pinterest (test existing scraper first)
  3. Screenshot/image upload via vision LLM
  4. Instagram caption
  5. Instagram Reel + Whisper

Phase 6 Charlie follows Phase 5.
Phase 8 hardware requires physical procurement.
```

---

## Architecture Rules (Don't Break These)

1. **No custom Instagram scraper** — yt-dlp only, it handles TLS fingerprinting
2. **Charlie ≠ Remy** — shared pipeline, separate agents and data models
3. **Nutrition data is optional everywhere** — missing card is fine, broken UI is not
4. **Phase 4 ships without Phase 5** — recipe library works with URL/paste/dish already
5. **Slim prompt for text/dish, full prompt for URL** — 395 vs 1499 tokens matters on local LLMs
6. **No LLM calls in error paths** — templates only, errors must be fast

---

## Technical Debt

| Item | Fix |
|------|-----|
| Confirmation state in-memory (lost on restart) | Redis |
| Polling for real-time chat updates | WebSocket |
| `parseRecipe` in alfred-client sends NL → re-routed | Already fixed: direct `/recipes/parse` |
| Recipe pipeline: no LLM retry on failure | Retry with backoff |
| SQLite single-writer | PostgreSQL in Phase 9 |
| Catalog: 58 SKUs, no real Swiggy search | Swiggy MCP live catalog |

---

## Milestones

| Milestone | Date | Status |
|-----------|------|--------|
| Phase 1–3 | April 2026 | ✅ |
| Recipe pipeline rewrite | April 26, 2026 | ✅ |
| Recipe-to-cart end-to-end | April 26, 2026 | ✅ |
| Catalog expanded (58 SKUs) | April 26, 2026 | ✅ |
| Phase 4 Recipe Library | TBD | 🔨 |
| Phase 5 Social Import | TBD | 📋 |
| Phase 6 Charlie | TBD | 📋 |
| Phase 7 Nutrition | TBD | 📋 |
| Phase 8 Hardware | TBD | 📋 |

---

**Last Updated:** April 26, 2026
