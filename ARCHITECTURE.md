# ROOMIE System Architecture

**Version:** Phase 3 Complete  
**Last Updated:** April 26, 2026

---

## System Overview

ROOMIE is a multi-agent AI system built on a microservices-inspired architecture where each agent is an independent service coordinated by Alfred, the orchestrator.

```
┌──────────────────────────────────────────────────────┐
│             Frontend (Next.js)                        │
│  ┌────────┬────────┬────────┬────────┬───────────┐   │
│  │Overview│Inventory│Recipe │Shopping│   Scan    │   │
│  ├────────┼────────┼────────┼────────┼───────────┤   │
│  │  Chat  │Analytics│Roomies │ Events │           │   │
│  └────────┴────────┴────────┴────────┴───────────┘   │
│            React Query State Management               │
└─────────────────────┬────────────────────────────────┘
                      │ HTTP/REST
                      ▼
┌──────────────────────────────────────────────────────┐
│          Alfred API Server (FastAPI)                  │
│  ┌────────────────────────────────────────────────┐  │
│  │  Intent Router                                  │  │
│  │  - Classify user intent                         │  │
│  │  - Route to appropriate agent                   │  │
│  │  - Handle confirmations                         │  │
│  │  - Force-agent mode (for Chat tab)              │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │  REST API Endpoints                             │  │
│  │  /health, /status, /message                     │  │
│  │  /inventory/*, /confirm                         │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────┬────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬────────────┐
        ▼             ▼             ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│     Elsa     │ │   Remy   │ │ Lebowski │ │   Iris   │
│  (Fridge)    │ │ (Pantry) │ │(Shopping)│ │ (Vision) │
└──────┬───────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
       │              │            │             │
       └──────────────┴────────────┴─────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │      Shared Services         │
        ├─────────────────────────────┤
        │  • Database (SQLite)         │
        │  • LLM Provider              │
        │  • Base Agent Class          │
        │  • Swiggy MCP OAuth          │
        └─────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌──────────────────┐      ┌──────────────────┐
│  External APIs    │      │  Database        │
├──────────────────┤      ├──────────────────┤
│ • Claude API      │      │ • inventory      │
│ • OpenAI API      │      │ • events         │
│ • Ollama (local)  │      │ • agent_state    │
│ • Swiggy MCP      │      │                  │
│ • Telegram API    │      │                  │
└──────────────────┘      └──────────────────┘
```

---

## Component Architecture

### 1. Frontend (Next.js 14 + React Query)

**Location:** `roomie-web/`

**Key Components:**
- `app/page.tsx` - Main dashboard with tab routing
- `components/*.tsx` - 12 React components
- `lib/alfred-client.ts` - API client with axios

**State Management:**
- React Query for server state
- Local React state for UI
- No Redux (deliberately simple)

**Tabs:**
1. Overview - System status
2. Inventory - CRUD operations
3. Recipe - Recipe parsing
4. Shopping - Cart building
5. Scan - Photo upload
6. Chat - Agent messaging
7. Analytics - Insights & metrics
8. Roomies - Agent profiles
9. Events - Activity log

---

### 2. Backend (FastAPI + SQLAlchemy)

**Location:** `agent_skills/alfred/`

**Alfred Responsibilities:**
- HTTP server (FastAPI on port 8000)
- Intent routing and classification
- Agent registration and discovery
- Confirmation workflow management
- REST API endpoints

**Key Endpoints:**
```python
GET  /health              # Health check
GET  /status              # Full system status
POST /message             # Send message to agents
POST /confirm             # Confirm pending actions
GET  /inventory/fridge    # List fridge items
POST /inventory/fridge    # Add fridge item
PUT  /inventory/fridge/:id # Update item
DELETE /inventory/fridge/:id # Delete item
# Same for /inventory/pantry
```

**Request Flow:**
```
HTTP Request → FastAPI → Intent Router → Agent Dispatcher
                 ↓
          Confirmation Check → Pending Queue
                 ↓
          Agent Execution → Response
```

---

### 3. Agent Architecture

**Base Class:** `shared/base_agent.py`

All agents inherit from `BaseAgent`:
```python
class BaseAgent:
    def __init__(self, name, system_prompt)
    async def handle(self, intent) -> AgentResponse
    async def get_status() -> dict
```

**Agent Response:**
```python
class AgentResponse:
    agent: str
    result: str  # Main response text
    action_type: str  # classify, update, query, etc.
    confidence: float
    needs_human_approval: bool
    suggested_action: str
```

**Individual Agents:**

**Elsa (Fridge Manager)**
- Location: `agent_skills/elsa/`
- Skills: CRUD ops, low stock detection
- Database: `inventory` table (agent_owner='elsa')

**Remy (Kitchen Master)**
- Location: `agent_skills/remy/`
- Skills: Recipe parsing (3 modes), pantry management
- Database: `inventory` table (agent_owner='remy')

