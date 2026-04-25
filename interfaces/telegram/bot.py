import os
import httpx
import logging
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

    session_id = f"tg_{update.effective_user.id}_{update.message.message_id}"
    await update.message.reply_chat_action("typing")

    try:
        result = await call_alfred("/message", {
            "message": update.message.text,
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
            format_result(result.get("result", "Done.")) + f"\n\n_— {result.get('agent', 'alfred')}_",
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


def run_bot():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN not set in .env")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("inventory", inventory_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    log.info("Telegram bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
