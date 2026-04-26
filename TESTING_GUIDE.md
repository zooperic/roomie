# ROOMIE Testing Guide

**Version:** Phase 3 Complete  
**Last Updated:** April 26, 2026

---

## Overview

This guide covers all testing procedures for ROOMIE system validation.

---

## Pre-Testing Setup

```bash
# 1. Start backend
cd ~/Desktop/meh/roomie
bash scripts/start_dev.sh

# 2. Start frontend (new terminal)
cd roomie-web
npm run dev

# 3. Open browser
# http://localhost:3001

# 4. Clear cache (first time)
# Mac: Cmd+Shift+R
# Windows: Ctrl+Shift+R
```

---

## Test Checklist

### ✅ System Health

- [ ] Alfred API responds at http://localhost:8000/health
- [ ] Frontend loads at http://localhost:3001
- [ ] No errors in browser console
- [ ] All 9 tabs visible in navigation

---

### ✅ Tab 1: Overview

- [ ] Shows 3 cards (Fridge, Pantry, Agents)
- [ ] Counts are accurate
- [ ] Cards are clickable
- [ ] Hover shows colored borders (green/orange/blue)
- [ ] Clicking Fridge/Pantry goes to Inventory tab
- [ ] Clicking Agents goes to Roomies tab

---

### ✅ Tab 2: Inventory

**Fridge Section:**
- [ ] List displays all fridge items
- [ ] Search filter works
- [ ] Category badges visible
- [ ] Low stock items highlighted (amber)
- [ ] Click "ADD ITEM" opens form
- [ ] Add new item → appears in list
- [ ] Edit item → changes persist
- [ ] Delete item → removed from list
- [ ] Real-time polling (updates every 10s)

**Pantry Section:**
- [ ] Same tests as Fridge
- [ ] Items separate from fridge

---

### ✅ Tab 3: Recipe

**Dish Name Mode:**
- [ ] Enter "Paneer Tikka"
- [ ] Click "PARSE RECIPE"
- [ ] Shows ingredient list
- [ ] Available items (green badges)
- [ ] Missing items (amber cards with "SHOP NOW")
- [ ] Click "SHOP NOW" → Goes to Shopping tab

**Recipe URL Mode:**
- [ ] Paste recipe URL
- [ ] Parse works
- [ ] Shows ingredients

**Paste Recipe Mode:**
- [ ] Paste raw recipe text
- [ ] Parse works
- [ ] Shows ingredients

---

### ✅ Tab 4: Shopping

**Manual Mode:**
- [ ] Add item manually
- [ ] Shows in cart
- [ ] Category grouping works
- [ ] Price breakdown visible
- [ ] Total calculated correctly

**From Recipe:**
- [ ] Come from Recipe tab via "SHOP NOW"
- [ ] Missing items auto-populated
- [ ] Can add more items
- [ ] "PLACE ORDER" button enabled

**Mock Mode (default):**
- [ ] SWIGGY_MCP_ENABLED=false in .env
- [ ] Place order
- [ ] Success message shown
- [ ] No real API calls

**Real Mode (optional):**
- [ ] SWIGGY_MCP_ENABLED=true
- [ ] First order opens OAuth
- [ ] Login to Swiggy
- [ ] Tokens saved
- [ ] Order placed successfully
- [ ] ⚠️ REAL MONEY - Be careful!

---

### ✅ Tab 5: Scan

**Upload Methods:**
- [ ] Drag & drop image works
- [ ] Click to browse works
- [ ] Image preview shows
- [ ] Remove photo works

**Intent Selection:**
- [ ] Three options visible
- [ ] Can select "Adding Items" (green)
- [ ] Can select "Used Items" (orange)
- [ ] Can select "General Scan" (blue)

**Scanning:**
- [ ] Upload fridge photo
- [ ] Select intent
- [ ] Click "SCAN NOW"
- [ ] Shows detected items
- [ ] Confidence scores displayed
- [ ] If "Adding" → Inventory updated
- [ ] If "Used" → Inventory decremented
- [ ] If "General" → No changes

**Tips Section:**
- [ ] Tips displayed at bottom
- [ ] Grid layout works

---

### ✅ Tab 6: Chat

**Agent Selection:**
- [ ] 6 agent buttons visible
- [ ] Each has emoji and color
- [ ] Can click to select
- [ ] Selected agent highlighted

