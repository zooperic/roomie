"""
Elsa Bot - Direct fridge inventory access
"""
from interfaces.telegram.base_bot import BaseAgentBot


class ElsaBot(BaseAgentBot):
    """Elsa bot - direct access to fridge inventory without Alfred routing"""
    
    def __init__(self):
        super().__init__(
            agent_name="elsa",
            token_env_var="TELEGRAM_TOKEN_ELSA",
            description="I manage your fridge inventory. Ask me what's in the fridge, add items, or check what's running low."
        )


if __name__ == "__main__":
    bot = ElsaBot()
    app = bot.run()
    if app:
        app.run_polling(allowed_updates=["message", "callback_query"])
