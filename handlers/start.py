from telegram import Update
from telegram.ext import ContextTypes

import database as db
from keyboards import main_menu


WELCOME_TEXT = (
    "👋 <b>Welcome to Telebot</b>\n\n"
    "Your Telegram Channel Automation Hub.\n"
    "Choose an option below to get started."
)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_settings(user.id)          # ensure settings row exists
    db.log_event(user.id, "start", "User started bot")
    await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML",
                                    reply_markup=main_menu())


async def cb_main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(WELCOME_TEXT, parse_mode="HTML",
                              reply_markup=main_menu())


async def cb_exit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("👋 Goodbye! Type /start to return.", parse_mode="HTML")
