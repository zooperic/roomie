"""
Finn - The Strategic Analyst Agent
Handles analytics, insights, and pattern recognition
"""

from typing import Dict
from shared.base_agent import BaseAgent, AgentResponse
from shared.db import SessionLocal, InventoryItemDB


class Finn(BaseAgent):
    """Analytics and insights specialist"""
    
    def __init__(self):
        self.name = "finn"
        self.system_prompt = """You are Finn, the strategic analyst for ROOMIE.

Your role:
- Analyze consumption patterns
- Generate insights about stock health
- Predict low stock situations
- Identify trends and anomalies

Personality: Data-driven, analytical, forward-thinking. You see patterns others miss.

You help users understand their kitchen habits and make better decisions."""
        
    
    async def handle(self, intent) -> AgentResponse:
        """Handle analytics requests"""
        
        action = intent.action.lower()
        message = intent.message.lower()
        
        # Analyze stock health
        if 'health' in message or 'analytics' in message or 'insights' in message:
            return await self._analyze_stock_health()
        
        # General query
        return AgentResponse(
            agent=self.name,
            result="I'm Finn, your analytics expert. Ask me about your stock health, consumption patterns, or inventory insights!",
            action_type="info",
            confidence=1.0
        )
    
    async def _analyze_stock_health(self) -> AgentResponse:
        """Analyze overall stock health"""
        
        db = SessionLocal()
        try:
            # Get all inventory items
            items = db.query(InventoryItemDB).all()
            
            if not items:
                return AgentResponse(
                    agent=self.name,
                    result="Your inventory is empty. Start adding items to get insights!",
                    action_type="info",
                    confidence=1.0
                )
            
            # Calculate metrics
            total_items = len(items)
            low_stock = sum(1 for item in items 
                          if item.low_stock_threshold and item.quantity <= item.low_stock_threshold)
            
            stock_health = round(((total_items - low_stock) / total_items) * 100) if total_items > 0 else 100
            
            # Generate insights
            insights = []
            if stock_health >= 80:
                insights.append("✅ Your kitchen is well-stocked!")
            elif stock_health >= 60:
                insights.append("📊 Stock levels are good overall.")
            else:
                insights.append("⚠️ Multiple items running low - time to shop!")
            
            if low_stock > 0:
                low_items = [item.name for item in items 
                           if item.low_stock_threshold and item.quantity <= item.low_stock_threshold]
                insights.append(f"Low stock items: {', '.join(low_items[:3])}" + 
                              (" and more" if len(low_items) > 3 else ""))
            
            result = f"""Stock Health Analysis:

📊 Overall Health: {stock_health}%
📦 Total Items: {total_items}
⚠️  Low Stock: {low_stock}

Insights:
{chr(10).join(f"• {insight}" for insight in insights)}
"""
            
            return AgentResponse(
                agent=self.name,
                result=result,
                action_type="query",
                confidence=1.0
            )
            
        finally:
            db.close()
    
    def get_skills(self) -> list:
        """Return agent skills"""
        from shared.models import SkillDefinition
        return [
            SkillDefinition(
                name="analyze_stock",
                description="Analyze stock health and consumption patterns",
                triggers=["health", "analytics", "insights", "patterns"],
                example_triggers=["what's my stock health", "analyze my inventory", "show me insights"],
                action_type="analyze"
            )
        ]
    
    async def get_status(self) -> Dict:
        """Return agent status"""
        return {
            "healthy": True,
            "summary": "Analytics operational"
        }


# Create singleton instance
finn_agent = Finn()
