# ROOMIE API Documentation

**Base URL:** `http://localhost:8000`  
**Version:** Phase 3 Complete  
**Last Updated:** April 26, 2026

---

## Authentication

Currently no authentication required (single-user system).  
**Phase 5:** Will add OAuth 2.0 / JWT tokens.

---

## Endpoints

### Health & Status

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "alfred"
}
```

#### `GET /status`
Full system status with all agents.

**Response:**
```json
{
  "alfred": "online",
  "agents": {
    "elsa": {"healthy": true, "summary": "Managing 12 fridge items"},
    "remy": {"healthy": true, "summary": "8 pantry items tracked"},
    "lebowski": {"healthy": true, "summary": "Ready to shop"},
    "finn": {"healthy": true, "summary": "Analytics operational"},
    "iris": {"healthy": true, "summary": "Vision system ready"}
  },
  "pending_confirmations": 0
}
```

---

### Messaging

#### `POST /message`
Send message to Alfred for agent routing.

**Request:**
```json
{
  "message": "What's in my fridge?",
  "user_id": "web-user",
  "force_agent": "elsa"  // Optional: bypass routing
}
```

**Response (Success):**
```json
{
  "status": "ok",
  "result": "You have milk (500ml), eggs (4 units), paneer (200g)...",
  "agent": "elsa",
  "action_type": "query"
}
```

**Response (Needs Confirmation):**
```json
{
  "status": "awaiting_confirmation",
  "session_id": "web-user_place_order",
  "message": "Alfred needs your approval:\nPlace order for ₹125 on Swiggy?",
  "agent": "lebowski",
  "confidence": 0.95
}
```

---

### Inventory - Fridge

#### `GET /inventory/fridge`
List all fridge items.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Milk",
    "quantity": 0.5,
    "unit": "L",
    "category": "dairy",
    "low_stock_threshold": 1.0,
    "last_updated": "2026-04-26T10:30:00"
  }
]
```

#### `POST /inventory/fridge`
Add new fridge item.

**Request:**
```json
{
  "name": "Eggs",
  "quantity": 12,
  "unit": "units",
  "category": "dairy",
  "low_stock_threshold": 6
}
```

**Response:**
```json
{
  "success": true,
  "item_id": 2
}
```

#### `PUT /inventory/fridge/{id}`
Update existing item.

**Request:**
```json
{
  "name": "Eggs",
  "quantity": 8,
  "unit": "units",
  "category": "dairy",
  "low_stock_threshold": 6
}
```

#### `DELETE /inventory/fridge/{id}`
Delete item.

**Response:**
```json
{
  "success": true,
  "item_id": 2
}
```

---

### Inventory - Pantry

Same endpoints as fridge, replace `/fridge` with `/pantry`:
- `GET /inventory/pantry`
- `POST /inventory/pantry`
- `PUT /inventory/pantry/{id}`
- `DELETE /inventory/pantry/{id}`

---

### Confirmations

#### `POST /confirm`
Confirm or cancel pending action.

**Request:**
```json
{
  "session_id": "web-user_place_order",
  "confirmed": true
}
```

**Response (Confirmed):**
```json
{
  "status": "confirmed",
  "result": "Order #12345 placed successfully! Total: ₹125"
}
```

**Response (Cancelled):**
```json
{
  "status": "cancelled",
  "message": "Action cancelled."
}
```

---

### System Info

#### `GET /agents`
List all registered agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "elsa",
      "skills": ["inventory management", "low stock detection"]
    },
    {
      "name": "remy",
      "skills": ["recipe parsing", "meal planning", "pantry management"]
    }
  ]
}
```

#### `GET /events`
Recent system events.

**Response:**
```json
{
  "events": [
    {
      "timestamp": "2026-04-26T15:30:00",
      "agent": "elsa",
      "type": "inventory_update",
      "detail": "Added Milk (1L)"
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 404 Not Found
```json
{
  "detail": "Agent 'unknown' not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently: None  
**Future:** 100 requests/minute per IP

---

## Interactive Docs

Visit `http://localhost:8000/docs` for Swagger UI.

---

**Last Updated:** April 26, 2026
