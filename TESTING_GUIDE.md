# Phase 2 Testing Guide
> Recipe & Procurement System - Complete Implementation

## 🚀 Quick Start

### 1. Start the System
```bash
cd ~/Desktop/meh/roomie
bash scripts/start_dev.sh
```

This starts:
- Alfred API (port 8000)
- Telegram bots (if tokens configured)
- All agents: Alfred, Elsa, Remy, Lebowski

### 2. Verify Health
```bash
python3 scripts/health_check.py
```

Expected output:
```
✓ Alfred API is running
✓ Message routing works
✓ Alfred agent: ONLINE
✓ Elsa agent: ONLINE
✓ Remy agent: ONLINE
✓ Lebowski agent: ONLINE
```

### 3. Run Tests
```bash
python3 scripts/test_all.py
```

This runs comprehensive tests for:
- Alfred natural greetings
- Multi-LLM routing
- Elsa fridge operations
- Remy recipe parsing (all 3 modes)
- Lebowski catalog matching
- End-to-end recipe-to-cart flow

---

## 🧪 Manual Testing Guide

### Test 1: Natural Greetings (Phase 1 Fix)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "hi",
    "user_id": "test_user"
  }'
```

**Expected:** Different greeting each time (not hardcoded)

---

### Test 2: Multi-LLM Routing (Phase 1 Feature)

Watch Alfred console for model selection logs:
```
[LLM] Using model: qwen2.5:7b        # Chat tasks
[VISION] Using model: qwen2.5vl:7b   # Photo tasks
[LLM] Using model: deepseek-r1:8b    # Reasoning tasks
```

---

### Test 3: Remy Recipe Parsing

#### Mode 1: Dish Name
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can I make Paneer Butter Masala?",
    "user_id": "test_user",
    "force_agent": "remy"
  }'
```

**Expected:**
```json
{
  "dish": "Paneer Butter Masala",
  "total_ingredients": 12,
  "available": ["onion", "tomato"],
  "missing": [
    {"name": "paneer", "quantity": 200, "unit": "g"},
    {"name": "kasuri methi", "quantity": 10, "unit": "g"}
  ]
}
```

#### Mode 2: Copy-Paste Text
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Parse this recipe: Pasta Carbonara. Ingredients: 400g spaghetti, 200g bacon, 4 eggs, 100g parmesan",
    "user_id": "test_user",
    "force_agent": "remy"
  }'
```

#### Mode 3: URL (requires web_fetch)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Parse this recipe: https://example.com/recipe/paneer-tikka",
    "user_id": "test_user",
    "force_agent": "remy"
  }'
```

---

### Test 4: Lebowski Catalog Matching

#### English Query
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "find milk on swiggy",
    "user_id": "test_user",
    "force_agent": "lebowski"
  }'
```

**Expected:**
```json
{
  "matched_items": [{
    "query": "milk",
    "matched": "Amul Taaza Toned Milk",
    "sku": "AMUL-MILK-1L",
    "price": 60,
    "quantity": 1
  }]
}
```

#### Hinglish Query
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "find haldi on swiggy",
    "user_id": "test_user",
    "force_agent": "lebowski"
  }'
```

**Expected:** Translates "haldi" → "turmeric" → Matches MDH Turmeric Powder

#### Pack-Size Rounding
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "find kasuri methi 10g",
    "user_id": "test_user",
    "force_agent": "lebowski"
  }'
```

**Expected:** Matches 25g pack (rounds up from 10g)

---

### Test 5: End-to-End Recipe-to-Cart

#### Step 1: Parse Recipe
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to make Pasta Carbonara",
    "user_id": "test_user",
    "force_agent": "remy"
  }'
```

Get the missing items list from response.

#### Step 2: Match to Catalog
```bash
# Use missing items from Step 1
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "find spaghetti, bacon, eggs on swiggy",
    "user_id": "test_user",
    "force_agent": "lebowski"
  }'
```

#### Step 3: Build Cart
(In production, this flows automatically)

---

## 📊 What to Check

