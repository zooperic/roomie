from pydantic import BaseModel, Field
from typing import Any, Optional
from enum import Enum
from datetime import datetime


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionType(str, Enum):
    INFORM = "inform"
    ORDER = "order"
    UPDATE_INVENTORY = "update"
    COMPARE = "compare"
    ANALYZE = "analyze"


class AgentResponse(BaseModel):
    agent: str
    result: Any
    action_type: ActionType = ActionType.INFORM
    requires_confirmation: bool = False
    suggested_action: Optional[str] = None
    suggested_action_payload: Optional[dict] = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.85

    def needs_human(self) -> bool:
        return self.requires_confirmation or not self.is_high_confidence()


class Intent(BaseModel):
    raw_message: str
    target_agent: str
    action: str
    parameters: dict = {}
    user_id: str = "default"
    session_id: Optional[str] = None


class InventoryItem(BaseModel):
    id: Optional[int] = None
    name: str
    quantity: float
    unit: str
    category: str
    agent_owner: str
    low_stock_threshold: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    def is_low_stock(self) -> bool:
        if self.low_stock_threshold is None:
            return False
        return self.quantity <= self.low_stock_threshold


class OrderItem(BaseModel):
    name: str
    quantity: float
    unit: str
    estimated_price: Optional[float] = None
    platform: Optional[str] = None
    platform_item_id: Optional[str] = None


class Order(BaseModel):
    id: Optional[int] = None
    items: list[OrderItem]
    platform: str
    total_estimated: Optional[float] = None
    status: str = "pending"
    placed_by: str = "alfred"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None


class SkillDefinition(BaseModel):
    name: str
    description: str
    example_triggers: list[str]
    action_type: ActionType
    requires_confirmation: bool = False
