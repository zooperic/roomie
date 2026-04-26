"""
Remy Bot - Direct kitchen/pantry Telegram access
Extends BaseAgentBot with:
  - Servings extraction from natural language ("for 4 people")
  - Ask-back when servings aren't mentioned
  - Human-readable recipe result formatting
  - Inline confirm/deny for Lebowski handoff
"""
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from interfaces.telegram.base_bot import BaseAgentBot
from shared.llm_provider import get_llm_response


SERVINGS_PATTERN = re.compile(
    r"\b(?:for\s+)?(\d+)\s*(?:people|persons|servings?|portions?|pax)\b",
    re.IGNORECASE,
)

# Dishes that strongly suggest recipe parsing intent
RECIPE_TRIGGERS = [
    "make", "cook", "prepare", "recipe", "ingredients", "want to",
    "going to", "planning to", "http", "https://",
]


def _extract_servings_from_text(text: str) -> tuple[str, int | None]:
    """
    Pull a servings number out of natural language.
    Returns (cleaned_text, servings_or_None).
    e.g. "make dal makhani for 3 people" → ("make dal makhani", 3)
    """
    match = SERVINGS_PATTERN.search(text)
    if match:
        servings = int(match.group(1))
        # Remove the servings phrase from the message
        cleaned = SERVINGS_PATTERN.sub("", text).strip().rstrip(",").strip()
        return cleaned, servings
    return text, None


def _looks_like_recipe_request(text: str) -> bool:
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in RECIPE_TRIGGERS)


