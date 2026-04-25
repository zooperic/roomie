"""
Remy Bot - Direct kitchen/pantry access (Phase 2)
"""
from interfaces.telegram.base_bot import BaseAgentBot


class RemyBot(BaseAgentBot):
    """Remy bot - direct kitchen and pantry access without Alfred routing"""
    
    def __init__(self):
        super().__init__(
            agent_name="remy",
            token_env_var="TELEGRAM_TOKEN_REMY",
            description="I manage your kitchen and pantry. Ask me about recipes, meal planning, or pantry inventory."
        )


if __name__ == "__main__":
    bot = RemyBot()
    app = bot.run()
    if app:
        app.run_polling(allowed_updates=["message", "callback_query"])
