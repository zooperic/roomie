import json
from shared.models import Intent
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
    
    # Check if real Swiggy MCP should be used
    use_swiggy_mcp = os.getenv("SWIGGY_MCP_ENABLED", "false").lower() == "true"
    print(f"[DEBUG] SWIGGY_MCP_ENABLED env var: {os.getenv('SWIGGY_MCP_ENABLED')}")
    print(f"[DEBUG] use_swiggy_mcp: {use_swiggy_mcp}")
    
    # Register agents
    from agent_skills.alfred.agent import AlfredAgent
    from agent_skills.elsa.main import ElsaAgent
    from agent_skills.remy.main import RemyAgent
    from agent_skills.lebowski.main import LebowskiAgent
    from agent_skills.iris.main import Iris
    from agent_skills.finn.main import Finn
    
    register_agent(AlfredAgent())
    register_agent(ElsaAgent())
    register_agent(RemyAgent())
    register_agent(LebowskiAgent(use_real_mcp=use_swiggy_mcp))
    register_agent(Iris())
    register_agent(Finn())
    
    if use_swiggy_mcp:
        print("[Alfred] Swiggy MCP REAL mode enabled - will use OAuth authentication")
    else:
        print("[Alfred] Swiggy MCP MOCK mode - using local catalog")
    
    print("[Alfred] Online. All agents registered.")
    yield
    print("[Alfred] Shutting down.")


