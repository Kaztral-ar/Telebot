from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler

import database as db
from keyboards import main_menu, back_button

WAIT_TIMEZONE = 1

COMMON_TIMEZONES = [
    "UTC", "US/Eastern", "US/Central", "US/Pacific",
    "Europe/London", "Europe/Paris", "Europe/Moscow",
    "Asia/Dubai", "Asia/Kolkata", "Asia/Singapore", "Asia/Tokyo",
    "Australia/Sydney", "America/Sao_Paulo"
]


async def cb_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id  = q.from_user.id
    settings = db.get_settings(user_id)

    text = (
        "⚙ <b>Settings</b>\n\n"
        f"🕐 Timezone: <b>{settings['timezone']}</b>\n"
        f"🔔 Notifications: <b>{'On' if settings['notifications'] else 'Off'}</b>\n"
    )

    notif_label = "🔕 Turn Off Notifs" if settings["notifications"] else "🔔 Turn On Notifs"
    keyboard = [
        [InlineKeyboardButton("🕐 Change Timezone", callback_data="set_timezone")],
        [InlineKeyboardButton(notif_label,           callback_data="toggle_notif")],
        [InlineKeyboardButton("« Back",              callback_data="main_menu")],
    ]
    await q.edit_message_text(text, parse_mode="HTML",
                              reply_markup=InlineKeyboardMarkup(keyboard))


async def cb_toggle_notif(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id  = q.from_user.id
    settings = db.get_settings(user_id)
    new_val  = 0 if settings["notifications"] else 1
    db.update_setting(user_id, "notifications", new_val)
    db.log_event(user_id, "settings_changed",
                 f"Notifications {'enabled' if new_val else 'disabled'}")
    # re-render
    await cb_settings(update, ctx)


async def cb_set_timezone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    rows = [
        [InlineKeyboardButton(tz, callback_data=f"tz:{tz}")]
        for tz in COMMON_TIMEZONES
    ]
    rows.append([InlineKeyboardButton("✏️ Enter manually", callback_data="tz_manual")])
    rows.append([InlineKeyboardButton("« Back", callback_data="settings")])

    await q.edit_message_text(
        "🕐 <b>Select Timezone</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows)
    )
    return ConversationHandler.END


async def cb_tz_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tz      = q.data.split(":", 1)[1]
    user_id = q.from_user.id
    db.update_setting(user_id, "timezone", tz)
    db.log_event(user_id, "settings_changed", f"Timezone set to {tz}")
    await q.edit_message_text(f"✅ Timezone set to <b>{tz}</b>",
                              parse_mode="HTML", reply_markup=main_menu())


async def cb_tz_manual(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🕐 Send your timezone string (e.g. <code>America/New_York</code>):\n\n"
        "See full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
        parse_mode="HTML"
    )
    return WAIT_TIMEZONE


async def recv_timezone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tz      = update.message.text.strip()
    user_id = update.effective_user.id
    db.update_setting(user_id, "timezone", tz)
    db.log_event(user_id, "settings_changed", f"Timezone set to {tz}")
    await update.message.reply_text(
        f"✅ Timezone set to <b>{tz}</b>",
        parse_mode="HTML", reply_markup=main_menu()
    )
    return ConversationHandler.END


def settings_tz_conv():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_tz_manual, pattern="^tz_manual$")],
        states={
            WAIT_TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_timezone)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_message=False
    )
