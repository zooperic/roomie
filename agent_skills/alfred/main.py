import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional

from shared.db import init_db, SessionLocal, AgentEventDB, InventoryItemDB as InventoryDB
from shared.models import AgentResponse, ActionType
from agent_skills.alfred.router import route_intent, dispatch, register_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Register agents
    from agent_skills.alfred.agent import AlfredAgent
    from agent_skills.elsa.main import ElsaAgent
    from agent_skills.remy.main import RemyAgent
    from agent_skills.lebowski.main import LebowskiAgent
    register_agent(AlfredAgent())
    register_agent(ElsaAgent())
    register_agent(RemyAgent())
    register_agent(LebowskiAgent())
    print("[Alfred] Online. All agents registered.")
    yield
    print("[Alfred] Shutting down.")


app = FastAPI(title="Alfred — Project Roomy", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class MessageRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: Optional[str] = None
    force_agent: Optional[str] = None  # Skip routing, go directly to this agent


class ConfirmActionRequest(BaseModel):
    session_id: str
    confirmed: bool


class ScanFridgeRequest(BaseModel):
    image_base64: str
    user_id: str = "default"


pending_confirmations: dict[str, AgentResponse] = {}


@app.get("/")
async def dashboard():
    path = os.path.join(os.path.dirname(__file__), "../../dashboard.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "Place dashboard.html at project root."}


@app.post("/message")
async def receive_message(req: MessageRequest):
    from agent_skills.alfred.router import AGENT_REGISTRY
    
    # If force_agent is specified, use Alfred's router for action classification but force the target
    if req.force_agent:
        # Verify agent exists
        agent = AGENT_REGISTRY.get(req.force_agent)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{req.force_agent}' not found")
        
        # Use Alfred's normal router to classify the action
        intent = await route_intent(req.message, user_id=req.user_id)
        
        # Override the target agent to the forced one
        intent.target_agent = req.force_agent
        
        response = await dispatch(intent)
    else:
        # Normal routing through Alfred
        intent = await route_intent(req.message, user_id=req.user_id)
        response = await dispatch(intent)
    
    if response.needs_human():
        session_id = req.session_id or f"{req.user_id}_{intent.action}"
        pending_confirmations[session_id] = response
        return {
            "status": "awaiting_confirmation",
            "session_id": session_id,
            "message": f"Alfred needs your approval:\n{response.suggested_action}",
            "agent": response.agent,
            "confidence": response.confidence,
        }
    return {"status": "ok", "result": response.result, "agent": response.agent, "action_type": response.action_type}


@app.post("/confirm")
async def confirm_action(req: ConfirmActionRequest):
    response = pending_confirmations.get(req.session_id)
    if not response:
        raise HTTPException(status_code=404, detail="No pending action found.")
    if not req.confirmed:
        del pending_confirmations[req.session_id]
        return {"status": "cancelled", "message": "Action cancelled."}
    
    # If this is a photo scan confirmation, apply inventory updates
    if req.session_id.startswith("scan_"):
        from shared.db import SessionLocal, InventoryItemDB as InventoryDB
        from datetime import datetime
        
        diff = response.result
        db = SessionLocal()
        try:
            # Apply added items
            for item in diff.get("added", []):
                new_item = InventoryDB(
                    name=item["name"],
                    quantity=item["quantity"],
                    unit=item.get("unit", "units"),
                    agent_owner="elsa",
                    created_at=datetime.utcnow()
                )
                db.add(new_item)
            
            # Apply updated items
            for item in diff.get("updated", []):
                existing = db.query(InventoryDB).filter_by(name=item["name"], agent_owner="elsa").first()
                if existing:
                    existing.quantity = item["quantity"]
            
            # Apply removed items
            for item in diff.get("removed", []):
                db.query(InventoryDB).filter_by(name=item["name"], agent_owner="elsa").delete()
            
            db.commit()
        finally:
            db.close()
        
        del pending_confirmations[req.session_id]
        return {"status": "confirmed", "message": "Inventory updated from photo scan"}
    
    del pending_confirmations[req.session_id]
    return {"status": "confirmed", "message": f"Action confirmed: {response.suggested_action}", "result": response.result}


@app.post("/scan_fridge")
async def scan_fridge(req: ScanFridgeRequest):
    """Process fridge photo via vision LLM and return inventory diff"""
    from agent_skills.alfred.router import AGENT_REGISTRY
    from shared.llm_provider import call_llm_vision
    from shared.db import SessionLocal, InventoryItemDB as InventoryDB
    import json
    
    # Call vision LLM to detect items
    vision_prompt = """Analyze this fridge photo and list ALL visible food items with their estimated quantities.

Return a JSON array of items in this exact format:
[
  {"name": "milk", "quantity": 2, "unit": "bottles"},
  {"name": "eggs", "quantity": 6, "unit": "units"},
  {"name": "tomatoes", "quantity": 4, "unit": "units"}
]

Rules:
- Be specific but use common names (not brand names)
- Estimate quantities conservatively
- Use standard units: bottles, units, kg, g, L, ml
- Only include items you can clearly see
- If unsure about quantity, round down"""

    try:
        vision_result = await call_llm_vision(vision_prompt, req.image_base64)
        
        # Strip markdown code blocks if present
        vision_result = vision_result.strip()
        if vision_result.startswith("```json"):
            vision_result = vision_result[7:]  # Remove ```json
        if vision_result.startswith("```"):
            vision_result = vision_result[3:]  # Remove ```
        if vision_result.endswith("```"):
            vision_result = vision_result[:-3]  # Remove trailing ```
        vision_result = vision_result.strip()
        
        # Parse JSON from LLM response
        detected_items = json.loads(vision_result)
    except Exception as e:
        return {"status": "error", "message": f"Vision processing failed: {e}"}
    
    # Get current inventory from Elsa
    db = SessionLocal()
    try:
        current_inventory = db.query(InventoryItemDB).filter_by(agent_owner='elsa').all()
        current_dict = {item.name: {"quantity": item.quantity, "unit": item.unit} for item in current_inventory}
    finally:
        db.close()
    
    # Calculate diff
    diff = calculate_inventory_diff(current_dict, detected_items)
    
    # Create session for confirmation
    session_id = f"scan_{req.user_id}_{hash(req.image_base64[:50])}"
    
    # Store diff in pending confirmations
    from shared.models import AgentResponse, ActionType
    response = AgentResponse(
        agent="elsa",
        action_type=ActionType.UPDATE,
        result=diff,
        suggested_action=f"Update inventory based on photo scan",
        requires_confirmation=True,
        confidence=0.7  # Vision is not 100% accurate
    )
    pending_confirmations[session_id] = response
    
    return {
        "status": "awaiting_confirmation",
        "session_id": session_id,
        "diff": diff,
        "message": "Review detected changes before updating inventory"
    }


def calculate_inventory_diff(current: dict, detected: list) -> dict:
    """Calculate diff between current inventory and detected items"""
    detected_dict = {item["name"]: item for item in detected}
    
    added = []
    removed = []
    updated = []
    
    # Find added and updated items
    for name, item in detected_dict.items():
        if name not in current:
            added.append(item)
        elif current[name]["quantity"] != item["quantity"]:
            updated.append({
                "name": name,
                "old_quantity": current[name]["quantity"],
                "quantity": item["quantity"],
                "unit": item.get("unit", current[name].get("unit", ""))
            })
    
    # Find removed items
    for name in current:
        if name not in detected_dict:
            removed.append({"name": name})
    
    return {"added": added, "removed": removed, "updated": updated}


@app.get("/status")
async def status():
    from agent_skills.alfred.router import AGENT_REGISTRY
    agent_statuses = {}
    for name, agent in AGENT_REGISTRY.items():
        agent_statuses[name] = await agent.get_status()
    return {"alfred": "online", "agents": agent_statuses, "pending_confirmations": len(pending_confirmations)}


@app.get("/events")
async def get_events(limit: int = 50):
    db = SessionLocal()
    try:
        events = db.query(AgentEventDB).order_by(AgentEventDB.created_at.desc()).limit(limit).all()
        return [{"agent": e.agent, "event_type": e.event_type, "payload": e.payload, "created_at": e.created_at.isoformat()} for e in events]
    finally:
        db.close()


@app.get("/agents")
async def list_agents():
    from agent_skills.alfred.router import AGENT_REGISTRY
    return {name: agent.as_registry_entry() for name, agent in AGENT_REGISTRY.items()}
