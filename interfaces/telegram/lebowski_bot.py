"""
Lebowski Bot - Direct procurement access (Phase 2)
"""
from interfaces.telegram.base_bot import BaseAgentBot


class LebowskiBot(BaseAgentBot):
    """Lebowski bot - direct procurement access without Alfred routing"""
    
    def __init__(self):
        super().__init__(
            agent_name="lebowski",
            token_env_var="TELEGRAM_TOKEN_LEBOWSKI",
            description="I handle procurement. Tell me what to buy and I'll match it to the catalog and build your cart."
        )


if __name__ == "__main__":
    bot = LebowskiBot()
    app = bot.run()
    if app:
        app.run_polling(allowed_updates=["message", "callback_query"])