### Phase 1 Fixes
- ✅ **No duplicate returns** in llm_provider.py
- ✅ **Natural greetings** - different responses each time
- ✅ **Model selection logs** - correct model for each task
- ✅ **No format_result duplicates** - clean output

### Phase 2 Features

#### Remy Agent
- ✅ All 3 recipe parsing modes work
- ✅ Cross-checks both fridge (Elsa) and pantry (Remy)
- ✅ Returns missing items with quantities
- ✅ Meal suggestions based on inventory

#### Lebowski Agent
- ✅ Hinglish translation works (50+ mappings)
- ✅ Catalog matching with IDF scoring
- ✅ Pack-size rounding (always rounds up)
- ✅ Cart building with price calculation
- ✅ Mock order placement ready

---

## 🐛 Troubleshooting

### Alfred won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Restart
bash scripts/start_dev.sh
```

### Agent not responding
```bash
# Check logs
tail -f alfred.log

# Verify agent is registered
python3 scripts/health_check.py
```

### Model not found (Ollama)
```bash
# List installed models
ollama list

# Pull missing models
ollama pull qwen2.5:7b
ollama pull qwen2.5vl:7b
ollama pull deepseek-r1:8b
ollama pull qwen2.5-coder:7b
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --break-system-packages
```

---

## 🔄 Testing Recipe-to-Cart via Telegram

If you have Telegram bots configured:

1. **Test Remy directly:**
   ```
   @remy_roomie_bot Can I make Paneer Lababdar?
   ```

2. **Test Lebowski directly:**
   ```
   @lebowski_roomie_bot find milk and eggs on swiggy
   ```

3. **Test via Alfred (auto-routing):**
   ```
   @alfred_roomie_bot I want to cook pasta carbonara tonight
   ```
   Alfred will route to Remy → parse recipe → check inventory → return missing items

---

## 📝 Expected Test Results

### All Green (Success)
```
✓ Alfred generates varied, natural greetings
✓ Multi-LLM routing working
✓ Elsa inventory operations work
✓ Remy recipe parsing (all modes)
✓ Remy pantry management works
✓ Lebowski catalog matching works
✓ Hinglish translation works
✓ Pack-size rounding works
✓ End-to-end flow demonstrated
```

### If Tests Fail
1. Check Alfred console for error messages
2. Verify all models are installed (Ollama)
3. Check database is initialized
4. Verify network connectivity (for URL fetching)
5. Check logs in `alfred.log`

---

## 🎯 Next Steps After Testing

1. **Test with real recipes** - Try actual recipe URLs
2. **Build up inventory** - Add items to fridge and pantry
3. **Test meal planning** - Ask Remy for suggestions
4. **Verify Hinglish** - Test with Indian ingredient names
5. **Monitor model selection** - Verify correct models used

---

## 🚧 Known Limitations (Mock Mode)

- **Swiggy orders are MOCK** - No real orders placed
- **Limited catalog** - 33 products (expandable)
- **URL recipe fetching** - Requires web_fetch implementation
- **No price history** - Price tracking not yet implemented

**Switch to Real Swiggy MCP:**
1. Get credentials from Swiggy Builders Club
2. Update `lebowski/main.py` → `_place_order()` function
3. Replace mock API calls with real MCP calls
4. Test with small order first

---

## 📚 Documentation

- **SESSION_SUMMARY_PHASE2.md** - Complete implementation details
- **ROADMAP.md** - Phase 3 plans and future features
- **agent_skills/*/SKILLS.md** - Individual agent specifications

---

## ✅ Testing Checklist

Before marking Phase 2 complete:

- [ ] Health check passes
- [ ] All agents respond
- [ ] Natural greetings work
- [ ] Remy parses recipes (all 3 modes)
- [ ] Lebowski matches catalog
- [ ] Hinglish translation works
- [ ] Pack-size rounding works
- [ ] Mock orders generate order IDs
- [ ] Model selection logs visible
- [ ] No Python errors in console

**When all checked:** Phase 2 is production-ready (with mock MCP)! 🎉