**Lebowski (Procurer)**
- Location: `agent_skills/lebowski/`
- Skills: Catalog matching, Swiggy integration, Hinglish
- External: Swiggy MCP OAuth

**Finn (Strategist)**
- Location: `agent_skills/finn/`
- Skills: Analytics, pattern recognition, insights
- No database (reads from inventory)

**Iris (Observer)**
- Location: `agent_skills/iris/`
- Skills: Image recognition, object detection
- External: Vision APIs

---

### 4. Database (SQLite/SQLAlchemy)

**Location:** `data/roomy.db`

**Schema:**

```sql
-- Inventory Table
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    category TEXT,
    agent_owner TEXT NOT NULL,  -- 'elsa' or 'remy'
    low_stock_threshold REAL,
    last_updated TIMESTAMP
);

-- Events Table
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent TEXT NOT NULL,
    event_type TEXT NOT NULL,
    detail TEXT,
    user_id TEXT
);
```

**Migration Path:**
- Development: SQLite (simple, file-based)
- Production: PostgreSQL (scalable, concurrent)
- Migration script: `scripts/migrate_to_postgres.py` (TODO)

---

### 5. LLM Integration

**Location:** `shared/llm_provider.py`

**Multi-Provider Support:**
```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")

if LLM_PROVIDER == "claude":
    from anthropic import Anthropic
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
elif LLM_PROVIDER == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
elif LLM_PROVIDER == "ollama":
    # Local Ollama instance
    client = ChatOllama(model="qwen2.5:7b")
```

**Usage in Agents:**
```python
llm = get_llm_client()
response = await llm.chat([
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_message}
])
```

---

### 6. Swiggy MCP Integration

**Location:** `shared/swiggy_mcp.py`

**OAuth 2.0 PKCE Flow:**
```
1. Generate code_verifier (random 43-128 chars)
2. Create code_challenge = base64(sha256(verifier))
3. Redirect to Swiggy: /oauth/authorize?...
4. User authenticates
5. Callback to localhost:8765 with code
6. Exchange code for tokens
7. Store tokens in .swiggy_tokens.json
8. Auto-refresh when expired
```

**Token Storage:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_at": 1234567890
}
```

**API Methods:**
- `authenticate()` - Full OAuth flow
- `search_products(query)` - Search catalog
- `add_to_cart(product_id, qty)` - Add item
- `checkout()` - Place order (COD only)
- `get_order_status(order_id)` - Track order

**Mock vs Real:**
```python
if os.getenv("SWIGGY_MCP_ENABLED") == "true":
    # Real API calls
    swiggy = SwiggyMCP()
else:
    # Mock catalog (33 items)
    swiggy = MockCatalog()
```

---

### 7. Telegram Bot

**Location:** `interfaces/telegram/telegram_interface.py`

**Multi-Bot Setup:**
- Each agent has its own bot token
- Alfred bot is primary (orchestrates)
- Direct agent bots for focused tasks

**Message Flow:**
```
User → Telegram → Bot Handler → Alfred API → Agent → Response
```

**Special Handlers:**
- Photo messages → Iris agent
- Text commands → Intent routing
- Callback buttons → Confirmation flow

---

## Design Patterns

### 1. Intent Routing Pattern

Alfred doesn't "know" things - it routes:
```python
async def route_intent(message: str) -> Intent:
    # Classify intent using LLM
    intent = await classifier.classify(message)
    
    # Route to appropriate agent
    agent = AGENT_REGISTRY[intent.target_agent]
    
    return intent
```

### 2. Confirmation Pattern

All real-world actions require human approval:
```python
class AgentResponse:
    needs_human_approval: bool
    suggested_action: str

if response.needs_human_approval:
    pending_confirmations[session_id] = response
    return {"status": "awaiting_confirmation", ...}
```

### 3. Force-Agent Pattern

Chat tab bypasses routing:
```python
if force_agent:
    # Classify action but override target
    intent = await route_intent(message)
    intent.target_agent = force_agent  # User's choice
```

### 4. Photo Intent Pattern

User declares what they're doing:
```python
intent = request.intent  # 'add', 'used', 'general'

items = await iris.detect(photo)

if intent == 'add':
    await inventory.add_items(items)
elif intent == 'used':
    await inventory.subtract_items(items)
# else: just return results
```

---

## Data Flow Examples

### Example 1: Recipe Parsing
```
User: "Can I make Paneer Tikka?"
  ↓
Alfred: Routes to Remy (recipe agent)
  ↓
Remy: Parses "Paneer Tikka" recipe
      Checks Elsa (fridge) + Remy (pantry)
      Returns: "Missing: kasuri methi, cream"
  ↓
Frontend: Displays missing items
          "Shop Now" button available
```

### Example 2: Shopping Flow
```
User: Clicks "Shop Now" on recipe
  ↓
