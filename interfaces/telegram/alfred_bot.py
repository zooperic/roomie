"""
Alfred Bot - Main orchestrator bot with photo pipeline support
"""
import base64
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from interfaces.telegram.base_bot import BaseAgentBot


class AlfredBot(BaseAgentBot):
    """Alfred orchestrator bot - handles all intents + photo pipeline"""
    
    def __init__(self):
        super().__init__(
            agent_name="alfred",
            token_env_var="TELEGRAM_TOKEN_ALFRED",
            description="I'm the orchestrator. I route your requests to the right agent and handle confirmations."
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Override base class - Alfred uses normal routing, not force_agent"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("Unauthorized.")
            return
        
        # Group chat support
        is_group = update.message.chat.type in ["group", "supergroup"]
        if is_group:
            bot_username = f"@{context.bot.username}"
            if bot_username.lower() not in update.message.text.lower():
                return
        
        session_id = f"tg_alfred_{update.effective_user.id}_{update.message.message_id}"
        await update.message.reply_chat_action("typing")
        
        message_text = update.message.text
        if is_group and context.bot.username:
            message_text = message_text.replace(f"@{context.bot.username}", "").strip()
        
        try:
            # DON'T set force_agent - let Alfred route naturally
            result = await self.call_alfred("/message", {
                "message": message_text,
                "user_id": str(update.effective_user.id),
                "session_id": session_id,
                # NO force_agent here!
            })
        except Exception as e:
            self.log.error(f"Error: {e}")
            await update.message.reply_text(f"Error: {e}")
            return
        
        if result.get("status") == "awaiting_confirmation":
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{result['session_id']}"),
                InlineKeyboardButton("❌ Cancel",  callback_data=f"cancel:{result['session_id']}"),
            ]])
            await update.message.reply_text(
                f"*Alfred needs approval:*\n\n{result['message']}\n\n"
                f"_Confidence: {result.get('confidence', 0):.0%}_",
                reply_markup=keyboard, parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                self.format_result(result.get("result", "Done.")),
                parse_mode="Markdown"
            )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle fridge photos for inventory scanning"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("Unauthorized.")
            return
        
        await update.message.reply_chat_action("typing")
        await update.message.reply_text("📸 Analyzing your fridge... This may take a moment.")
        
        try:
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
            
            result = await self.call_alfred("/scan_fridge", {
                "image_base64": photo_base64,
                "user_id": str(update.effective_user.id),
            })
            
            if result.get("status") == "awaiting_confirmation":
                diff_text = self.format_inventory_diff(result.get("diff", {}))
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{result['session_id']}"),
                    InlineKeyboardButton("❌ Cancel",  callback_data=f"cancel:{result['session_id']}"),
                ]])
                await update.message.reply_text(
                    f"*Detected changes:*\n\n{diff_text}\n\nConfirm to update inventory?",
                    reply_markup=keyboard, parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(result.get("message", "Photo processed."))
        except Exception as e:
            self.log.error(f"Photo processing error: {e}")
            await update.message.reply_text(f"Error processing photo: {e}")
    
    def format_inventory_diff(self, diff: dict) -> str:
        """Format inventory diff for display"""
        lines = []
        
        added = diff.get("added", [])
        removed = diff.get("removed", [])
        updated = diff.get("updated", [])
        
        if added:
            lines.append("*Added:*")
            for item in added:
                lines.append(f"  + {item['name']} — {item['quantity']} {item.get('unit', '')}")
        
        if removed:
            lines.append("\n*Removed:*")
            for item in removed:
                lines.append(f"  - {item['name']}")
        
        if updated:
            lines.append("\n*Updated:*")
            for item in updated:
                old_qty = item.get('old_quantity', '?')
                new_qty = item['quantity']
                unit = item.get('unit', '')
                lines.append(f"  ~ {item['name']}: {old_qty} → {new_qty} {unit}")
        
        return "\n".join(lines) if lines else "_No changes detected_"
    
    def run(self):
        """Start Alfred bot with photo handler"""
        if not self.token:
            self.log.warning(f"No token for {self.agent_name} bot - skipping")
            return None
        
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        self.log.info(f"{self.agent_name.capitalize()} bot starting...")
        return app


if __name__ == "__main__":
    bot = AlfredBot()
    app = bot.run()
    if app:
        app.run_polling(allowed_updates=["message", "callback_query"])
