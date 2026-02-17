from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from keyboards import back_button, main_menu

EVENT_ICONS = {
    "start":             "🚀",
    "channel_added":     "➕",
    "post_created":      "📝",
    "post_published":    "📤",
    "post_deleted":      "🗑",
    "multipost_sent":    "📤",
    "post_scheduled":    "⏰",
    "scheduled_sent":    "✅",
    "scheduled_failed":  "❌",
    "scheduled_deleted": "🗑",
    "settings_changed":  "⚙",
}


async def cb_event_log(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    events  = db.get_events(user_id, limit=30)

    if not events:
        await q.edit_message_text(
            "📊 <b>Event Log</b>\n\nNo events yet.",
            parse_mode="HTML",
            reply_markup=back_button()
        )
        return

    lines = []
    for ev in events:
        icon = EVENT_ICONS.get(ev["event_type"], "•")
        ts   = str(ev["created_at"])[:16]
        lines.append(f"{icon} <code>{ts}</code>  {ev['description']}")

    text = "📊 <b>Event Log</b> (last 30)\n\n" + "\n".join(lines)

    # Telegram message limit safety
    if len(text) > 4000:
        text = text[:3990] + "\n…"

    await q.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Clear Log", callback_data="clear_log")],
            [InlineKeyboardButton("« Back",      callback_data="main_menu")],
        ])
    )


async def cb_clear_log(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db.clear_events(q.from_user.id)
    await q.edit_message_text("🗑 Event log cleared.", reply_markup=main_menu())
