from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler

import database as db
from keyboards import main_menu, channel_list_keyboard

# Conversation states
WAIT_CHANNEL_ID = 1


async def cb_add_channel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["prev_msg_id"] = q.message.message_id
    await q.edit_message_text(
        "📢 <b>Add a Channel</b>\n\n"
        "1️⃣ Add me as an <b>Administrator</b> to your channel.\n"
        "2️⃣ Send me the channel username or ID.\n\n"
        "<i>Example: @mychannel  or  -1001234567890</i>\n\n"
        "Send /cancel to abort.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Back", callback_data="main_menu")
        ]])
    )
    return WAIT_CHANNEL_ID


async def recv_channel_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Validate by fetching chat info
    try:
        chat = await ctx.bot.get_chat(text)
    except Exception as e:
        await update.message.reply_text(
            f"❌ Could not access that channel.\n<code>{e}</code>\n\n"
            "Make sure I'm an admin there, then try again or /cancel.",
            parse_mode="HTML"
        )
        return WAIT_CHANNEL_ID

    channel_id   = str(chat.id)
    channel_name = chat.title or chat.username or channel_id

    ok = db.add_channel(user_id, channel_id, channel_name)
    if ok:
        db.log_event(user_id, "channel_added", f"Added channel {channel_name}", channel_id=channel_id)
        await update.message.reply_text(
            f"✅ Channel <b>{channel_name}</b> added!",
            parse_mode="HTML", reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            f"⚠️ Channel <b>{channel_name}</b> is already in your list.",
            parse_mode="HTML", reply_markup=main_menu()
        )

    return ConversationHandler.END


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Cancelled.", reply_markup=main_menu())
    return ConversationHandler.END


def add_channel_conv():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_add_channel, pattern="^add_channel$")],
        states={
            WAIT_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_channel_id)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=False
    )
