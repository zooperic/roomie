import os
import httpx
import logging
import base64
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
ALFRED_BASE_URL  = os.getenv("ALFRED_URL", "http://localhost:8000")
ALLOWED_USER_IDS = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").split(",")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS or ALLOWED_USER_IDS == [""]:
        return True
    return str(user_id) in ALLOWED_USER_IDS


async def call_alfred(endpoint: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{ALFRED_BASE_URL}{endpoint}", json=payload)
        response.raise_for_status()
        return response.json()


def format_result(result) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        lines = []
        for k, v in result.items():
            if isinstance(v, list):
                lines.append(f"*{k.replace('_', ' ').title()}*:")
                for item in v:
                    if isinstance(item, dict):
                        lines.append(f"  • {item.get('name', item)} — {item.get('quantity', '')} {item.get('unit', '')}")
                    else:
                        lines.append(f"  • {item}")
            else:
                lines.append(f"*{k.replace('_', ' ').title()}*: {v}")
        return "\n".join(lines)
    return str(result)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await update.message.reply_text(
        "👋 *Project Roomy online.*\n\nI'm Alfred. Talk to me naturally.\n\n"
        "Examples:\n• _What's in the fridge?_\n• _I bought 2L milk_\n• _What's running low?_\n\n"
        "/status — System status\n/inventory — Full fridge inventory",
        parse_mode="Markdown"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{ALFRED_BASE_URL}/status")
        data = resp.json()
    elsa = data.get("agents", {}).get("elsa", {})
    await update.message.reply_text(
        f"*🏠 Roomy Status*\n\nAlfred: ✅ Online\n"
        f"Elsa: {'✅' if elsa.get('healthy') else '❌'} — {elsa.get('summary', 'No data')}\n"
        f"Pending: {data.get('pending_confirmations', 0)}",
        parse_mode="Markdown"
    )


async def inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    result = await call_alfred("/message", {"message": "show me everything in the fridge", "user_id": str(update.effective_user.id)})
    await update.message.reply_text(format_result(result.get("result", result)), parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    # Group chat support: only respond when bot is mentioned
    is_group = update.message.chat.type in ["group", "supergroup"]
    if is_group:
        bot_username = f"@{context.bot.username}"
        if bot_username not in update.message.text:
            return  # Ignore messages in groups where bot isn't tagged

    session_id = f"tg_{update.effective_user.id}_{update.message.message_id}"
    await update.message.reply_chat_action("typing")

    # Remove bot mention from message before sending to Alfred
    message_text = update.message.text
    if is_group and context.bot.username:
        message_text = message_text.replace(f"@{context.bot.username}", "").strip()

    try:
        result = await call_alfred("/message", {
            "message": message_text,
            "user_id": str(update.effective_user.id),
            "session_id": session_id,
        })
    except Exception as e:
        await update.message.reply_text(f"Alfred error: {e}")
        return

    if result.get("status") == "awaiting_confirmation":
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{result['session_id']}"),
            InlineKeyboardButton("❌ Cancel",  callback_data=f"cancel:{result['session_id']}"),
        ]])
        await update.message.reply_text(
            f"*Alfred needs approval:*\n\n{result['message']}\n\n_Confidence: {result.get('confidence', 0):.0%}_",
            reply_markup=keyboard, parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            format_result(result.get("result", "Done.")),
            parse_mode="Markdown"
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, session_id = query.data.split(":", 1)
    try:
        result = await call_alfred("/confirm", {"session_id": session_id, "confirmed": action == "confirm"})
        await query.edit_message_text(f"{'✅' if action == 'confirm' else '❌'} {result.get('message', '')}")
    except Exception as e:
        await query.edit_message_text(f"Error: {e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fridge photos for inventory scanning"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return

    await update.message.reply_chat_action("typing")
    await update.message.reply_text("📸 Analyzing your fridge... This may take a moment.")

    try:
        # Get the largest photo size
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        
        # Download photo as bytes
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Convert to base64
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Send to Alfred's vision endpoint
        result = await call_alfred("/scan_fridge", {
            "image_base64": photo_base64,
            "user_id": str(update.effective_user.id),
        })
        
        if result.get("status") == "awaiting_confirmation":
            # Present inventory diff for confirmation
            diff_text = format_inventory_diff(result.get("diff", {}))
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
        log.error(f"Photo processing error: {e}")
        await update.message.reply_text(f"Error processing photo: {e}")


def format_inventory_diff(diff: dict) -> str:
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


def run_bot():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN not set in .env")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("inventory", inventory_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    log.info("Telegram bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
