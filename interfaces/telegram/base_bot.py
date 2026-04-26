"""
Base bot implementation - shared logic for all agent bots
"""
import os
import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

# ── Logging setup ──────────────────────────────────────────────────────────────
# Keep Alfred/agent logs clean. Silence the httpx polling noise from telegram bots.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
# httpx logs every Telegram getUpdates call (every 10s per bot) — pure noise
logging.getLogger("httpx").setLevel(logging.WARNING)
# python-telegram-bot internals — only show warnings+
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

ALFRED_URL = os.getenv("ALFRED_URL", "http://localhost:8000")
ALLOWED_USER_IDS = [int(uid) for uid in os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").split(",") if uid]


class BaseAgentBot:
    """Base class for all agent-specific Telegram bots"""
    
    def __init__(self, agent_name: str, token_env_var: str, description: str):
        self.agent_name = agent_name
        self.token = os.getenv(token_env_var)
        self.description = description
        self.log = logging.getLogger(f"bot.{agent_name}")
        
    def is_authorized(self, user_id: int) -> bool:
        return user_id in ALLOWED_USER_IDS if ALLOWED_USER_IDS else True
    
    async def call_alfred(self, endpoint: str, payload: dict) -> dict:
        """Call Alfred API"""
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(f"{ALFRED_URL}{endpoint}", json=payload)
            response.raise_for_status()
            return response.json()
    
    def format_result(self, result) -> str:
        """Format agent response for human-readable display"""
        if isinstance(result, dict):
            # Handle inventory check response
            if "found" in result:
                items = result["found"]
                if not items:
                    return "Fridge is empty."
                lines = ["*Your Fridge:*\n"]
                for item in items:
                    lines.append(f"• {item['name'].title()}: {item['quantity']} {item['unit']}")
                return "\n".join(lines)
            
            # Handle low stock response
            if "low_stock_items" in result:
                items = result["low_stock_items"]
                if not items:
                    return "Everything is well-stocked!"
                lines = ["*Running Low:*\n"]
                for item in items:
                    lines.append(f"• {item['name'].title()}: {item['quantity']} {item['unit']} (threshold: {item['threshold']})")
                return "\n".join(lines)
            
            # Handle recipe parse response
            if "dish" in result:
                dish = result["dish"]
                available = result.get("available", [])
                missing = result.get("missing", [])
                lines = [f"*Recipe: {dish}*\n"]
                if available:
                    lines.append("✅ Have: " + ", ".join(available))
                if missing:
                    lines.append("❌ Need: " + ", ".join([m["name"] if isinstance(m, dict) else m for m in missing]))
                return "\n".join(lines)
            
            # Handle cart/order response
            if "cart" in result:
                cart = result["cart"]
                lines = ["*Shopping Cart:*\n"]
                for item in cart:
                    lines.append(f"• {item['name']}: {item['quantity']} {item.get('unit', 'units')}")
                return "\n".join(lines)
            
            # Fallback for other dicts - just stringify
            return str(result)
        
        # For non-dict results (strings, numbers), return as-is
        return str(result)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("Unauthorized.")
            return
        await update.message.reply_text(
            f"*{self.agent_name.capitalize()} Bot*\n\n{self.description}\n\n"
            f"Just send me messages directly - no need to mention Alfred.",
            parse_mode="Markdown"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - routes directly to specific agent"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("Unauthorized.")
            return
        
        # Group chat support
        is_group = update.message.chat.type in ["group", "supergroup"]
        if is_group:
            bot_username = f"@{context.bot.username}"
            if bot_username.lower() not in update.message.text.lower():
                return
        
        session_id = f"tg_{self.agent_name}_{update.effective_user.id}_{update.message.message_id}"
        await update.message.reply_chat_action("typing")
        
        message_text = update.message.text
        if is_group and context.bot.username:
            message_text = message_text.replace(f"@{context.bot.username}", "").strip()
        
        try:
            # Route directly to agent (bypass Alfred's router)
            result = await self.call_alfred("/message", {
                "message": message_text,
                "user_id": str(update.effective_user.id),
                "session_id": session_id,
                "force_agent": self.agent_name,  # Force routing to this agent
            })
        except Exception as e:
            self.log.error(f"Error: {e}")
            await update.message.reply_text(f"Error: {e}")
            return
        
        if result.get("status") == "awaiting_confirmation":
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{result['session_id']}"),
                InlineKeyboardButton("❌ Cancel",  callback_data=f"cancel:{result['session_id']}"),
            ]])
            await update.message.reply_text(
                f"*{self.agent_name.capitalize()} needs approval:*\n\n{result['message']}\n\n"
                f"_Confidence: {result.get('confidence', 0):.0%}_",
                reply_markup=keyboard, parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                self.format_result(result.get("result", "Done.")),
                parse_mode="Markdown"
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        action, session_id = query.data.split(":", 1)
        try:
            result = await self.call_alfred("/confirm", {
                "session_id": session_id,
                "confirmed": action == "confirm"
            })
            await query.edit_message_text(f"{'✅' if action == 'confirm' else '❌'} {result.get('message', '')}")
        except Exception as e:
            self.log.error(f"Callback error: {e}")
            await query.edit_message_text(f"Error: {e}")
    
    def run(self):
        """Start the bot"""
        if not self.token:
            self.log.warning(f"No token for {self.agent_name} bot - skipping")
            return None
        
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        self.log.info(f"{self.agent_name.capitalize()} bot starting...")
        return app
