"""
Alfred Agent - Conversational assistant and router coordinator
Handles general queries, greetings, and clarifications naturally
"""
from datetime import datetime
from typing import Optional

from shared.base_agent import BaseAgent
from shared.models import AgentResponse, Intent, ActionType, SkillDefinition
from shared.llm_provider import get_llm_response

AGENT_NAME = "alfred"


class AlfredAgent(BaseAgent):
    """Alfred - The conversational assistant and coordinator"""
    name = AGENT_NAME
    description = (
        "I'm Alfred, your home assistant. I handle general questions, greetings, "
        "and help you understand what I can do. When you need specific help with "
        "the fridge, recipes, or shopping, I route you to the right specialist."
    )
    version = "0.1.0"

    def get_skills(self) -> list[SkillDefinition]:
        return [
            SkillDefinition(
                name="chat",
                description="Handle greetings, general questions, and casual conversation",
                example_triggers=[
                    "hi", "hello", "how are you", "what can you do",
                    "help", "what's possible", "who are you"
                ],
                action_type=ActionType.INFORM,
            ),
            SkillDefinition(
                name="clarify",
                description="Ask for clarification when intent is unclear",
                example_triggers=[
                    "unclear request", "ambiguous query"
                ],
                action_type=ActionType.INFORM,
            ),
        ]

    async def handle(self, intent: Intent) -> AgentResponse:
        action = intent.action
        params = intent.parameters

        if action == "chat" or action == "greet":
            return await self._chat(intent.raw_message)
        elif action == "clarify":
            return await self._clarify(intent.raw_message)
        else:
            return AgentResponse(
                agent=AGENT_NAME,
                result=f"I'm not sure how to handle that. Could you rephrase?",
                action_type=ActionType.INFORM,
            )

    async def get_status(self) -> dict:
        return {
            "agent": AGENT_NAME,
            "healthy": True,
            "summary": "Alfred is online and coordinating agents",
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def _chat(self, message: str) -> AgentResponse:
        """Handle general conversation naturally with LLM"""
        system_prompt = """You are Alfred, a friendly and helpful home assistant.

You help manage:
- Fridge inventory (tracked by Elsa)
- Recipes and cooking (managed by Remy)  
- Shopping and orders (handled by Lebowski)

Keep responses:
- Natural and conversational
- Brief but warm (2-3 sentences max)
- Helpful without being overly formal

For greetings: Be friendly but don't list capabilities unless asked.
For "what can you do": Briefly mention the three main areas above.
For other chat: Respond naturally and guide toward relevant capabilities if appropriate."""

        response = await get_llm_response(
            prompt=message,
            system=system_prompt,
            task_type="chat",
            max_tokens=256,
        )

        return AgentResponse(
            agent=AGENT_NAME,
            result=response.strip(),
            action_type=ActionType.INFORM,
            confidence=0.95,
        )

    async def _clarify(self, message: str) -> AgentResponse:
        """Ask for clarification when intent is unclear"""
        system_prompt = """You are Alfred, a home assistant. The user's request was unclear.

Politely ask them to clarify what they need help with. 
Mention that you can help with:
- Checking what's in the fridge
- Managing recipes and cooking
- Shopping and ordering

Be friendly and helpful, not robotic. Keep it to 2-3 sentences."""

        response = await get_llm_response(
            prompt=f"User said: {message}",
            system=system_prompt,
            task_type="chat",
            max_tokens=256,
        )

        return AgentResponse(
            agent=AGENT_NAME,
            result=response.strip(),
            action_type=ActionType.INFORM,
            confidence=0.6,
        )