Frontend: Builds cart event → Shopping tab
  ↓
Lebowski: Matches "kasuri methi" to catalog
          Finds "MDH Kasuri Methi 10g - ₹25"
  ↓
User: Confirms order
  ↓
Lebowski: Calls Swiggy MCP
          Places COD order
  ↓
Response: "Order #123 placed! ₹55 total"
```

### Example 3: Photo Scan
```
User: Uploads fridge photo, selects "Adding Items"
  ↓
Frontend: Base64 encode → /message with force_agent=iris
  ↓
Iris: Processes image
      Detects: Milk (1L, 95%), Eggs (12, 88%)
  ↓
Elsa: Adds items to fridge inventory
  ↓
Analytics: Stock health improves 65% → 85%
```

---

## Security Considerations

### API Security
- CORS enabled for localhost:3001
- No auth yet (single-user)
- Rate limiting: TODO
- Input validation via Pydantic

### Token Storage
- Swiggy tokens in `.swiggy_tokens.json`
- Gitignored (not committed)
- Auto-refresh before expiry
- No plaintext passwords

### Future Auth
- Phase 5: OAuth 2.0 for users
- JWT tokens
- Session management
- Multi-tenant isolation

---

## Performance Characteristics

### Response Times (Typical)
- Health check: <10ms
- Inventory CRUD: 50-200ms
- Recipe parsing: 2-5s (LLM dependent)
- Photo scan: 3-8s (Iris processing)
- Shopping cart: 1-3s
- Analytics: 200-500ms

### Scaling Limits (Current)
- Single-user: Excellent
- Multi-user: Not designed for it
- Concurrent requests: ~10-20
- Database: SQLite (not for production scale)

### Bottlenecks
1. LLM API latency (2-5s)
2. SQLite write concurrency
3. Single-threaded Python (GIL)

### Future Optimizations
- Redis for caching
- PostgreSQL for concurrency
- WebSockets for real-time
- Background task queue (Celery)

---

## Testing Architecture

### Unit Tests
- Location: `agent_skills/*/tests/`
- Framework: pytest
- Coverage: ~60% (TODO: improve)

### Integration Tests
- Location: `scripts/test_all.py`
- Tests full workflow
- Mock external APIs

### E2E Tests
- Manual testing via dashboard
- Checklist in `TESTING_GUIDE.md`

---

## Deployment Architecture

### Development (Current)
```
localhost:8000 ← Alfred API
localhost:3001 ← Next.js dev server
localhost:8765 ← OAuth callback
```

### Production (Recommended)
```
Frontend: Vercel (Next.js)
Backend: Railway/Heroku (FastAPI)
Database: PostgreSQL (managed)
Redis: Upstash/Redis Cloud
```

---

## Error Handling

### API Errors
```python
try:
    result = await agent.handle(intent)
except Exception as e:
    logger.error(f"Agent error: {e}")
    return {"status": "error", "message": str(e)}
```

### Frontend Errors
```typescript
onError: (error) => {
  setMessages(prev => [...prev, {
    role: 'agent',
    content: `Error: ${error.message}`,
  }]);
}
```

### Logging
- Alfred: `alfred.log`
- Agents: Individual logs
- Frontend: Browser console
- Level: INFO (dev), ERROR (prod)

---

## Future Architecture Plans

### Phase 4 (Hardware)
```
┌─────────────────┐
│  Raspberry Pi   │
│  ┌───────────┐  │
│  │  Camera   │←─┼── Fridge door sensor
│  │  Module   │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │  Weight   │←─┼── Load cells (x4)
│  │  Sensors  │  │
│  └───────────┘  │
│        ↓        │
│   MQTT Broker   │
└────────┬────────┘
         ↓
    Alfred API
```

### Phase 5 (Cloud)
```
┌──────────────────────────────┐
│      CDN (Cloudflare)         │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│   Frontend (Vercel)           │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│   Load Balancer               │
└──────────────┬───────────────┘
               ↓
    ┌──────────┴──────────┐
    ↓                     ↓
┌─────────┐          ┌─────────┐
│ Alfred  │          │ Alfred  │
│Instance1│          │Instance2│
└────┬────┘          └────┬────┘
     │                    │
     └──────────┬─────────┘
                ↓
┌──────────────────────────────┐
│   PostgreSQL (RDS)            │
│   Redis (ElastiCache)         │
└──────────────────────────────┘
```

---

## Key Architectural Principles

1. **Separation of Concerns** - Each agent owns one domain
2. **Loose Coupling** - Agents communicate via Alfred
3. **Fail Safe** - Confirmations before real-world actions
4. **Extensible** - New agents register automatically
5. **Provider Agnostic** - Swap LLMs via env var
6. **Progressive Enhancement** - Works locally, scales to cloud

---

**Last Updated:** April 26, 2026  
**Status:** Phase 3 Complete - Production Ready
