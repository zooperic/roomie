"""
Remy Agent - Kitchen operations, recipe parsing, and meal planning
Manages pantry inventory and coordinates with Elsa for comprehensive ingredient checks.

Phase 2: Full recipe pipeline (scrape → LLM extract → catalog handoff to Lebowski)
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

from agent_skills.remy.recipe_pipeline import (
    pipeline_from_url,
    pipeline_from_text,
    pipeline_from_dish_name,
    ParsedRecipe,
    Ingredient,
)
from agent_skills.remy.prompts import (
    HUMANIZE_ERROR_PROMPT,
    LEBOWSKI_HANDOFF_PROMPT,
    SERVINGS_ASK_PROMPT,
)

AGENT_NAME = "remy"


class RemyAgent(BaseAgent):
    """Remy - The kitchen master"""
    name = AGENT_NAME
    description = (
        "I manage the pantry and kitchen operations. I can parse recipes from URLs, text, or dish names, "
        "check what ingredients you have, suggest meals based on your inventory, and help you figure out "
        "what you need to buy. I'll check your fridge and pantry first, then ask Lebowski to source "
        "anything missing on Swiggy Instamart."
    )
    version = "0.2.0"

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
                description=(
                    "Extract ingredients from recipe URL, pasted text, or dish name. "
                    "Checks fridge + pantry, then offers to send missing items to Lebowski."
                ),
                example_triggers=[
                    "I want to make Paneer Lababdar", "here's a recipe",
                    "can I cook this", "recipe for pasta carbonara",
                    "https://recipe.com/...", "what do I need to make butter chicken"
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="send_to_lebowski",
                description="Send missing recipe ingredients to Lebowski for Swiggy cart",
                example_triggers=[
                    "yes order it", "go ahead", "send to lebowski", "yes please order",
                    "add to cart", "yes get the missing items"
                ],
                action_type=ActionType.ORDER,
                requires_confirmation=True,
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
            servings = params.get("servings")
            if servings:
                try:
                    servings = int(servings)
                except (ValueError, TypeError):
                    servings = None
            return await self._parse_recipe(recipe_input, target_servings=servings)
        elif action == "send_to_lebowski":
            items = params.get("items", [])
            dish = params.get("dish", "your recipe")
            return await self._send_to_lebowski(items, dish)
        elif action == "suggest_meal":
            return await self._suggest_meal(params.get("preferences", ""))
        else:
            return await self._humanize_unknown_action(action, intent.raw_message)

    # ------------------------------------------------------------------
    # Recipe Parsing
    # ------------------------------------------------------------------

    async def _parse_recipe(
        self,
        recipe_input: str,
        target_servings: Optional[int] = None,
    ) -> AgentResponse:
        if not recipe_input:
            return AgentResponse(
                agent=AGENT_NAME,
                result=(
                    "What are you thinking of making? Share a recipe URL, "
                    "paste the recipe, or just tell me the dish name."
                ),
                action_type=ActionType.INFORM,
                error="missing_input",
            )

        input_type = self._detect_input_type(recipe_input)
        print(f"[Remy] ══ parse_recipe ══════════════════════════════════════")
        print(f"[Remy] input_type={input_type} | servings={target_servings} | len={len(recipe_input)}")
        print(f"[Remy] input preview: {recipe_input[:100].strip()!r}{'...' if len(recipe_input)>100 else ''}")

        try:
            if input_type == "url":
                recipe = await pipeline_from_url(recipe_input, target_servings=target_servings)
            elif input_type == "dish_name":
                recipe = await pipeline_from_dish_name(recipe_input, target_servings=target_servings)
            else:
                recipe = await pipeline_from_text(recipe_input, target_servings=target_servings)
        except ValueError as e:
            return await self._humanize_error(str(e), task="fetching the recipe")
        except Exception as e:
            return await self._humanize_error(str(e), task="parsing the recipe")

        available, missing = await self._compile_missing_items(recipe.ingredients)

        result = {
            "dish": recipe.title,
            "servings": recipe.servings,
            "total_ingredients": len(recipe.ingredients),
            "available": [ing["name"] for ing in available],
            "missing": missing,
            "source_type": recipe.source_type,
        }

        if missing:
            suggested = await self._generate_lebowski_ask(recipe.title, missing)
        else:
            suggested = f"Great news — you've got everything to make {recipe.title}! 🎉"

        return AgentResponse(
            agent=AGENT_NAME,
            result=result,
            action_type=ActionType.INFORM,
            suggested_action=suggested,
            suggested_action_payload={
                "items": missing,
                "dish": recipe.title,
                "action": "send_to_lebowski",
            } if missing else None,
            confidence=0.90,
        )

    async def _send_to_lebowski(
        self,
        items: List[Dict],
        dish: str,
    ) -> AgentResponse:
        if not items:
            return AgentResponse(
                agent=AGENT_NAME,
                result="Nothing to send — you already have everything!",
                action_type=ActionType.INFORM,
            )

        normalized_items = []
        for item in items:
            if isinstance(item, dict):
                normalized_items.append({
                    "name": item.get("name", ""),
                    "quantity": item.get("quantity"),
                    "unit": item.get("unit", "units"),
                })
            else:
                normalized_items.append({"name": str(item)})

        result = {
            "dish": dish,
            "items_sent": normalized_items,
            "handoff_to": "lebowski",
            "next_step": "catalog_match",
        }

        return AgentResponse(
            agent=AGENT_NAME,
            result=result,
            action_type=ActionType.ORDER,
            requires_confirmation=False,
            suggested_action=f"Sending {len(normalized_items)} items to Lebowski to find on Swiggy Instamart...",
            suggested_action_payload={
                "agent": "lebowski",
                "action": "build_cart",
                "items": normalized_items,
            },
            confidence=0.95,
        )

    def _detect_input_type(self, text: str) -> str:
        if re.search(r"https?://[^\s]+", text):
            return "url"
        if len(text) < 60 and not any(
            word in text.lower()
            for word in ["ingredients", "recipe", "cup", "tbsp", "tsp", "gram", "ml", "kg"]
        ):
            return "dish_name"
        return "text"

    async def _compile_missing_items(
        self,
        ingredients: List[Ingredient],
    ) -> tuple[List[Dict], List[Dict]]:
        db = SessionLocal()
        try:
            print(f"[Remy] checking {len(ingredients)} ingredients against fridge+pantry")
            available = []
            missing = []

            for ing in ingredients:
                ing_name = ing.name.lower()

                pantry_item = db.query(InventoryItemDB).filter(
                    InventoryItemDB.name.ilike(f"%{ing_name}%"),
                    InventoryItemDB.agent_owner == AGENT_NAME,
                ).first()

                fridge_item = db.query(InventoryItemDB).filter(
                    InventoryItemDB.name.ilike(f"%{ing_name}%"),
                    InventoryItemDB.agent_owner == "elsa",
                ).first()

                ing_dict = {
                    "name": ing.name,
                    "original_name": ing.original_name,
                    "quantity": ing.quantity,
                    "unit": ing.unit.value if ing.unit else "piece",
                    "notes": ing.notes,
                    "optional": ing.optional,
                }

                if (pantry_item and pantry_item.quantity > 0) or (
                    fridge_item and fridge_item.quantity > 0
                ):
                    available.append(ing_dict)
                else:
                    missing.append(ing_dict)

            print(f"[Remy] inventory check: {len(available)} available, {len(missing)} missing")
            if missing:
                print(f"[Remy] missing: {[m['name'] for m in missing]}")
            return available, missing
        finally:
            db.close()

    async def _generate_lebowski_ask(self, dish: str, missing: List[Dict]) -> str:
        """
        Generate the Lebowski handoff question.
        Uses a template — no LLM call. Saves ~30-60s on Ollama.
        The message is functional; humanization is a luxury we can't afford here.
        """
        missing_names = [m["name"] for m in missing]
        count = len(missing)
        preview = ", ".join(missing_names[:4])
        if count > 4:
            preview += f" +{count - 4} more"
        return (
            f"You're missing {count} ingredient{'s' if count != 1 else ''} for {dish} "
            f"({preview}). Want me to find them on Swiggy Instamart?"
        )

    # ------------------------------------------------------------------
    # Humane error handling
    # ------------------------------------------------------------------

    async def _humanize_error(self, error: str, task: str) -> AgentResponse:
        """
        Convert a technical error into a natural message.
        No LLM call — we're already in a failure path, don't add latency.
        """
        err_lower = error.lower()
        if "timeout" in err_lower or "timed out" in err_lower:
            message = (
                "That took too long to load. Try pasting the recipe text directly "
                "instead of using a URL."
            )
        elif "404" in err_lower or "not found" in err_lower:
            message = "Couldn't find that page — double-check the link."
        elif "ingredients" in err_lower or "couldn't find" in err_lower:
            message = (
                "Found the page but couldn't spot any ingredients. "
                "Try pasting the recipe text directly."
            )
        elif "fetch" in err_lower or "connect" in err_lower or "reach" in err_lower:
            message = "Couldn't reach that site. Is the URL correct?"
        else:
            message = (
                "Something didn't work while "
                + task
                + ". Try pasting the ingredients directly."
            )

        return AgentResponse(
            agent=AGENT_NAME,
            result=message,
            action_type=ActionType.INFORM,
            error="pipeline_error",
            confidence=1.0,
        )

    async def _humanize_unknown_action(self, action: str, raw_message: str) -> AgentResponse:
        return AgentResponse(
            agent=AGENT_NAME,
            result=(
                "Not sure I got that. I can parse recipes, check your pantry, "
                "or suggest what to cook — what would you like?"
            ),
            action_type=ActionType.INFORM,
        )

    # ------------------------------------------------------------------
    # Inventory operations
    # ------------------------------------------------------------------

    async def list_all_items(self) -> list[dict]:
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
        db = SessionLocal()
        try:
            query = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == AGENT_NAME
            )
            if item:
                query = query.filter(InventoryItemDB.name.ilike(f"%{item}%"))
            items = query.all()

            if not items:
                result = f"'{item}' isn't in the pantry." if item else "Pantry is empty."
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
            operation = params.get("operation", "set")

            if not name:
                return AgentResponse(
                    agent=AGENT_NAME,
                    result="What item should I update in the pantry?",
                    action_type=ActionType.INFORM,
                    error="missing_item_name",
                )

            existing = db.query(InventoryItemDB).filter(
                InventoryItemDB.name.ilike(f"%{name}%"),
                InventoryItemDB.agent_owner == AGENT_NAME,
            ).first()

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
                        result=f"Removed {name} from the pantry.",
                        action_type=ActionType.UPDATE_INVENTORY,
                        confidence=1.0
                    )
                else:
                    return AgentResponse(
                        agent=AGENT_NAME,
                        result=f"'{name}' isn't in the pantry to begin with.",
                        action_type=ActionType.INFORM,
                    )

            if existing:
                if operation == "subtract":
                    new_qty = existing.quantity - quantity
                    if new_qty <= 0:
                        db.delete(existing)
                        db.commit()
                        return AgentResponse(
                            agent=AGENT_NAME,
                            result=f"Used up the last of the {name}.",
                            action_type=ActionType.UPDATE_INVENTORY,
                            confidence=1.0
                        )
                    existing.quantity = new_qty
                    msg = f"Used {quantity} {unit} of {name}. {new_qty} {unit} left."
                elif operation == "add":
                    existing.quantity += quantity
                    msg = f"Added {quantity} {unit} of {name}. Now {existing.quantity} {unit} total."
                else:
                    existing.quantity = quantity
                    msg = f"Updated {name}: {quantity} {unit}."
                existing.unit = unit
                existing.last_updated = datetime.utcnow()
            else:
                db.add(InventoryItemDB(
                    name=name, quantity=quantity, unit=unit,
                    category=params.get("category", "pantry"),
                    agent_owner=AGENT_NAME,
                    low_stock_threshold=params.get("low_stock_threshold"),
                ))
                msg = f"Added {name}: {quantity} {unit} to the pantry."

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
                return AgentResponse(
                    agent=AGENT_NAME,
                    result="All pantry staples are well-stocked.",
                    action_type=ActionType.INFORM,
                )
            return AgentResponse(
                agent=AGENT_NAME,
                result={"low_stock_items": low},
                action_type=ActionType.INFORM,
                suggested_action=f"{len(low)} pantry item(s) running low. Want me to add them to a Swiggy order?",
                confidence=0.95,
            )
        finally:
            db.close()

    async def _suggest_meal(self, preferences: str) -> AgentResponse:
        db = SessionLocal()
        try:
            pantry_items = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == AGENT_NAME
            ).all()
            fridge_items = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == "elsa"
            ).all()

            pantry_list = [f"{i.name} ({i.quantity} {i.unit})" for i in pantry_items]
            fridge_list = [f"{i.name} ({i.quantity} {i.unit})" for i in fridge_items]

            system = """You are Remy, a kitchen assistant. Suggest 2-3 meal ideas based on available ingredients.

For each suggestion mention:
1. Recipe name
2. Key ingredients they already have
3. What's missing (max 3 items)
4. Rough difficulty (easy / medium)

Be conversational and specific. Prioritize recipes that need the fewest missing items."""

            prompt = (
                f"Pantry: {', '.join(pantry_list) if pantry_list else 'empty'}\n"
                f"Fridge: {', '.join(fridge_list) if fridge_list else 'empty'}\n"
                f"Preferences: {preferences or 'none'}\n\nWhat can I suggest?"
            )

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
        db = SessionLocal()
        try:
            count = db.query(InventoryItemDB).filter(
                InventoryItemDB.agent_owner == AGENT_NAME
            ).delete()
            db.commit()
            return AgentResponse(
                agent=self.name,
                result=f"Cleared {count} items from the pantry.",
                action_type=ActionType.UPDATE_INVENTORY,
                confidence=1.0
            )
        finally:
            db.close()
