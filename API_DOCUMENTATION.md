# 📡 API Documentation - Project Roomy

**Base URL:** `http://localhost:8000` (development)  
**Version:** Phase 2  
**Authentication:** None (planned for Phase 4)

---

## 🔍 Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/message` | POST | Send message to agents |
| `/docs` | GET | Interactive API docs (Swagger) |
| `/redoc` | GET | Alternative API docs |

---

## 📍 Endpoints

### GET /

Health check endpoint.

**Response:**
```json
{
  "status": "online",
  "agents": ["alfred", "elsa", "remy", "lebowski"]
}
```

**Example:**
```bash
curl http://localhost:8000/
```

---

### POST /message

Main endpoint for interacting with all agents.

**Request Body:**
```json
{
  "message": "string (required)",
  "user_id": "string (required)",
  "force_agent": "string (optional)"
}
```

**Parameters:**
- `message` - Natural language query or command
- `user_id` - Unique identifier for the user (used for session management)
- `force_agent` - Force routing to specific agent: `alfred`, `elsa`, `remy`, or `lebowski`

**Response:**
```json
{
  "response": "string",
  "agent": "string",
  "timestamp": "ISO 8601 datetime"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is in my fridge?",
    "user_id": "user123"
  }'
```

**Response:**
```json
{
  "response": "Your fridge contains: milk (1L), eggs (12 units), butter (200g).",
  "agent": "elsa",
  "timestamp": "2026-04-26T10:30:00Z"
}
```

---

## 🤖 Agent Reference

### Alfred (Conversational Assistant & Router)

**Purpose:** Natural conversation and intelligent routing to specialized agents

**Capabilities:**
- Greetings and small talk
- Route queries to appropriate agent
- General Q&A
- System status queries

**Keywords that trigger Alfred:**
- Greetings: hi, hello, hey, good morning, etc.
- General: help, status, how are you, etc.

**Example Queries:**
```bash
# Natural greeting
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "user_id": "user123"}'

# System status
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"message": "How is everything?", "user_id": "user123"}'
```

---

### Elsa (Fridge Inventory Manager)

**Purpose:** Track and manage refrigerator inventory

**Capabilities:**
- Add items to fridge
- Remove items from fridge
- Subtract quantities (when cooking)
- View inventory
- Low stock alerts
- Expiry tracking (planned)

**Keywords that trigger Elsa:**
- fridge, refrigerator
- add, remove, use
- what do I have, what's in stock

**Commands:**

#### Add Item
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "add milk 1 liter",
    "user_id": "user123",
    "force_agent": "elsa"
  }'
```

**Response:** `"Added milk: 1.0 liter"`

#### View Inventory
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "show fridge",
    "user_id": "user123",
    "force_agent": "elsa"
  }'
```

**Response:**
```json
{
  "response": "Your fridge contains:\n- milk: 1.0 liters\n- eggs: 12.0 units\n- butter: 200.0 grams",
  "agent": "elsa"
}
```

#### Subtract Quantity
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "use milk 500ml",
    "user_id": "user123",
    "force_agent": "elsa"
  }'
```

**Response:** `"Removed milk from fridge (used 500.0 ml)"`

#### Remove Item
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "remove milk",
    "user_id": "user123",
    "force_agent": "elsa"
  }'
```

**Response:** `"Removed milk from fridge"`

#### Low Stock Check
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "what is low in stock?",
    "user_id": "user123",
    "force_agent": "elsa"
  }'
```

**Response:** `"Low stock items: eggs (2 units), butter (50g)"`

---

### Remy (Recipe Parser & Pantry Manager)

**Purpose:** Parse recipes, manage pantry inventory, suggest meals

**Capabilities:**
- Parse recipes from URLs
- Parse recipes from copy-pasted text
- Parse recipes from dish names
- Manage pantry inventory
- Cross-check ingredients with fridge + pantry
- Suggest meals based on available ingredients

**Keywords that trigger Remy:**
- recipe, cook, make, ingredients
- pantry, dry goods
- can I make, what can I cook

**Commands:**

#### Parse Recipe - Mode 1 (URL)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Parse recipe from https://example.com/recipe/pasta-carbonara",
    "user_id": "user123",
    "force_agent": "remy"
  }'
```

