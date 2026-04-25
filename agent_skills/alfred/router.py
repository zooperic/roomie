import json
from shared.llm_provider import get_llm_response, parse_json_response
from shared.models import Intent

AGENT_REGISTRY: dict = {}


def register_agent(agent_instance) -> None:
    AGENT_REGISTRY[agent_instance.name] = agent_instance
    print(f"[Alfred] Registered agent: {agent_instance.name}")


def build_routing_context() -> str:
    lines = ["Available agents and their skills:\n"]
    for name, agent in AGENT_REGISTRY.items():
        lines.append(f"Agent: {name}")
        lines.append(f"  Description: {agent.description}")
        for skill in agent.get_skills():
            lines.append(f"  Skill: {skill.name}")
            lines.append(f"    What it does: {skill.description}")
            lines.append(f"    Triggered by: {', '.join(skill.example_triggers)}")
        lines.append("")
    return "\n".join(lines)


ROUTING_SYSTEM_PROMPT = """
You are Alfred, a home assistant orchestrator. Your only job is to classify 
incoming messages and decide which agent should handle them.

{agent_context}

Given the user's message, respond ONLY with this JSON:
{{
  "target_agent": "<agent name from the list above>",
  "action": "<specific skill name to invoke>",
  "parameters": {{
    "item": "<item name if mentioned, e.g. milk, eggs, butter>",
    "quantity": <numeric quantity if mentioned, e.g. 2, 1.5 — omit if not mentioned>,
    "unit": "<unit if mentioned, e.g. liters, kg, units, packets — omit if not mentioned>",
    "url": "<URL if a link was shared — omit if not mentioned>",
    "text": "<any other relevant text to pass to the agent>"
  }},
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<one sentence why you routed here>"
}}

Parameter extraction rules:
- For "I bought 2 liters of milk" → item: "milk", quantity: 2, unit: "liters"
- For "do I have eggs" → item: "eggs"
- For "what's in the fridge" → no item needed
- For recipe links → url: "<the link>"
- Always extract item name in lowercase
- Omit parameters that are not present in the message — do not guess

If no agent can handle the request, use target_agent: "alfred" and action: "clarify".
Never make up agent names. Only use agents listed above.
"""


async def route_intent(raw_message: str, user_id: str = "default") -> Intent:
    agent_context = build_routing_context()
    system = ROUTING_SYSTEM_PROMPT.format(agent_context=agent_context)

    raw_response = await get_llm_response(
        prompt=raw_message,
        system=system,
        json_mode=True,
        max_tokens=512,
    )

    try:
        parsed = parse_json_response(raw_response)
    except json.JSONDecodeError:
        return Intent(
            raw_message=raw_message,
            target_agent="alfred",
            action="clarify",
            parameters={},
            user_id=user_id,
        )

    return Intent(
        raw_message=raw_message,
        target_agent=parsed.get("target_agent", "alfred"),
        action=parsed.get("action", "clarify"),
        parameters=parsed.get("parameters", {}),
        user_id=user_id,
    )


async def dispatch(intent: Intent):
    agent = AGENT_REGISTRY.get(intent.target_agent)

    if agent is None:
        from shared.models import AgentResponse, ActionType
        return AgentResponse(
            agent="alfred",
            result=f"No agent named '{intent.target_agent}' is registered.",
            action_type=ActionType.INFORM,
            error="routing_error",
        )

    return await agent.handle(intent)