app = FastAPI(title="Alfred — Project Roomy", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class MessageRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: Optional[str] = None
    force_agent: Optional[str] = None
    image_data: Optional[str] = None  # Skip routing, go directly to this agent


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
    
    if req.force_agent:
        if req.force_agent == "alfred":
            intent = await route_intent(req.message, user_id=req.user_id)
        else:
            agent = AGENT_REGISTRY.get(req.force_agent)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent '{req.force_agent}' not found")
            
            intent = await route_intent(req.message, user_id=req.user_id)
            intent.target_agent = req.force_agent
            
            # Pass image_data to parameters
            if req.image_data:
                intent.parameters['image_data'] = req.image_data
        
        response = await dispatch(intent)
        
        # AUTO-ADD: If Iris scanned with 'add' operation, send items to Elsa
        if req.force_agent == "iris" and intent.parameters.get('operation') == 'add':
            try:
                result_data = json.loads(response.result)
                items = result_data.get('items', [])
                
                if items:
                    elsa = AGENT_REGISTRY.get("elsa")
                    
                    # Add each item to fridge
                    added_count = 0
                    for item in items:
                        elsa_intent = Intent(
                            raw_message=f"Add {item['quantity']} {item['unit']} of {item['name']}",
                            target_agent="elsa",
                            action="add",
                            parameters={
                                "item": item['name'],
                                "quantity": item['quantity'],
                                "unit": item['unit'],
                                "source": "vision_scan"
                            },
                            user_id=req.user_id
                        )
                        
                        await elsa.handle(elsa_intent)
                        added_count += 1
                    
                    # Update response message
                    result_data['message'] = f"Detected {len(items)} items and added {added_count} to inventory"
                    response.result = json.dumps(result_data)
                    
            except Exception as e:
                print(f"[Alfred] Error auto-adding items: {e}")
                # If parsing fails, just return Iris result as-is
    else:
        intent = await route_intent(req.message, user_id=req.user_id)
        response = await dispatch(intent)
    
    return {
        "agent": response.agent,
        "result": response.result,
        "message": response.result,
        "action_type": response.action_type,
        "confidence": response.confidence,
        "error": response.error
    }

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
    """Scan fridge photo and auto-add detected items to inventory"""
    from agent_skills.alfred.router import AGENT_REGISTRY
    
    try:
        # Get Iris to analyze the photo
        iris = AGENT_REGISTRY.get("iris")
        if not iris:
            raise HTTPException(status_code=500, detail="Iris agent not available")
        
        intent = Intent(
            raw_message="scan fridge and add items",
            target_agent="iris",
            action="scan_image",
            parameters={"image_data": req.image_base64, "operation": "add"},
            user_id=req.user_id
        )
        
        response = await iris.handle(intent)
        result_data = json.loads(response.result)
        items = result_data.get('items', [])
        
        # Auto-add items to inventory via Elsa
        if items:
            elsa = AGENT_REGISTRY.get("elsa")
            added_count = 0
            
            for item in items:
                elsa_intent = Intent(
                    raw_message=f"Add {item['quantity']} {item['unit']} of {item['name']}",
                    target_agent="elsa",
                    action="add",
                    parameters={
                        "item": item['name'],
                        "quantity": item['quantity'],
                        "unit": item['unit'],
                        "source": "photo_scan"
                    },
                    user_id=req.user_id
                )
                
                await elsa.handle(elsa_intent)
                added_count += 1
            
            result_data['message'] = f"Scanned and added {added_count} items to inventory"
        
        return result_data
        
    except Exception as e:
        print(f"[Alfred] Scan fridge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def status():
    from agent_skills.alfred.router import AGENT_REGISTRY
    agent_statuses = {}
    for name, agent in AGENT_REGISTRY.items():
        agent_statuses[name] = await agent.get_status()
    return {"alfred": "online", "agents": agent_statuses, "pending_confirmations": len(pending_confirmations)}


@app.get("/health")
async def health():
    """Health check endpoint for frontend"""
    return {"status": "healthy", "service": "alfred"}



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


# ===== Inventory Endpoints =====

class InventoryItemRequest(BaseModel):
    name: str
    quantity: float
    unit: str
    category: Optional[str] = None
    low_stock_threshold: Optional[float] = None


@app.get("/inventory/fridge")
async def get_fridge_inventory():
    """Get all fridge items"""
    from agent_skills.alfred.router import AGENT_REGISTRY
    elsa = AGENT_REGISTRY.get("elsa")
    if not elsa:
        raise HTTPException(status_code=503, detail="Elsa agent not available")
    return await elsa.list_all_items()


@app.get("/inventory/pantry")
async def get_pantry_inventory():
    """Get all pantry items"""
    from agent_skills.alfred.router import AGENT_REGISTRY
    remy = AGENT_REGISTRY.get("remy")
    if not remy:
        raise HTTPException(status_code=503, detail="Remy agent not available")
    return await remy.list_all_items()


@app.post("/inventory/fridge")
async def add_fridge_item(request: dict):
    """Add item to fridge inventory via Elsa"""
    from agent_skills.alfred.router import AGENT_REGISTRY
    
    try:
        elsa = AGENT_REGISTRY.get("elsa")
        if not elsa:
            raise HTTPException(status_code=500, detail="Elsa not available")
        
        intent = Intent(
            raw_message=f"Add {request.get('quantity', 1)} {request.get('unit', 'units')} of {request['name']}",
            target_agent="elsa",
            action="update_inventory",
            parameters={
                "item": request['name'],
                "quantity": request.get('quantity', 1),
                "unit": request.get('unit', 'units'),
                "storage_location": "fridge",
                "category": request.get('category', 'general'),
                "operation": "add" 
            },
            user_id="web-user"
        )
        
        response = await elsa.handle(intent)
        return {"status": "success", "message": response.result}
        
    except Exception as e:
        print(f"[Alfred] Add fridge item error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory/pantry")
async def add_pantry_item(request: dict):
    """Add item to pantry inventory via Remy"""
    from agent_skills.alfred.router import AGENT_REGISTRY
    
    try:
        remy = AGENT_REGISTRY.get("remy")
        if not remy:
            raise HTTPException(status_code=500, detail="Remy not available")
        
        intent = Intent(
            raw_message=f"Add {request.get('quantity', 1)} {request.get('unit', 'units')} of {request['name']}",
            target_agent="remy",
            action="update_inventory",
            parameters={
                "item": request['name'],
                "quantity": request.get('quantity', 1),
                "unit": request.get('unit', 'units'),
                "storage_location": "pantry",
                "category": request.get('category', 'general'),
                "operation": "add"
            },
            user_id="web-user"
        )
        
        response = await remy.handle(intent)
        return {"status": "success", "message": response.result}
        
    except Exception as e:
        print(f"[Alfred] Add pantry item error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/build_cart")
async def build_cart(request: dict):
    """Build shopping cart by matching items to catalog via Lebowski"""
    from agent_skills.alfred.router import AGENT_REGISTRY
    
    try:
        items = request.get('items', [])
        print(f"[BUILD_CART DEBUG] Received items: {items}") 
        if not items:
            raise HTTPException(status_code=400, detail="No items provided")
        
        lebowski = AGENT_REGISTRY.get("lebowski")
        if not lebowski:
            raise HTTPException(status_code=500, detail="Lebowski not available")

        print(f"[BUILD_CART DEBUG] Calling Lebowski with items: {items}")
        
        intent = Intent(
            raw_message=f"Build cart with items: {items}",
            target_agent="lebowski",
            action="build_cart",
            parameters={"items": items},
            user_id="web-user"
        )
        
        response = await lebowski.handle(intent)
        print(f"[BUILD_CART DEBUG] Lebowski response: {response.result}") 
        
        # Parse response
        try:
            result = json.loads(response.result) if isinstance(response.result, str) else response.result
        except:
            result = {"matched_items": [], "total_cost": 0, "message": response.result}
        
        return {
            "response": result,
            "result": result
        }
        
    except Exception as e:
        print(f"[Alfred] Build cart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/inventory/fridge/{item_id}")
async def update_fridge_item(item_id: int, item: InventoryItemRequest):
    """Update fridge item"""
    db = SessionLocal()
    try:
        db_item = db.query(InventoryDB).filter(
            InventoryDB.id == item_id,
            InventoryDB.agent_owner == "elsa"
        ).first()
        
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        db_item.name = item.name
        db_item.quantity = item.quantity
        db_item.unit = item.unit
        if item.category:
            db_item.category = item.category
        if item.low_stock_threshold is not None:
            db_item.low_stock_threshold = item.low_stock_threshold
        
        db.commit()
        return {"success": True, "item_id": item_id}
    finally:
        db.close()


@app.put("/inventory/pantry/{item_id}")
async def update_pantry_item(item_id: int, item: InventoryItemRequest):
    """Update pantry item"""
    db = SessionLocal()
    try:
        db_item = db.query(InventoryDB).filter(
            InventoryDB.id == item_id,
            InventoryDB.agent_owner == "remy"
        ).first()
        
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        db_item.name = item.name
        db_item.quantity = item.quantity
        db_item.unit = item.unit
        if item.category:
            db_item.category = item.category
        if item.low_stock_threshold is not None:
            db_item.low_stock_threshold = item.low_stock_threshold
        
        db.commit()
        return {"success": True, "item_id": item_id}
    finally:
        db.close()


@app.delete("/inventory/fridge/{item_id}")
async def delete_fridge_item(item_id: int):
    """Delete fridge item"""
    db = SessionLocal()
    try:
        db_item = db.query(InventoryDB).filter(
            InventoryDB.id == item_id,
            InventoryDB.agent_owner == "elsa"
        ).first()
        
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        db.delete(db_item)
        db.commit()
        return {"success": True, "item_id": item_id}
    finally:
        db.close()


@app.delete("/inventory/pantry/{item_id}")
async def delete_pantry_item(item_id: int):
    """Delete pantry item"""
    db = SessionLocal()
    try:
        db_item = db.query(InventoryDB).filter(
            InventoryDB.id == item_id,
            InventoryDB.agent_owner == "remy"
        ).first()
        
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        db.delete(db_item)
        db.commit()
        return {"success": True, "item_id": item_id}
    finally:
        db.close()