**Response:**
```json
{
  "response": "Recipe: Pasta Carbonara\n\nIngredients:\n✓ eggs (in fridge)\n✗ pasta 500g (missing)\n✗ bacon 200g (missing)\n✓ parmesan (in pantry)\n\nMissing items: pasta, bacon",
  "agent": "remy"
}
```

#### Parse Recipe - Mode 2 (Copy-Paste Text)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Parse this recipe:\nIngredients:\n- 500g paneer\n- 200g yogurt\n- 2 tbsp kasuri methi\n- 1 tsp turmeric",
    "user_id": "user123",
    "force_agent": "remy"
  }'
```

#### Parse Recipe - Mode 3 (Dish Name)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What ingredients do I need for Butter Chicken?",
    "user_id": "user123",
    "force_agent": "remy"
  }'
```

**Response:** LLM-generated ingredient list + availability check

#### Add to Pantry
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "add rice 5kg to pantry",
    "user_id": "user123",
    "force_agent": "remy"
  }'
```

**Response:** `"Added rice: 5.0 kg to pantry"`

#### View Pantry
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "show pantry",
    "user_id": "user123",
    "force_agent": "remy"
  }'
```

#### Meal Suggestions
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can I cook with what I have?",
    "user_id": "user123",
    "force_agent": "remy"
  }'
```

**Response:** LLM-generated meal suggestions based on fridge + pantry inventory

---

### Lebowski (Procurement & Catalog Matching)

**Purpose:** Match ingredients to products, build shopping carts, place orders

**Capabilities:**
- Match ingredients to catalog products
- Translate Hinglish to English
- Smart pack-size rounding
- Build shopping cart with pricing
- Place orders (mock Swiggy integration)

**Keywords that trigger Lebowski:**
- buy, shop, order, purchase
- match catalog, find products
- cart, checkout

**Commands:**

#### Match Catalog (English)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "match catalog for milk, butter, cheese",
    "user_id": "user123",
    "force_agent": "lebowski"
  }'
```

**Response:**
```json
{
  "response": "Found products:\n\n1. Amul Taaza Toned Milk 1L\n   SKU: MILK001 | ₹60\n\n2. Amul Butter 100g\n   SKU: DAIRY003 | ₹55\n\n3. Amul Cheese Slices 200g\n   SKU: DAIRY004 | ₹120",
  "agent": "lebowski"
}
```

#### Match Catalog (Hinglish)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "match catalog for haldi, dhaniya, jeera",
    "user_id": "user123",
    "force_agent": "lebowski"
  }'
```

**Response:**
- haldi → turmeric → matched product
- dhaniya → coriander → matched product
- jeera → cumin → matched product

**Supported Hinglish Translations (54 total):**
```
haldi → turmeric
dhaniya → coriander
jeera → cumin
atta → wheat flour
chawal → rice
dal → lentils
ghee → clarified butter
paneer → cottage cheese
dahi → yogurt
... (see hinglish_dict.json for full list)
```

#### Pack-Size Rounding
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need kasuri methi 10g",
    "user_id": "user123",
    "force_agent": "lebowski"
  }'
```

**Response:** Matches "MDH Kasuri Methi 25g" (smallest pack that fits 10g need)

**Logic:**
- Need 10g → Match 25g pack (not 100g or 250g)
- Need 150g → Match 200g pack (not 100g)
- Tolerance: 20% over-buying is acceptable

#### Build Cart
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "build cart for: paneer 500g, yogurt 200g, kasuri methi 2 tbsp",
    "user_id": "user123",
    "force_agent": "lebowski"
  }'
```

**Response:**
```
Shopping Cart:

Dairy (2 items):
• Amul Paneer 500g - ₹150 (SKU: DAIRY002)
• Amul Dahi Yogurt 400g - ₹65 (SKU: DAIRY005)

Spices (1 item):
• MDH Kasuri Methi 25g - ₹35 (SKU: SPICE042)

Subtotal: ₹250
Delivery: ₹40
Total: ₹290
```

#### Place Order (Mock)
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "place order",
    "user_id": "user123",
    "force_agent": "lebowski"
  }'
```

