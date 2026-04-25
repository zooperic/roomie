import json
from datetime import datetime
from typing import Optional

from shared.base_agent import BaseAgent
from shared.models import (
    AgentResponse, Intent, OrderItem,
    ActionType, SkillDefinition,
)
from shared.llm_provider import get_llm_response, parse_json_response
from shared.db import SessionLocal, InventoryItemDB, AgentEventDB

AGENT_NAME = "elsa"


class ElsaAgent(BaseAgent):
    name = AGENT_NAME
    description = (
        "Manages fridge inventory. Tracks what's in stock, identifies low-stock items, "
        "parses recipes into ingredient lists, checks availability, and suggests orders."
    )
    version = "0.1.0"

    def get_skills(self) -> list[SkillDefinition]:
        return [
            SkillDefinition(
                name="check_inventory",
                description="Check what's in the fridge or if a specific item is available.",
                example_triggers=[
                    "what's in my fridge", "do I have milk", "is there butter",
                    "what do I have", "fridge inventory", "check fridge"
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="update_inventory",
                description="Add, update, or remove an item from fridge inventory.",
                example_triggers=[
                    "I bought milk", "add eggs to fridge", "I used up the curd",
                    "remove tomatoes", "I finished the juice"
                ],
                action_type=ActionType.UPDATE_INVENTORY,
                requires_confirmation=False,
            ),
            SkillDefinition(
                name="low_stock_check",
                description="Identify items running low in the fridge.",
                example_triggers=[
                    "what's running low", "what do I need to restock",
                    "what should I order", "what's almost finished"
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="parse_recipe",
                description="Extract ingredients from a recipe URL or text, check fridge availability.",
                example_triggers=[
                    "I want to make this recipe", "here's a recipe link",
                    "can I make this", "instagram recipe", "check ingredients for"
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="suggest_order",
                description="Suggest an InstaMart order for missing or low-stock items.",
                example_triggers=[
                    "order milk", "restock", "place an order",
                    "buy from instamart", "order what's missing"
                ],
                action_type=ActionType.ORDER,
                requires_confirmation=True,
            ),
        ]

    async def handle(self, intent: Intent) -> AgentResponse:
        action = intent.action
        params = intent.parameters

        if action == "check_inventory":
            return await self._check_inventory(params.get("item"))
        elif action == "update_inventory":
            return await self._update_inventory(params)
        elif action == "low_stock_check":
            return await self._low_stock_check()
        elif action == "parse_recipe":
            return await self._parse_recipe(params.get("url") or params.get("text", ""))
        elif action == "suggest_order":
            return await self._suggest_order(params.get("items"))
        else:
            return AgentResponse(
                agent=AGENT_NAME,
                result=f"I don't know how to handle action '{action}'.",
                action_type=ActionType.INFORM,
                error="unknown_action",
            )

    async def get_status(self) -> dict:
        db = SessionLocal()
        try:
            items = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == AGENT_NAME
            ).all()
            low = [i for i in items if i.low_stock_threshold and i.quantity <= i.low_stock_threshold]
            return {
                "agent": AGENT_NAME,
                "healthy": True,
                "summary": f"{len(items)} items tracked. {len(low)} low stock.",
                "total_items": len(items),
                "low_stock_count": len(low),
                "low_stock_items": [i.name for i in low],
                "last_updated": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()

    async def _check_inventory(self, item: Optional[str]) -> AgentResponse:
        db = SessionLocal()
        try:
            query = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == AGENT_NAME
            )
            if item:
                query = query.filter(InventoryItemDB.name.ilike(f"%{item}%"))
            items = query.all()

            if not items:
                result = f"'{item}' is not tracked in the fridge." if item else "Fridge inventory is empty."
            else:
                result = {
                    "found": [
                        {"name": i.name, "quantity": i.quantity, "unit": i.unit}
                        for i in items
                    ]
                }
            return AgentResponse(agent=AGENT_NAME, result=result, action_type=ActionType.INFORM, confidence=0.95)
        finally:
            db.close()

    async def _update_inventory(self, params: dict) -> AgentResponse:
        db = SessionLocal()
        try:
            name = params.get("name") or params.get("item")
            quantity = float(params.get("quantity", 0))
            unit = params.get("unit", "units")

            if not name:
                return AgentResponse(
                    agent=AGENT_NAME, result="I need an item name to update inventory.",
                    action_type=ActionType.INFORM, error="missing_item_name",
                )

            existing = db.query(InventoryItemDB).filter(
                InventoryItemDB.name.ilike(f"%{name}%"),
                InventoryItemDB.agent_owner == AGENT_NAME,
            ).first()

            if existing:
                existing.quantity = quantity
                existing.unit = unit
                existing.last_updated = datetime.utcnow()
                msg = f"Updated {name}: {quantity} {unit}"
            else:
                db.add(InventoryItemDB(
                    name=name, quantity=quantity, unit=unit,
                    category=params.get("category", "general"),
                    agent_owner=AGENT_NAME,
                    low_stock_threshold=params.get("low_stock_threshold"),
                ))
                msg = f"Added {name}: {quantity} {unit}"

            db.add(AgentEventDB(
                agent=AGENT_NAME, event_type="inventory_update",
                payload={"item": name, "quantity": quantity, "unit": unit},
            ))
            db.commit()
            return AgentResponse(agent=AGENT_NAME, result=msg, action_type=ActionType.UPDATE_INVENTORY, confidence=1.0)
        finally:
            db.close()

    async def _low_stock_check(self) -> AgentResponse:
        db = SessionLocal()
        try:
            items = db.query(InventoryItemDB).filter(InventoryItemDB.agent_owner == AGENT_NAME).all()
            low = [
                {"name": i.name, "quantity": i.quantity, "unit": i.unit, "threshold": i.low_stock_threshold}
                for i in items if i.low_stock_threshold and i.quantity <= i.low_stock_threshold
            ]
            if not low:
                return AgentResponse(agent=AGENT_NAME, result="Everything in the fridge is well-stocked.", action_type=ActionType.INFORM)
            return AgentResponse(
                agent=AGENT_NAME, result={"low_stock_items": low},
                action_type=ActionType.INFORM,
                suggested_action=f"{len(low)} item(s) running low. Want me to suggest an order?",
                confidence=0.95,
            )
        finally:
            db.close()

    async def _parse_recipe(self, recipe_input: str) -> AgentResponse:
        if not recipe_input:
            return AgentResponse(
                agent=AGENT_NAME, result="Please share the recipe URL or paste the text.",
                action_type=ActionType.INFORM, error="missing_input",
            )

        raw = await get_llm_response(
            prompt=f"Extract ingredients from this recipe: {recipe_input}",
            system="Extract a structured ingredient list. Respond only in JSON: {\"dish_name\": \"...\", \"ingredients\": [{\"name\": \"...\", \"quantity\": 0, \"unit\": \"...\"}]}",
            json_mode=True, max_tokens=512,
        )

        try:
            parsed = parse_json_response(raw)
            ingredients = parsed.get("ingredients", [])
            dish = parsed.get("dish_name", "the dish")
        except Exception:
            return AgentResponse(
                agent=AGENT_NAME, result="Couldn't parse the recipe. Try pasting the ingredient list directly.",
                action_type=ActionType.INFORM, error="parse_failed",
            )

        db = SessionLocal()
        try:
            available, missing = [], []
            for ing in ingredients:
                found = db.query(InventoryItemDB).filter(
                    InventoryItemDB.name.ilike(f"%{ing['name']}%"),
                    InventoryItemDB.agent_owner == AGENT_NAME,
                ).first()
                if found and found.quantity > 0:
                    available.append(ing["name"])
                else:
                    missing.append(ing)

            result = {"dish": dish, "total_ingredients": len(ingredients), "available": available, "missing": missing}
            suggested = f"{len(missing)} ingredients missing for {dish}. Want me to suggest an order?" if missing else None

            return AgentResponse(
                agent=AGENT_NAME, result=result, action_type=ActionType.INFORM,
                suggested_action=suggested,
                suggested_action_payload={"items": missing, "source": "recipe_parse"},
                confidence=0.88,
            )
        finally:
            db.close()

    async def _suggest_order(self, items: Optional[list]) -> AgentResponse:
        db = SessionLocal()
        try:
            if not items:
                low = db.query(InventoryItemDB).filter(
                    InventoryItemDB.agent_owner == AGENT_NAME,
                    InventoryItemDB.low_stock_threshold.isnot(None),
                ).all()
                items = [
                    {"name": i.name, "quantity": i.low_stock_threshold, "unit": i.unit}
                    for i in low if i.quantity <= (i.low_stock_threshold or 0)
                ]

            if not items:
                return AgentResponse(agent=AGENT_NAME, result="Nothing to order — all stocked.", action_type=ActionType.INFORM)

            cart = [
                OrderItem(
                    name=i.get("name", i) if isinstance(i, dict) else i,
                    quantity=i.get("quantity", 1) if isinstance(i, dict) else 1,
                    unit=i.get("unit", "units") if isinstance(i, dict) else "units",
                    platform="instamart",
                )
                for i in items
            ]

            db.add(AgentEventDB(agent=AGENT_NAME, event_type="order_suggested", payload={"items": [c.dict() for c in cart]}))
            db.commit()

            return AgentResponse(
                agent=AGENT_NAME,
                result={"cart": [c.dict() for c in cart]},
                action_type=ActionType.ORDER,
                requires_confirmation=True,
                suggested_action=f"Order {', '.join(c.name for c in cart)} from InstaMart",
                suggested_action_payload={"cart": [c.dict() for c in cart], "platform": "instamart"},
                confidence=0.90,
            )
        finally:
            db.close()