**Messaging:**
- [ ] Type message
- [ ] Press Enter sends
- [ ] Shift+Enter adds new line
- [ ] User message appears (right side)
- [ ] Agent response appears (left side)
- [ ] Timestamps shown
- [ ] Auto-scroll to bottom

**Test Messages:**
- Alfred: "What can you do?"
- Elsa: "What's in my fridge?"
- Remy: "Can I make Paneer Tikka?"
- Lebowski: "Find milk on Swiggy"
- Finn: "What's my stock health?"
- Iris: "Help me scan a photo"

**Switch Agents:**
- [ ] Click different agent
- [ ] Chat resets (new conversation)
- [ ] Color theme changes

---

### ✅ Tab 7: Analytics

**Key Metrics:**
- [ ] Stock Health Score shows (0-100%)
- [ ] Total Items correct
- [ ] Low Stock count accurate
- [ ] Categories count shown

**Insights:**
- [ ] At least one insight shows
- [ ] Low stock alert (if applicable)
- [ ] Well stocked message (if health >80%)
- [ ] Category leader shown

**Category Breakdown:**
- [ ] Bar charts visible
- [ ] Percentages shown
- [ ] Colors differentiated
- [ ] Top 5 categories displayed

**Low Stock Details:**
- [ ] Shows if items low
- [ ] Current quantities
- [ ] Thresholds displayed

---

### ✅ Tab 8: Roomies

**Agent Cards:**
- [ ] All 6 agents displayed
- [ ] Emojis and colors correct
- [ ] Quotes showing
- [ ] Skills badges visible
- [ ] Quirks listed
- [ ] Fun facts shown

**Status:**
- [ ] Live status indicators
- [ ] Agent summaries (if available)

**Polling:**
- [ ] Updates every 30s
- [ ] No excessive refreshing

---

### ✅ Tab 9: Events

- [ ] Event log displays
- [ ] Recent events shown
- [ ] Timestamps correct
- [ ] Agent names shown
- [ ] Event types visible

---

## Integration Tests

### End-to-End Workflow 1: Shopping from Recipe

```
1. Go to Recipe tab
2. Enter "Paneer Tikka"
3. Parse recipe
4. Note missing items
5. Click "SHOP NOW"
6. Verify items in cart
7. Place order (mock mode)
8. Verify success message
```

**Expected:** Complete flow without errors

---

### End-to-End Workflow 2: Photo Scan to Analytics

```
1. Go to Scan tab
2. Upload fridge photo
3. Select "Adding Items"
4. Scan
5. Note detected items
6. Go to Inventory tab
7. Verify items added
8. Go to Analytics tab
9. Check stock health improved
```

**Expected:** Inventory updated, analytics reflect changes

---

### End-to-End Workflow 3: Chat to Action

```
1. Go to Chat tab
2. Select Elsa
3. Type: "I used 2 eggs"
4. Press Enter
5. Wait for response
6. Go to Inventory
7. Check eggs quantity decreased
```

**Expected:** Conversational inventory update

---

## API Tests

### Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"alfred"}
```

### Get Inventory
```bash
curl http://localhost:8000/inventory/fridge
# Expected: JSON array of items
```

### Send Message
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"message":"What is in my fridge?","user_id":"test"}'
# Expected: {"status":"ok","result":"...","agent":"elsa"}
```

---

## Performance Tests

### Response Times
- Health check: <100ms
- Inventory list: <500ms
- Recipe parse: 2-5s (LLM)
- Photo scan: 3-8s
- Chat message: 1-3s

### Load Test (Optional)
```bash
# Install Apache Bench
# Run 100 requests
ab -n 100 -c 10 http://localhost:8000/health
```

---

## Regression Tests

After any code changes, run through:
1. ✅ System Health checklist
2. ✅ All 9 tabs basic functionality
3. ✅ At least one E2E workflow
4. ✅ API health check

---

## Bug Reporting

If you find issues:

1. **Note the steps to reproduce**
2. **Check browser console for errors**
3. **Check alfred.log for backend errors**
4. **Note your environment:**
   - OS
   - Python version
   - Node version
   - Browser

---

## Known Issues

### None!
All Phase 3 bugs resolved as of April 26, 2026.

---

## Test Automation (Future)

**Phase 4 TODO:**
- Playwright for E2E tests
- Pytest coverage >80%
- CI/CD pipeline
- Automated regression suite

---

**Last Updated:** April 26, 2026  
**Status:** Manual testing complete, automation planned
