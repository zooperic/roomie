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

---

## 🧪 Comprehensive Test Scenarios

### Database Reset (Fresh Start)
```bash
cd ~/Desktop/meh/roomie
rm roomie.db
bash scripts/start_dev.sh
```

### Test Suite: Elsa (Fridge Manager)

#### Add Item
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "add milk 1 liter",
    "user_id": "test",
    "force_agent": "elsa"
  }'
```

#### View Inventory
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "show fridge contents",
    "user_id": "test",
    "force_agent": "elsa"
  }'
```

#### Subtract Quantity
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "use milk 500ml",
    "user_id": "test",
    "force_agent": "elsa"
  }'
```

#### Remove Item
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "remove milk",
    "user_id": "test",
    "force_agent": "elsa"
  }'
```

#### Low Stock Check
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "what is low in stock?",
    "user_id": "test",
    "force_agent": "elsa"
  }'
```

---

### Test Suite: Remy (Recipe & Pantry)

#### Add to Pantry
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "add rice 5kg to pantry",
    "user_id": "test",
    "force_agent": "remy"
  }'
```

#### View Pantry
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "show pantry",
    "user_id": "test",
    "force_agent": "remy"
  }'
```

#### Meal Suggestions
```bash
# First add some ingredients
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "add rice 2kg, dal 1kg, onions 500g to pantry",
    "user_id": "test",
    "force_agent": "remy"
  }'

# Ask for suggestions
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can I cook with what I have?",
    "user_id": "test",
    "force_agent": "remy"
  }'
```

---

### Test Suite: Lebowski (Procurement)

#### Hinglish Translation Test
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "match catalog for haldi, dhaniya, jeera, atta, chawal",
    "user_id": "test",
    "force_agent": "lebowski"
  }'
```

**Expected Translations:**
- haldi → turmeric
- dhaniya → coriander  
- jeera → cumin
- atta → wheat flour
- chawal → rice

#### Pack-Size Rounding Test
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need kasuri methi 10g",
    "user_id": "test",
    "force_agent": "lebowski"
  }'
```
**Expected:** Match 25g pack (smallest that fits 10g need)

#### Build Cart
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "build cart for: paneer 500g, yogurt 200g, kasuri methi 2 tbsp, cream 200ml",
    "user_id": "test",
    "force_agent": "lebowski"
  }'
```

**Expected:**
- Products matched and grouped by category
- Subtotal + delivery fee calculated
- Total shown

#### Place Order (Mock)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "place order",
    "user_id": "test",
    "force_agent": "lebowski"
  }'
```

**Expected:**
- Mock order confirmation
- Order ID generated
- ETA shown (~30 min)

---

### End-to-End: Complete Recipe-to-Cart Flow

**Step 1: Reset & Parse Recipe**
```bash
# Clear database
rm roomie.db
bash scripts/start_dev.sh

# Parse recipe with all ingredients
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can I make Paneer Tikka? Ingredients: 500g paneer, 200g yogurt, 2 tbsp kasuri methi, 1 tsp haldi, 2 tsp red chili powder, 2 tbsp cream",
    "user_id": "test",
    "force_agent": "remy"
  }'
```
**Expected:** All items missing (empty fridge/pantry)

**Step 2: Build Cart**
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "build cart for: paneer 500g, yogurt 200g, kasuri methi 2 tbsp, haldi 1 tsp, red chili powder 2 tsp, cream 200ml",
    "user_id": "test",
    "force_agent": "lebowski"
  }'
```

**Expected:**
- All items matched from catalog
- Hinglish translated (haldi → turmeric)
- Pack sizes rounded appropriately
- Total cart value shown

**Step 3: Place Order**
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "place order",
    "user_id": "test",
    "force_agent": "lebowski"
  }'
```

**Expected:** Mock order confirmation

---

### Edge Case Tests

#### Empty Inventory
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "show fridge",
    "user_id": "test",
    "force_agent": "elsa"
  }'
```
**Expected:** "Fridge is empty" or empty list

#### Remove Non-Existent Item
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "remove dragon fruit",
    "user_id": "test",
    "force_agent": "elsa"
  }'
```
**Expected:** Error: "Dragon fruit not in fridge"

#### Subtract More Than Available
```bash
# Add 500ml milk
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"message": "add milk 500ml", "user_id": "test", "force_agent": "elsa"}'

# Try to use 1L
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"message": "use milk 1000ml", "user_id": "test", "force_agent": "elsa"}'
```
**Expected:** Error: "Not enough milk (have 500ml, need 1000ml)"

#### Unknown Ingredient
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "match catalog for unicorn tears",
    "user_id": "test",
    "force_agent": "lebowski"
  }'
```
**Expected:** "Product not found in catalog"

---

### Common Issues & Solutions

#### Issue: Timeout on First Request
**Cause:** Ollama loading model into memory  
**Solution:** Wait 30-60s, timeout now set to 60s in scripts

#### Issue: "No agent named 'X' is registered"
**Cause:** Alfred API didn't start properly  
**Solution:** Check startup logs, restart with auto-kill script

#### Issue: 404 on /message endpoint
**Cause:** Port 8000 not running Alfred  
**Solution:** `lsof -ti:8000 | xargs kill -9`, then restart

#### Issue: Empty LLM responses
**Cause:** Ollama not running or model not pulled  
**Solution:** `ollama pull qwen2.5:7b`, verify Ollama running

#### Issue: Database locked
**Cause:** Multiple processes accessing DB  
**Solution:** Stop all processes, restart cleanly
