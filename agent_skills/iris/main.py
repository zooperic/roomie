"""
Iris - The Visual Observer Agent
Handles image recognition and photo scanning
"""

import os
import json
import base64
from typing import Dict, List
from shared.base_agent import BaseAgent, AgentResponse


class Iris(BaseAgent):
    """Vision and image recognition specialist"""
    
    def __init__(self):
        self.name = "iris"
        self.system_prompt = """You are Iris, the visual observer for ROOMIE.

Your role:
- Process photos of fridges and pantries
- Identify food items in images
- Estimate quantities when possible
- Provide confidence scores

Personality: Precise, detail-oriented, observant. You see what others miss.

When analyzing images, you provide structured output with:
- Item names
- Quantities (estimated)
- Confidence scores (0-1)

You help users track inventory through visual inspection."""
        
    
    async def handle(self, intent) -> AgentResponse:
        """Handle image recognition requests"""

        print(f"[IRIS DEBUG] handle called, action={intent.action}")  
        print(f"[IRIS DEBUG] Intent type: {type(intent)}")
        print(f"[IRIS DEBUG] Intent dir: {dir(intent)}")
        if hasattr(intent, 'parameters'):
            print(f"[IRIS DEBUG] Parameters: {intent.parameters}")
        print(f"[IRIS DEBUG] Full intent: {intent}")
    
        # Get the message from intent - try different possible field names
        message = ""
        if hasattr(intent, 'message'):
            message = intent.message
        elif hasattr(intent, 'user_message'):
            message = intent.user_message
        elif hasattr(intent, 'query'):
            message = intent.query
        elif hasattr(intent, 'text'):
            message = intent.text
        else:
            # Fallback - just check the action
            message = ""
    
        if isinstance(message, str):
            message = message.lower()
    
        action = intent.action.lower() if hasattr(intent, 'action') else ""
    
        # Check if this is an image scan request
        if 'scan' in message or 'photo' in message or 'image' in message or action == 'scan' or action == 'analyze' or action == 'scan_image':
            print("[IRIS DEBUG] Calling _scan_image!")
            return await self._scan_image(intent)
    
        # General query
        return AgentResponse(
            agent=self.name,
            result="I'm Iris, your visual observer. Send me a photo of your fridge or pantry and I'll identify the items!",
            action_type="inform",
            confidence=1.0
        )
    
    async def _scan_image(self, intent) -> AgentResponse:
        """
        Scan an image and detect items using REAL vision model
        """
        print("[IRIS DEBUG] _scan_image called!")
        from shared.llm_provider import call_llm_vision
        import json
    
        # Determine intent from message
        message_lower = ""
        if hasattr(intent, 'message'):
            message_lower = intent.message.lower()
        elif hasattr(intent, 'user_message'):
            message_lower = intent.user_message.lower()
    
        scan_intent = 'general'
        if 'add' in message_lower or 'adding' in message_lower:
            scan_intent = 'add'
        elif 'used' in message_lower or 'subtract' in message_lower or 'consumed' in message_lower:
            scan_intent = 'used'
    
        # Get image from intent parameters
        image_base64 = None
        if hasattr(intent, 'parameters') and isinstance(intent.parameters, dict):
            image_base64 = intent.parameters.get('image_data')
            print(f"[IRIS DEBUG] Got image_base64: {image_base64[:50] if image_base64 else 'None'}...")
    
        if not image_base64:
            # No image provided - return mock data for testing
            mock_items = self._get_mock_detected_items(scan_intent)
            result = {
                "items": mock_items,
                "intent": scan_intent,
                "message": f"Detected {len(mock_items)} items (MOCK MODE - no image provided)"
            }
            return AgentResponse(
                agent=self.name,
                result=json.dumps(result),
                action_type="analyze",
                confidence=0.85
            )
    
        # REAL VISION: Call the vision model
        prompt = """Analyze this fridge/pantry photo and list all food items you can see.
    
        Return ONLY a JSON array with this exact format:
        [
            {"name": "item name", "quantity": estimated_quantity, "unit": "units/g/ml/L", "confidence": 0.0-1.0}
        ]

        Be specific with item names. Estimate quantities conservatively. Only include items you're confident about."""
    
        try:
            vision_response = await call_llm_vision(
                prompt=prompt,
                image_base64=image_base64,
                system="You are a precise visual food item detector. Return only valid JSON."
            )
        
            # Parse the vision response
            items = json.loads(vision_response)
        
            result = {
                "items": items,
                "intent": scan_intent,
                "message": f"Detected {len(items)} items using vision AI"
            }
        
            return AgentResponse(
                agent=self.name,
                result=json.dumps(result),
                action_type="analyze",
                confidence=0.85,
                needs_human_approval=scan_intent != 'general'
            )
        
        except Exception as e:
            # Fallback to mock on error
            print(f"[IRIS] Vision error: {e}, using mock data")
            mock_items = self._get_mock_detected_items(scan_intent)
            result = {
                "items": mock_items,
                "intent": scan_intent,
                "message": f"Vision error - using mock data: {str(e)}"
            }
            return AgentResponse(
                agent=self.name,
                result=json.dumps(result),
                action_type="analyze",
                confidence=0.50
            )
        """
        Scan an image and detect items
        
        For now, this is a MOCK implementation that returns plausible results
        In Phase 4, this will integrate with actual vision APIs
        """
        
        # Determine intent from message
        message_lower = intent.message.lower()
        scan_intent = 'general'
        
        if 'add' in message_lower or 'adding' in message_lower:
            scan_intent = 'add'
        elif 'used' in message_lower or 'subtract' in message_lower or 'consumed' in message_lower:
            scan_intent = 'used'
        
        # MOCK: Return plausible detected items
        # In real implementation, this would call vision API
        mock_items = self._get_mock_detected_items(scan_intent)
        
        result = {
            "items": mock_items,
            "intent": scan_intent,
            "message": f"Detected {len(mock_items)} items with confidence scores"
        }
        
        return AgentResponse(
            agent=self.name,
            result=json.dumps(result),
            action_type="scan",
            confidence=0.85,
            needs_human_approval=scan_intent != 'general'  # Confirm inventory changes
        )
    
    def _get_mock_detected_items(self, intent: str) -> List[Dict]:
        """
        Return mock detected items for testing
        
        In Phase 4, this will be replaced with actual vision API calls
        """
        
        if intent == 'add':
            # Simulating items just purchased
            return [
                {"name": "Milk", "quantity": 1, "unit": "L", "confidence": 0.95},
                {"name": "Eggs", "quantity": 6, "unit": "units", "confidence": 0.92},
                {"name": "Paneer", "quantity": 200, "unit": "g", "confidence": 0.88},
                {"name": "Tomatoes", "quantity": 500, "unit": "g", "confidence": 0.85},
            ]
        elif intent == 'used':
            # Simulating items consumed
            return [
                {"name": "Eggs", "quantity": 2, "unit": "units", "confidence": 0.90},
                {"name": "Bread", "quantity": 2, "unit": "slices", "confidence": 0.87},
                {"name": "Butter", "quantity": 20, "unit": "g", "confidence": 0.83},
            ]
        else:
            # General scan
            return [
                {"name": "Milk", "quantity": 0.5, "unit": "L", "confidence": 0.93},
                {"name": "Eggs", "quantity": 8, "unit": "units", "confidence": 0.91},
                {"name": "Yogurt", "quantity": 400, "unit": "g", "confidence": 0.89},
                {"name": "Cheese", "quantity": 150, "unit": "g", "confidence": 0.86},
                {"name": "Vegetables", "quantity": 1, "unit": "kg", "confidence": 0.75},
            ]
    
    def get_skills(self) -> list:
        """Return agent skills"""
        from shared.models import SkillDefinition
        return [
            SkillDefinition(
                name="scan_image",
                description="Analyze photos of fridge/pantry and identify items",
                triggers=["scan", "photo", "image", "picture"],
                example_triggers=["scan my fridge", "analyze this photo", "what's in this image"],
                action_type="analyze"
            )
        ]
    
    async def get_status(self) -> Dict:
        """Return agent status"""
        return {
            "healthy": True,
            "summary": "Vision system ready (mock mode)"
        }


# Create singleton instance
iris_agent = Iris()