**Response:**
```
Order placed successfully!

Order ID: ORDER-12345
Platform: Swiggy Instamart (Mock)
Total: ₹290
Estimated Delivery: 30 minutes

Items: paneer, yogurt, kasuri methi
```

---

## 🔧 Multi-LLM Routing

Alfred automatically selects the best model for each task:

| Task Type | Model | Use Case |
|-----------|-------|----------|
| `chat` | `qwen2.5:7b` | Conversations, routing |
| `vision` | `qwen2.5vl:7b` | Image analysis (future) |
| `code` | `qwen2.5-coder:7b` | Code generation (future) |
| `reasoning` | `deepseek-r1:8b` | Complex logic (future) |
| `fast` | `qwen2.5-coder:1.5b` | Quick responses (future) |

**Check logs:**
```
[LLM] Using model: qwen2.5:7b
```

---

## 🗄️ Database Schema

### inventory_items (Elsa - Fridge)
```sql
CREATE TABLE inventory_items (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    category TEXT,
    expiry_date TIMESTAMP,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### pantry_items (Remy - Pantry)
```sql
CREATE TABLE pantry_items (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    category TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔒 Error Handling

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - Agent not found
- `500` - Server error (LLM failure, database error)

**Error Response Format:**
```json
{
  "error": "Error description",
  "details": "Additional context (optional)"
}
```

**Common Errors:**

### "No agent named 'X' is registered"
**Cause:** Invalid `force_agent` value  
**Solution:** Use one of: alfred, elsa, remy, lebowski

### "Item not found in inventory"
**Cause:** Trying to remove/subtract item that doesn't exist  
**Solution:** Check inventory first

### "Not enough quantity available"
**Cause:** Trying to subtract more than exists  
**Solution:** Check quantity before subtracting

### "Product not found in catalog"
**Cause:** Ingredient doesn't match any catalog item  
**Solution:** Try different keywords or Hinglish translation

---

## 📊 Rate Limits

**Current:** None (development)  
**Planned:** 100 requests/minute per user_id (production)

---

## 🔐 Authentication

**Current:** None  
**Planned (Phase 4):**
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "...", "user_id": "..."}'
```

---

## 🧪 Interactive Documentation

**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

Try requests directly in browser!

---

## 📚 SDK / Client Libraries

### Python Client
```python
import requests

class RoomyClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def send_message(self, message: str, user_id: str, force_agent: str = None):
        response = requests.post(
            f"{self.base_url}/message",
            json={
                "message": message,
                "user_id": user_id,
                "force_agent": force_agent
            }
        )
        return response.json()

# Usage
client = RoomyClient()
result = client.send_message("What's in my fridge?", "user123")
print(result["response"])
```

### JavaScript Client
```javascript
class RoomyClient {
  constructor(baseUrl = "http://localhost:8000") {
    this.baseUrl = baseUrl;
  }
  
  async sendMessage(message, userId, forceAgent = null) {
    const response = await fetch(`${this.baseUrl}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        user_id: userId,
        force_agent: forceAgent
      })
    });
    return await response.json();
  }
}

// Usage
const client = new RoomyClient();
const result = await client.sendMessage("What's in my fridge?", "user123");
console.log(result.response);
```

---

## 🚀 Advanced Usage

### Batch Operations
```bash
# Add multiple items
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "add milk 1L, eggs 12 units, butter 200g",
    "user_id": "user123",
    "force_agent": "elsa"
  }'
```

### Complex Queries
```bash
# Multi-step flow
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Check if I can make Paneer Tikka, and if not, build a cart for the missing items",
    "user_id": "user123"
  }'
```

**Note:** Alfred will route to Remy for recipe check, then to Lebowski for cart building.

---

## 🐛 Debugging

### Enable Verbose Logging
```bash
export LOG_LEVEL=DEBUG
bash scripts/start_dev.sh
```

### Check Agent Status
```bash
curl http://localhost:8000/
```

### View Recent Errors
Check Alfred console output for:
```
[ERROR] ...
[WARNING] ...
```

---

## 📞 Support

**Issues:** GitHub Issues (when repo is public)  
**Documentation:** See README.md, ROADMAP.md  
**Tests:** Run `python3 scripts/test_all.py`

---

**Version:** Phase 2 Complete  
**Last Updated:** 2026-04-26