class RemyBot(BaseAgentBot):
    """Remy bot - direct kitchen and pantry access without Alfred routing"""

    def __init__(self):
        super().__init__(
            agent_name="remy",
            token_env_var="TELEGRAM_TOKEN_REMY",
            description=(
                "I'm Remy, your kitchen assistant.\n\n"
                "I can:\n"
                "• Parse recipes from URLs, dish names, or pasted text\n"
                "• Check your pantry and fridge\n"
                "• Tell you what's missing and order it on Swiggy\n"
                "• Suggest meals from what you have\n\n"
                "Just tell me what you want to cook!"
            )
        )
        # Pending servings asks: {chat_id: {message: str, asked: bool}}
        self._pending_servings: dict[int, dict] = {}

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("Unauthorized.")
            return

        user_text = update.message.text.strip()
        chat_id = update.message.chat_id

        # Check if this is a reply to a servings question
        pending = self._pending_servings.pop(chat_id, None)
        if pending:
            servings = self._parse_servings_reply(user_text)
            if servings:
                # Re-attach servings to the original message and process
                original_msg = pending["original_message"]
                await update.message.reply_chat_action("typing")
                await self._process_recipe_message(update, context, original_msg, servings)
                return
            else:
                # User replied something else — treat as new message, not servings reply
                pass

        # Extract servings inline from the message
        cleaned_text, servings = _extract_servings_from_text(user_text)

        # If it looks like a recipe request and no servings given → ask back
        if (
            _looks_like_recipe_request(user_text)
            and servings is None
            and len(user_text) < 200  # don't ask for pasted recipe blocks
        ):
            self._pending_servings[chat_id] = {"original_message": cleaned_text}
            await self._ask_servings(update, cleaned_text)
            return

        # Normal flow
        await update.message.reply_chat_action("typing")
        await self._process_recipe_message(update, context, cleaned_text, servings)

    async def _ask_servings(self, update: Update, dish_hint: str):
        """Ask how many people they're cooking for."""
        # Inline buttons for common answers
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Just me (1)", callback_data="servings:1"),
                InlineKeyboardButton("2 people", callback_data="servings:2"),
                InlineKeyboardButton("4 people", callback_data="servings:4"),
            ],
            [
                InlineKeyboardButton("6 people", callback_data="servings:6"),
                InlineKeyboardButton("Skip / Default", callback_data="servings:0"),
            ],
        ])

        dish_display = dish_hint[:40] + "..." if len(dish_hint) > 40 else dish_hint
        await update.message.reply_text(
            f"How many people are you cooking for? 🍽️\n"
            f"_(Or just type a number like '3')_",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    def _parse_servings_reply(self, text: str) -> int | None:
        """Parse a short servings reply like '3', 'four', 'just me'."""
        text = text.strip().lower()
        # Direct number
        if text.isdigit():
            return int(text)
        # Word numbers
        word_map = {
            "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8,
            "just me": 1, "myself": 1, "solo": 1,
        }
        for word, num in word_map.items():
            if word in text:
                return num
        # Pattern match
        match = SERVINGS_PATTERN.search(text)
        if match:
            return int(match.group(1))
        return None

    async def _process_recipe_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message: str,
        servings: int | None,
    ):
        """Send the (possibly servings-augmented) message to Alfred/Remy."""
        user_id = str(update.effective_user.id)
        session_id = f"tg_remy_{user_id}_{update.message.message_id}"

        # Append servings to message so the router picks it up
        full_message = message
        if servings and servings > 0:
            full_message = f"{message} for {servings} servings"

        try:
            result = await self.call_alfred("/message", {
                "message": full_message,
                "user_id": user_id,
                "session_id": session_id,
                "force_agent": "remy",
            })
        except Exception as e:
            self.log.error(f"Alfred call failed: {e}")
            await update.message.reply_text(
                "Something went sideways on my end — give it another shot in a second."
            )
            return

        formatted = self._format_remy_result(result)

        # If result has a Lebowski handoff payload, show confirm buttons
        response_data = result.get("result", {})
        payload = None
        if isinstance(response_data, dict):
            payload = response_data.get("suggested_action_payload") or result.get("suggested_action_payload")

        if payload and payload.get("action") == "send_to_lebowski":
            import json
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "✅ Yes, order on Swiggy",
                    callback_data=f"lebowski:{session_id}",
                ),
                InlineKeyboardButton(
                    "❌ No thanks",
                    callback_data=f"skip_lebowski:{session_id}",
                ),
            ]])
            # Store the payload for the callback
            context.chat_data[f"lebowski_{session_id}"] = payload

            await update.message.reply_text(
                formatted,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(formatted, parse_mode="Markdown")

    # ------------------------------------------------------------------
    # Callback handling (servings buttons + Lebowski confirm)
    # ------------------------------------------------------------------

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        # Servings button
        if data.startswith("servings:"):
            servings_val = int(data.split(":")[1])
            chat_id = query.message.chat_id
            pending = self._pending_servings.pop(chat_id, None)

            if not pending:
                await query.edit_message_text("Got it! Send your recipe request again and I'll include the servings.")
                return

            original_msg = pending["original_message"]
            if servings_val == 0:
                # Skip — use default servings
                servings_val = None

            await query.edit_message_text(
                f"On it! Parsing{'...' if not servings_val else f' for {servings_val} people...'}"
            )

            # Create a fake Update to reuse _process_recipe_message
            await self._process_recipe_message(
                update=update,
                context=context,
                message=original_msg,
                servings=servings_val,
            )
            return

        # Lebowski handoff confirm
        if data.startswith("lebowski:"):
            session_id = data[len("lebowski:"):]
            payload = context.chat_data.pop(f"lebowski_{session_id}", None)

            if not payload:
                await query.edit_message_text("Couldn't find the order details anymore. Try parsing the recipe again.")
                return

            await query.edit_message_text("Sending to Lebowski... 🛒")

            try:
                result = await self.call_alfred("/message", {
                    "message": f"build cart for {payload.get('dish', 'this recipe')}",
                    "user_id": str(query.from_user.id),
                    "session_id": f"lebowski_{session_id}",
                    "force_agent": "lebowski",
                    "parameters": {
                        "action": "build_cart",
                        "items": payload.get("items", []),
                    },
                })
                formatted = self._format_cart_result(result)
                await query.edit_message_text(formatted, parse_mode="Markdown")
            except Exception as e:
                self.log.error(f"Lebowski handoff failed: {e}")
                await query.edit_message_text(
                    "Lebowski's having trouble right now. Try again in a moment."
                )
            return

        if data.startswith("skip_lebowski:"):
            await query.edit_message_text("No problem! Let me know if you change your mind. 👨‍🍳")
            return

        # Fallback to base confirm/cancel
        await super().handle_callback(update, context)

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def _format_remy_result(self, api_result: dict) -> str:
        """
        Format Remy's recipe parse result into a clean Telegram message.
        Handles both the recipe parse response and generic string responses.
        """
        result = api_result.get("result", "")
        suggested = api_result.get("suggested_action", "")

        # Plain string (e.g. errors, meal suggestions)
        if isinstance(result, str):
            if suggested:
                return f"{result}\n\n_{suggested}_"
            return result

        if not isinstance(result, dict):
            return str(result)

        # Recipe parse result
        if "dish" in result:
            dish = result.get("dish", "Recipe")
            servings = result.get("servings")
            available = result.get("available", [])
            missing = result.get("missing", [])
            total = result.get("total_ingredients", 0)

            lines = [f"*{dish}*"]
            if servings:
                lines.append(f"_{servings} servings_")
            lines.append("")

            if available:
                lines.append(f"✅ *Have ({len(available)}):*")
                lines.append(", ".join(available))
                lines.append("")

            if missing:
                lines.append(f"🛒 *Need to buy ({len(missing)}):*")
                for item in missing:
                    qty_str = ""
                    if isinstance(item, dict):
                        qty = item.get("quantity")
                        unit = item.get("unit", "")
                        name = item.get("name", str(item))
                        if qty:
                            qty_str = f" — {qty} {unit}".rstrip()
                    else:
                        name = str(item)
                    lines.append(f"• {name}{qty_str}")
                lines.append("")

            if not missing:
                lines.append("🎉 You have everything!")
            elif suggested:
                lines.append(f"_{suggested}_")

            return "\n".join(lines)

        # Inventory result
        if "found" in result:
            return self.format_result(result)

        # Low stock
        if "low_stock_items" in result:
            return self.format_result(result)

        # Fallback
        return str(result)

    def _format_cart_result(self, api_result: dict) -> str:
        """Format Lebowski's cart result for Telegram."""
        result = api_result.get("result", {})

        if isinstance(result, str):
            return result

        if not isinstance(result, dict):
            return str(result)

        if "matched_items" in result:
            items = result.get("matched_items", [])
            total = result.get("total_cost", 0)
            lines = [f"*Cart ready* 🛒\n"]
            for item in items:
                if item.get("matched"):
                    price = item.get("total_price", 0)
                    lines.append(f"• {item['matched']} — ₹{price}")
                else:
                    lines.append(f"• _{item['query']} (not found)_")
            lines.append(f"\n*Total: ₹{total}*")
            return "\n".join(lines)

        return str(result)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self):
        if not self.token:
            self.log.warning("No token for remy bot — skipping")
            return None

        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(CallbackQueryHandler(self.handle_callback))

        self.log.info("Remy bot starting...")
        return app


if __name__ == "__main__":
    bot = RemyBot()
    app = bot.run()
    if app:
        app.run_polling(allowed_updates=["message", "callback_query"])
