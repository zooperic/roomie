"""
Remy Agent - Kitchen operations, recipe parsing, and meal planning
Manages pantry inventory and coordinates with Elsa for comprehensive ingredient checks
"""
import json
import re
from datetime import datetime
from typing import Optional, List, Dict

from shared.base_agent import BaseAgent
from shared.models import (
    AgentResponse, Intent, OrderItem,
    ActionType, SkillDefinition,
)
from shared.llm_provider import get_llm_response, parse_json_response
from shared.db import SessionLocal, InventoryItemDB, AgentEventDB

AGENT_NAME = "remy"


class RemyAgent(BaseAgent):
    """Remy - The kitchen master"""
    name = AGENT_NAME
    description = (
        "I manage the pantry and kitchen operations. I can parse recipes from URLs, text, or dish names, "
        "check what ingredients you have, suggest meals based on your inventory, and help you figure out "
        "what you need to buy."
    )
    version = "0.1.0"

    def get_skills(self) -> list[SkillDefinition]:
        return [
            SkillDefinition(
                name="check_inventory",
                description="Check what's in the pantry (dry goods, spices, staples)",
                example_triggers=[
                    "what's in my pantry", "do I have rice", "is there pasta",
                    "pantry inventory", "what dry goods do I have"
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="update_inventory",
                description="Add, update, or remove pantry items",
                example_triggers=[
                    "I bought rice", "add turmeric", "I finished the pasta",
                    "update pantry", "5kg rice bag"
                ],
                action_type=ActionType.UPDATE_INVENTORY,
                requires_confirmation=False,
            ),
            SkillDefinition(
                name="low_stock_check",
                description="Identify pantry staples running low",
                example_triggers=[
                    "what pantry items are low", "what staples do I need",
                    "pantry restock", "what's running out"
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="parse_recipe",
                description="Extract ingredients from recipe URL, pasted text, or dish name",
                example_triggers=[
                    "I want to make Paneer Lababdar", "here's a recipe",
                    "can I cook this", "recipe for pasta carbonara",
                    "https://recipe.com/..."
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="suggest_meal",
                description="Suggest recipes based on current inventory",
                example_triggers=[
                    "what can I cook tonight", "suggest a recipe", "meal ideas",
                    "what should I make", "dinner suggestions"
                ],
                action_type=ActionType.INFORM,
            ),
        ]

    async def handle(self, intent: Intent) -> AgentResponse:
        action = intent.action
        params = intent.parameters
        raw_msg = intent.raw_message.lower()

        if 'clear' in raw_msg or 'remove all' in raw_msg or 'delete all' in raw_msg or 'empty' in raw_msg:
            return await self._clear_all()

        if action == "check_inventory":
            return await self._check_inventory(params.get("item"))
        elif action == "update_inventory":
            return await self._update_inventory(params)
        elif action == "low_stock_check":
            return await self._low_stock_check()
        elif action == "parse_recipe":
            recipe_input = params.get("url") or params.get("text") or params.get("item", "")
            return await self._parse_recipe(recipe_input)
        elif action == "suggest_meal":
            return await self._suggest_meal(params.get("preferences", ""))
        else:
            return AgentResponse(
                agent=AGENT_NAME,
                result=f"I don't know how to handle action '{action}'.",
                action_type=ActionType.INFORM,
                error="unknown_action",
            )

    async def list_all_items(self) -> list[dict]:
        """Return all pantry items as structured data for API"""
        db = SessionLocal()
        try:
            items = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == AGENT_NAME
            ).all()
            
            return [
                {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "category": item.category,
                    "low_stock_threshold": item.low_stock_threshold,
                    "last_updated": item.last_updated.isoformat() if item.last_updated else None,
                }
                for item in items
            ]
        finally:
            db.close()

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
                "summary": f"{len(items)} pantry items tracked. {len(low)} low stock.",
                "total_items": len(items),
                "low_stock_count": len(low),
                "low_stock_items": [i.name for i in low],
                "last_updated": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()

    async def _check_inventory(self, item: Optional[str]) -> AgentResponse:
        """Check pantry inventory"""
        db = SessionLocal()
        try:
            query = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == AGENT_NAME
            )
            if item:
                query = query.filter(InventoryItemDB.name.ilike(f"%{item}%"))
            items = query.all()

            if not items:
                result = f"'{item}' is not in the pantry." if item else "Pantry is empty."
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
        """Update pantry inventory - same logic as Elsa"""
        db = SessionLocal()
        try:
            name = params.get("name") or params.get("item")
            quantity = float(params.get("quantity", 0))
            unit = params.get("unit", "units")
            operation = params.get("operation", "set")  # Default to set for pantry

            if not name:
                return AgentResponse(
                    agent=AGENT_NAME, result="I need an item name to update pantry.",
                    action_type=ActionType.INFORM, error="missing_item_name",
                )

            existing = db.query(InventoryItemDB).filter(
                InventoryItemDB.name.ilike(f"%{name}%"),
                InventoryItemDB.agent_owner == AGENT_NAME,
            ).first()

            # Handle zero or negative quantity - remove item
            if quantity <= 0:
                if existing:
                    db.delete(existing)
                    db.add(AgentEventDB(
                        agent=AGENT_NAME, event_type="inventory_remove",
                        payload={"item": name},
                    ))
                    db.commit()
                    return AgentResponse(
                        agent=AGENT_NAME,
                        result=f"Removed {name} from pantry.",
                        action_type=ActionType.UPDATE_INVENTORY,
                        confidence=1.0
                    )
                else:
                    return AgentResponse(
                        agent=AGENT_NAME,
                        result=f"'{name}' is not in the pantry.",
                        action_type=ActionType.INFORM,
                    )

            # Update or add item
            if existing:
                if operation == "subtract":
                    new_qty = existing.quantity - quantity
                    if new_qty <= 0:
                        db.delete(existing)
                        db.add(AgentEventDB(
                            agent=AGENT_NAME, event_type="inventory_remove",
                            payload={"item": name, "consumed": quantity},
                        ))
                        db.commit()
                        return AgentResponse(
                            agent=AGENT_NAME,
                            result=f"Removed {name} from pantry (used {quantity} {unit}).",
                            action_type=ActionType.UPDATE_INVENTORY,
                            confidence=1.0
                        )
                    existing.quantity = new_qty
                    msg = f"Used {quantity} {unit} of {name}. Remaining: {new_qty} {unit}"
                elif operation == "add":
                    existing.quantity += quantity
                    msg = f"Added {quantity} {unit} of {name}. Total: {existing.quantity} {unit}"
                else:  # set
                    existing.quantity = quantity
                    msg = f"Updated {name}: {quantity} {unit}"

                existing.unit = unit
                existing.last_updated = datetime.utcnow()
            else:
                db.add(InventoryItemDB(
                    name=name, quantity=quantity, unit=unit,
                    category=params.get("category", "pantry"),
                    agent_owner=AGENT_NAME,
                    low_stock_threshold=params.get("low_stock_threshold"),
                ))
                msg = f"Added {name}: {quantity} {unit} to pantry"

            db.add(AgentEventDB(
                agent=AGENT_NAME, event_type="inventory_update",
                payload={"item": name, "quantity": quantity, "unit": unit},
            ))
            db.commit()
            return AgentResponse(agent=AGENT_NAME, result=msg, action_type=ActionType.UPDATE_INVENTORY, confidence=1.0)
        finally:
            db.close()

    async def _low_stock_check(self) -> AgentResponse:
        """Check for low pantry items"""
        db = SessionLocal()
        try:
            items = db.query(InventoryItemDB).filter(InventoryItemDB.agent_owner == AGENT_NAME).all()
            low = [
                {"name": i.name, "quantity": i.quantity, "unit": i.unit, "threshold": i.low_stock_threshold}
                for i in items if i.low_stock_threshold and i.quantity <= i.low_stock_threshold
            ]
            if not low:
                return AgentResponse(agent=AGENT_NAME, result="All pantry staples are well-stocked.", action_type=ActionType.INFORM)
            return AgentResponse(
                agent=AGENT_NAME, result={"low_stock_items": low},
                action_type=ActionType.INFORM,
                suggested_action=f"{len(low)} pantry item(s) running low.",
                confidence=0.95,
            )
        finally:
            db.close()

    async def _parse_recipe(self, recipe_input: str) -> AgentResponse:
        """
        Parse recipe from URL, text, or dish name
        Supports 3 modes: URL fetch, copy-paste, dish name search
        """
        if not recipe_input:
            return AgentResponse(
                agent=AGENT_NAME,
                result="Please share a recipe URL, paste the recipe text, or tell me what dish you want to make.",
                action_type=ActionType.INFORM,
                error="missing_input",
            )

        # Detect input type
        input_type = self._detect_recipe_input_type(recipe_input)

        if input_type == "url":
            return await self._parse_recipe_from_url(recipe_input)
        elif input_type == "dish_name":
            return await self._parse_recipe_from_dish_name(recipe_input)
        else:  # text
            return await self._parse_recipe_from_text(recipe_input)

    def _detect_recipe_input_type(self, text: str) -> str:
        """Detect if input is URL, dish name, or recipe text"""
        # Check for URL pattern
        url_pattern = r'https?://[^\s]+'
        if re.search(url_pattern, text):
            return "url"

        # If it's very short (< 50 chars) and doesn't have typical recipe markers, treat as dish name
        if len(text) < 50 and not any(word in text.lower() for word in ['ingredients', 'recipe', 'cup', 'tbsp', 'tsp', 'gram']):
            return "dish_name"

        # Otherwise assume it's pasted recipe text
        return "text"

    async def _parse_recipe_from_url(self, url: str) -> AgentResponse:
        """Fetch recipe from URL and parse ingredients"""
        try:
            # Use web_fetch tool if available, otherwise LLM reasoning
            from shared.llm_provider import get_llm_response

            system = """You are a recipe parser. Extract ingredients from the recipe content.
            
Respond ONLY in JSON format:
{
    "dish_name": "name of the dish",
    "ingredients": [
        {"name": "ingredient name", "quantity": number, "unit": "g/kg/ml/l/cup/tbsp/tsp/units"},
        ...
    ]
}

Rules:
- Extract all ingredients with quantities
- Normalize units (1 cup = 240ml, 1 tbsp = 15ml, 1 tsp = 5ml)
- If quantity not specified, use 1 unit
- Keep ingredient names simple (e.g., "chicken breast" not "boneless skinless chicken breast")"""

            prompt = f"Parse this recipe URL and extract ingredients: {url}"

            raw = await get_llm_response(
                prompt=prompt,
                system=system,
                json_mode=True,
                max_tokens=2048,
                task_type="chat",  # Use reasoning model for complex extraction
            )

            parsed = parse_json_response(raw)
            ingredients = parsed.get("ingredients", [])
            dish = parsed.get("dish_name", "the dish")

            return await self._compile_missing_items(dish, ingredients)

        except Exception as e:
            return AgentResponse(
                agent=AGENT_NAME,
                result=f"Couldn't fetch recipe from URL. Error: {str(e)}",
                action_type=ActionType.INFORM,
                error="url_fetch_failed",
            )

    async def _parse_recipe_from_text(self, text: str) -> AgentResponse:
        """Parse recipe from pasted text"""
        system = """You are a recipe parser. Extract ingredients from the pasted recipe text.

Respond ONLY in JSON format:
{
    "dish_name": "name of the dish",
    "ingredients": [
        {"name": "ingredient name", "quantity": number, "unit": "g/kg/ml/l/cup/tbsp/tsp/units"},
        ...
    ]
}

Rules:
- Extract all ingredients with quantities
- Normalize units (1 cup = 240ml, 1 tbsp = 15ml, 1 tsp = 5ml)  
- If quantity not specified, use 1 unit
- Keep ingredient names simple"""

        try:
            raw = await get_llm_response(
                prompt=f"Extract ingredients from this recipe:\n\n{text}",
                system=system,
                json_mode=True,
                max_tokens=1024,
                task_type="reasoning",
            )

            parsed = parse_json_response(raw)
            ingredients = parsed.get("ingredients", [])
            dish = parsed.get("dish_name", "the dish")

            return await self._compile_missing_items(dish, ingredients)

        except Exception as e:
            return AgentResponse(
                agent=AGENT_NAME,
                result=f"Couldn't parse recipe text. Error: {str(e)}",
                action_type=ActionType.INFORM,
                error="parse_failed",
            )

    async def _parse_recipe_from_dish_name(self, dish_name: str) -> AgentResponse:
        """Search for recipe by dish name, fetch top result, then parse"""
        system = """You are a recipe finder. Given a dish name, find a recipe and extract ingredients.

Respond ONLY in JSON format:
{
    "dish_name": "name of the dish",
    "ingredients": [
        {"name": "ingredient name", "quantity": number, "unit": "g/kg/ml/l/cup/tbsp/tsp/units"},
        ...
    ]
}

Use your knowledge of common recipes. If it's a common dish, provide typical ingredients and quantities."""

        try:
            raw = await get_llm_response(
                prompt=f"Find a recipe for '{dish_name}' and extract the ingredients with quantities.",
                system=system,
                json_mode=True,
                max_tokens=1024,
                task_type="reasoning",
            )

            parsed = parse_json_response(raw)
            ingredients = parsed.get("ingredients", [])
            dish = parsed.get("dish_name", dish_name)

            return await self._compile_missing_items(dish, ingredients)

        except Exception as e:
            return AgentResponse(
                agent=AGENT_NAME,
                result=f"Couldn't find recipe for '{dish_name}'. Error: {str(e)}",
                action_type=ActionType.INFORM,
                error="dish_search_failed",
            )

    async def _compile_missing_items(self, dish: str, ingredients: List[Dict]) -> AgentResponse:
        """
        Cross-check ingredients against fridge (Elsa) and pantry (Remy)
        Returns what's available and what's missing
        """
        db = SessionLocal()
        try:
            available = []
            missing = []

            for ing in ingredients:
                ing_name = ing["name"].lower()
                
                # Check pantry (Remy's inventory)
                pantry_item = db.query(InventoryItemDB).filter(
                    InventoryItemDB.name.ilike(f"%{ing_name}%"),
                    InventoryItemDB.agent_owner == AGENT_NAME,
                ).first()

                # Check fridge (Elsa's inventory)
                fridge_item = db.query(InventoryItemDB).filter(
                    InventoryItemDB.name.ilike(f"%{ing_name}%"),
                    InventoryItemDB.agent_owner == "elsa",
                ).first()

                if (pantry_item and pantry_item.quantity > 0) or (fridge_item and fridge_item.quantity > 0):
                    available.append(ing_name)
                else:
                    missing.append(ing)

            result = {
                "dish": dish,
                "total_ingredients": len(ingredients),
                "available": available,
                "missing": missing,
            }

            suggested = None
            if missing:
                suggested = f"{len(missing)} ingredient(s) missing for {dish}. Want me to help you order them?"
            else:
                suggested = f"You have everything to make {dish}!"

            return AgentResponse(
                agent=AGENT_NAME,
                result=result,
                action_type=ActionType.INFORM,
                suggested_action=suggested,
                suggested_action_payload={"items": missing, "source": "recipe_parse", "dish": dish} if missing else None,
                confidence=0.88,
            )
        finally:
            db.close()

    async def _suggest_meal(self, preferences: str) -> AgentResponse:
        """Suggest meals based on current fridge + pantry inventory"""
        db = SessionLocal()
        try:
            # Get pantry items
            pantry_items = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == AGENT_NAME
            ).all()

            # Get fridge items  
            fridge_items = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == "elsa"
            ).all()

            inventory_summary = {
                "pantry": [f"{i.name} ({i.quantity} {i.unit})" for i in pantry_items],
                "fridge": [f"{i.name} ({i.quantity} {i.unit})" for i in fridge_items],
            }

            system = """You are a meal planning assistant. Suggest 2-3 recipes based on available ingredients.

For each suggestion, indicate:
1. Recipe name
2. What ingredients they have
3. What's missing (if any)
4. Difficulty level (easy/medium/hard)

Be creative and practical. Prioritize recipes that use most of what they have."""

            prompt = f"""Available ingredients:
Pantry: {', '.join(inventory_summary['pantry']) if inventory_summary['pantry'] else 'empty'}
Fridge: {', '.join(inventory_summary['fridge']) if inventory_summary['fridge'] else 'empty'}

User preferences: {preferences if preferences else 'none specified'}

Suggest 2-3 meal ideas."""

            response = await get_llm_response(
                prompt=prompt,
                system=system,
                task_type="chat",
                max_tokens=512,
            )

            return AgentResponse(
                agent=AGENT_NAME,
                result=response.strip(),
                action_type=ActionType.INFORM,
                confidence=0.85,
            )
        finally:
            db.close()
    
    async def _clear_all(self) -> AgentResponse:
        """Clear all items from pantry"""
        db = SessionLocal()
        try:
            count = db.query(InventoryItemDB).filter(
                InventoryItemDB.storage_location == 'pantry'
            ).delete()
            db.commit()
        
            return AgentResponse(
                agent=self.name,
                result=f"✅ Cleared {count} items from the pantry.",
                action_type="update",
                confidence=1.0
            )
        finally:
            db.close()
