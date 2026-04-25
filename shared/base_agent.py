from abc import ABC, abstractmethod
from shared.models import AgentResponse, Intent, SkillDefinition


class BaseAgent(ABC):

    name: str = "unnamed_agent"
    description: str = "No description provided."
    version: str = "0.1.0"

    @abstractmethod
    async def handle(self, intent: Intent) -> AgentResponse:
        ...

    @abstractmethod
    async def get_status(self) -> dict:
        ...

    @abstractmethod
    def get_skills(self) -> list[SkillDefinition]:
        ...

    def skill_names(self) -> list[str]:
        return [s.name for s in self.get_skills()]

    def as_registry_entry(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "skills": [
                {
                    "name": s.name,
                    "description": s.description,
                    "triggers": s.example_triggers,
                }
                for s in self.get_skills()
            ],
        }
