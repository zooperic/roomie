"""
Lebowski Agent - Procurement specialist
Handles catalog matching, cart building, and order placement via Swiggy MCP (mock)
"""
import json
import os
import re
import math
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter

from shared.base_agent import BaseAgent
from shared.models import AgentResponse, Intent, ActionType, SkillDefinition
from shared.llm_provider import get_llm_response

AGENT_NAME = "lebowski"


class LebowskiAgent(BaseAgent):
    """Lebowski - The procurement specialist"""
    name = AGENT_NAME
    description = (
        "I handle procurement and shopping. I match ingredients to real products, "
        "build shopping carts, compare prices, and place orders through Swiggy Instamart. "
        "I speak both English and Hinglish fluently."
    )
    version = "0.1.0"
    
    def __init__(self):
        super().__init__()
        # Load Hinglish dictionary
        hinglish_path = os.path.join(os.path.dirname(__file__), "hinglish_dict.json")
        with open(hinglish_path, "r") as f:
            self.hinglish_dict = json.load(f)
        
        # Load mock catalog
        catalog_path = os.path.join(os.path.dirname(__file__), "mock_catalog.json")
        with open(catalog_path, "r") as f:
            self.catalog = json.load(f)
        
        print(f"[Lebowski] Loaded {len(self.catalog)} items from catalog")
        print(f"[Lebowski] Loaded {len(self.hinglish_dict)} Hinglish translations")

    def get_skills(self) -> list[SkillDefinition]:
        return [
            SkillDefinition(
                name="match_catalog",
                description="Match ingredient names to products in Swiggy catalog",
                example_triggers=[
                    "find paneer on swiggy", "search for haldi",
                    "match these items", "get prices for"
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="build_cart",
                description="Build shopping cart from matched items",
                example_triggers=[
                    "add to cart", "build cart", "create order",
                    "what will this cost"
                ],
                action_type=ActionType.ORDER,
                requires_confirmation=True,
            ),
            SkillDefinition(
                name="place_order",
                description="Place order via Swiggy MCP (requires confirmation)",
                example_triggers=[
                    "place order", "confirm order", "buy these items",
                    "checkout"
                ],
                action_type=ActionType.ORDER,
                requires_confirmation=True,
            ),
        ]

    async def handle(self, intent: Intent) -> AgentResponse:
        action = intent.action
        params = intent.parameters

        if action == "match_catalog":
            items = params.get("items", [])
            if isinstance(params.get("text"), str):
                items = [params.get("text")]
            return await self._match_catalog(items)
        
        elif action == "build_cart":
            items = params.get("items", [])
            return await self._build_cart(items)
        
        elif action == "place_order":
            cart = params.get("cart", [])
            return await self._place_order(cart)
        
        else:
            return AgentResponse(
                agent=AGENT_NAME,
                result=f"I don't know how to handle action '{action}'.",
                action_type=ActionType.INFORM,
                error="unknown_action",
            )

    async def get_status(self) -> dict:
        return {
            "agent": AGENT_NAME,
            "healthy": True,
            "summary": f"Procurement ready. {len(self.catalog)} products in catalog.",
            "catalog_size": len(self.catalog),
            "hinglish_translations": len(self.hinglish_dict),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _translate_hinglish(self, text: str) -> str:
        """Translate Hinglish to English using dictionary"""
        text_lower = text.lower()
        
        # Try exact match first
        if text_lower in self.hinglish_dict:
            return self.hinglish_dict[text_lower]
        
        # Try partial matches (multi-word phrases)
        for hinglish, english in self.hinglish_dict.items():
            if hinglish in text_lower:
                text_lower = text_lower.replace(hinglish, english)
        
        return text_lower

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for matching"""
        # Remove special chars, convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Split and filter empty
        return [t for t in text.split() if t and len(t) > 1]

    def _calculate_idf_score(self, query_tokens: List[str], item: Dict) -> float:
        """
        Calculate IDF-weighted match score
        Higher score = better match
        """
        # Get all searchable text from item
        searchable = f"{item['name']} {item['brand']} {' '.join(item['aliases'])}".lower()
        searchable_tokens = self._tokenize(searchable)
        
        if not searchable_tokens:
            return 0.0
        
        # Count token frequencies across catalog for IDF
        doc_freq = Counter()
        for cat_item in self.catalog:
            cat_text = f"{cat_item['name']} {cat_item['brand']} {' '.join(cat_item['aliases'])}".lower()
            cat_tokens = set(self._tokenize(cat_text))
            doc_freq.update(cat_tokens)
        
        total_docs = len(self.catalog)
        score = 0.0
        
        for token in query_tokens:
            if token in searchable_tokens:
                # IDF = log(total_docs / docs_containing_token)
                idf = math.log(total_docs / (doc_freq.get(token, 0) + 1))
                
                # Bonus for token appearing in name vs aliases
                if token in item['name'].lower():
                    score += idf * 2.0  # Double weight for name match
                else:
                    score += idf
        
        # Normalize by query length
        return score / len(query_tokens) if query_tokens else 0.0

    def _extract_quantity_unit(self, query: str) -> tuple[Optional[float], Optional[str]]:
        """Extract quantity and unit from query (e.g., '200g' -> (200, 'g'))"""
        # Match patterns like: 200g, 1kg, 500ml, 2L, 10 grams, etc.
        patterns = [
            r'(\d+\.?\d*)\s*(g|kg|ml|l|units?|pieces?)',
            r'(\d+\.?\d*)\s*(gram|kilogram|liter|litre)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                qty = float(match.group(1))
                unit = match.group(2)
                # Normalize units
                if unit in ['gram', 'grams']:
                    unit = 'g'
                elif unit in ['kilogram', 'kilograms']:
                    unit = 'kg'
                elif unit in ['liter', 'litre', 'liters', 'litres']:
                    unit = 'l'
                elif unit in ['piece', 'pieces', 'unit']:
                    unit = 'units'
                return qty, unit
        
        return None, None

    def _round_pack_size(self, required_qty: float, required_unit: str, item: Dict) -> int:
        """
        Round up pack size to smallest available pack
        Returns quantity of packs needed
        """
        item_weight = item['weight']
        item_unit = item['unit']
        
        # Convert to same unit for comparison
        if required_unit == item_unit:
            packs_needed = math.ceil(required_qty / item_weight)
            return max(1, packs_needed)
        
        # Unit conversion (simplified)
        conversions = {
            ('g', 'kg'): 1000,
            ('kg', 'g'): 0.001,
            ('ml', 'l'): 1000,
            ('l', 'ml'): 0.001,
        }
        
        conv_key = (required_unit, item_unit)
        if conv_key in conversions:
            required_in_item_units = required_qty * conversions[conv_key]
            packs_needed = math.ceil(required_in_item_units / item_weight)
            return max(1, packs_needed)
        
        # Default: 1 pack
        return 1

    async def _match_catalog(self, items: List) -> AgentResponse:
        """
        Match ingredient list to catalog items
        Input: ["kasuri methi 10g", "cream 200ml", "paneer"]
        Output: Matched catalog items with SKU, price, quantity
        """
        if not items:
            return AgentResponse(
                agent=AGENT_NAME,
                result="Please provide items to match against catalog.",
                action_type=ActionType.INFORM,
                error="missing_items",
            )

        matched_items = []

        for item_query in items:
            # Handle dict format (from recipe parsing)
            if isinstance(item_query, dict):
                item_name = item_query.get("name", "")
                item_qty = item_query.get("quantity")
                item_unit = item_query.get("unit", "units")
                query = f"{item_name} {item_qty}{item_unit}" if item_qty else item_name
            else:
                query = str(item_query)
                item_qty, item_unit = self._extract_quantity_unit(query)

            # Translate Hinglish
            translated = self._translate_hinglish(query)
            
            # Tokenize query
            query_tokens = self._tokenize(translated)

            # Score all catalog items
            scores = []
            for cat_item in self.catalog:
                score = self._calculate_idf_score(query_tokens, cat_item)
                if score > 0:
                    scores.append((score, cat_item))

            if not scores:
                # No match found
                matched_items.append({
                    "query": query,
                    "matched": None,
                    "error": "No matching product found",
                })
                continue

            # Get best match
            scores.sort(reverse=True, key=lambda x: x[0])
            best_match = scores[0][1]

            # Calculate pack quantity needed
            if item_qty and item_unit:
                pack_qty = self._round_pack_size(item_qty, item_unit, best_match)
            else:
                pack_qty = 1

            matched_items.append({
                "query": query,
                "matched": best_match['name'],
                "sku": best_match['sku'],
                "price": best_match['price'],
                "quantity": pack_qty,
                "unit_price": best_match['price'],
                "total_price": best_match['price'] * pack_qty,
                "pack_size": f"{best_match['weight']}{best_match['unit']}",
            })

        total_cost = sum(item['total_price'] for item in matched_items if item.get('matched'))
        
        result = {
            "matched_items": matched_items,
            "total_items": len(matched_items),
            "successfully_matched": sum(1 for i in matched_items if i.get('matched')),
            "total_cost": total_cost,
        }

        return AgentResponse(
            agent=AGENT_NAME,
            result=result,
            action_type=ActionType.INFORM,
            suggested_action=f"Found {result['successfully_matched']}/{len(items)} items. Total: ₹{total_cost}. Build cart?",
            suggested_action_payload={"items": matched_items, "action": "build_cart"},
            confidence=0.90,
        )

    async def _build_cart(self, items: List[Dict]) -> AgentResponse:
        """
        Build shopping cart from matched items
        Groups by category, calculates totals
        """
        if not items:
            return AgentResponse(
                agent=AGENT_NAME,
                result="No items provided to build cart.",
                action_type=ActionType.INFORM,
                error="empty_cart",
            )

        # Filter out unmatched items
        valid_items = [i for i in items if i.get('matched')]

        if not valid_items:
            return AgentResponse(
                agent=AGENT_NAME,
                result="No successfully matched items to add to cart.",
                action_type=ActionType.INFORM,
                error="no_valid_items",
            )

        # Group by category (if we have catalog data)
        categories = {}
        for item in valid_items:
            # Find category from catalog
            cat_item = next((c for c in self.catalog if c['sku'] == item['sku']), None)
            category = cat_item['category'] if cat_item else 'other'
            
            if category not in categories:
                categories[category] = []
            categories[category].append(item)

        subtotal = sum(item['total_price'] for item in valid_items)
        delivery_fee = 0 if subtotal >= 99 else 25  # Free delivery over ₹99
        total = subtotal + delivery_fee

        cart_data = {
            "items": valid_items,
            "categories": categories,
            "item_count": len(valid_items),
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "total": total,
            "platform": "Swiggy Instamart (Mock)",
        }

        return AgentResponse(
            agent=AGENT_NAME,
            result=cart_data,
            action_type=ActionType.ORDER,
            requires_confirmation=True,
            suggested_action=f"Cart ready: {len(valid_items)} items, ₹{total} total. Confirm to place order?",
            suggested_action_payload={"cart": cart_data, "action": "place_order"},
            confidence=0.95,
        )

    async def _place_order(self, cart: Dict) -> AgentResponse:
        """
        Place order via mock Swiggy MCP
        In production, this would call actual Swiggy API
        """
        if not cart:
            return AgentResponse(
                agent=AGENT_NAME,
                result="No cart provided to place order.",
                action_type=ActionType.INFORM,
                error="empty_cart",
            )

        # Mock order placement
        # In production: Call Swiggy MCP API here
        # URL: https://mcp.swiggy.com/im
        # Method: create_order with cart items

        order_id = f"SWG-MOCK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        order_result = {
            "order_id": order_id,
            "status": "confirmed",
            "platform": "Swiggy Instamart (Mock)",
            "items": cart.get('items', []),
            "total": cart.get('total', 0),
            "delivery_fee": cart.get('delivery_fee', 0),
            "estimated_delivery": "15-20 minutes",
            "payment_method": "COD",
            "note": "🚧 MOCK ORDER - Not actually placed. Replace with real Swiggy MCP when credentials available.",
        }

        return AgentResponse(
            agent=AGENT_NAME,
            result=order_result,
            action_type=ActionType.ORDER,
            suggested_action=f"✅ Mock order placed: {order_id}. (Replace with real MCP integration)",
            confidence=1.0,
        )
