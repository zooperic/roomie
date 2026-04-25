import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional

from shared.db import init_db, SessionLocal, AgentEventDB
from shared.models import AgentResponse, ActionType
from agent_skills.alfred.router import route_intent, dispatch, register_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from agent_skills.elsa.main import ElsaAgent
    register_agent(ElsaAgent())
    print("[Alfred] Online. All agents registered.")
    yield
    print("[Alfred] Shutting down.")


app = FastAPI(title="Alfred — Project Roomy", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class MessageRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: Optional[str] = None


class ConfirmActionRequest(BaseModel):
    session_id: str
    confirmed: bool


pending_confirmations: dict[str, AgentResponse] = {}


@app.get("/")
async def dashboard():
    path = os.path.join(os.path.dirname(__file__), "../../dashboard.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "Place dashboard.html at project root."}


@app.post("/message")
async def receive_message(req: MessageRequest):
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
    del pending_confirmations[req.session_id]
    return {"status": "confirmed", "message": f"Action confirmed: {response.suggested_action}", "result": response.result}


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
