from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler,
                           MessageHandler, filters, CallbackQueryHandler)

import database as db
from keyboards import main_menu, post_list_keyboard, scheduled_list_keyboard, back_button

# States
SEL_POST, SEL_CHANNEL, WAIT_DATETIME = range(3)


# ── Schedule Post ────────────────────────────────────────────────────────────

async def cb_schedule_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    posts   = db.get_posts(user_id)

    if not posts:
        await q.edit_message_text(
            "📂 No posts found. Create one first.",
            reply_markup=back_button()
        )
        return SEL_POST

    await q.edit_message_text(
        "⏰ <b>Schedule Post</b>\n\nStep 1: Pick the post to schedule:",
        parse_mode="HTML",
        reply_markup=post_list_keyboard(posts, "sched_post")
    )
    return SEL_POST


async def cb_sched_select_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    post_id = int(q.data.split(":")[1])
    ctx.user_data["sched_post_id"] = post_id

    user_id  = q.from_user.id
    channels = db.get_channels(user_id)

    if not channels:
        await q.edit_message_text("❌ No channels. Add one first.", reply_markup=back_button())
        return ConversationHandler.END

    rows = [
        [InlineKeyboardButton(
            f"📢 {ch['channel_name'] or ch['channel_id']}",
            callback_data=f"sched_ch:{ch['channel_id']}:{ch['channel_name'] or ''}"
        )]
        for ch in channels
    ]
    rows.append([InlineKeyboardButton("« Back", callback_data="main_menu")])

    await q.edit_message_text(
        "⏰ <b>Schedule Post</b>\n\nStep 2: Choose the target channel:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows)
    )
    return SEL_CHANNEL


async def cb_sched_select_channel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split(":", 2)
    ctx.user_data["sched_channel_id"]   = parts[1]
    ctx.user_data["sched_channel_name"] = parts[2] if len(parts) > 2 else parts[1]

    await q.edit_message_text(
        "⏰ <b>Schedule Post</b>\n\n"
        "Step 3: Send me the date and time in this format:\n\n"
        "<code>YYYY-MM-DD HH:MM</code>\n\n"
        "Example: <code>2025-12-31 18:00</code>\n"
        "<i>(All times in UTC)</i>\n\n"
        "Send /cancel to abort.",
        parse_mode="HTML"
    )
    return WAIT_DATETIME


async def recv_schedule_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime, timezone
    text    = update.message.text.strip()
    user_id = update.effective_user.id

    try:
        dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
        if dt < datetime.utcnow():
            await update.message.reply_text(
                "❌ That time is in the past! Try again or /cancel."
            )
            return WAIT_DATETIME
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Use <code>YYYY-MM-DD HH:MM</code> (e.g. 2025-12-31 18:00)",
            parse_mode="HTML"
        )
        return WAIT_DATETIME

    post_id      = ctx.user_data["sched_post_id"]
    channel_id   = ctx.user_data["sched_channel_id"]
    channel_name = ctx.user_data["sched_channel_name"]
    post         = db.get_post(post_id)

    sched_id = db.schedule_post(
        user_id, channel_id, channel_name,
        scheduled_time=text,
        content=post["content"],
        media_file_id=post["media_file_id"],
        media_type=post["media_type"],
        post_id=post_id
    )

    db.log_event(user_id, "post_scheduled",
                 f"Post #{post_id} scheduled for {text} → {channel_name}",
                 channel_id=channel_id, post_id=post_id)

    await update.message.reply_text(
        f"✅ Post scheduled for <b>{text} UTC</b> → <b>{channel_name}</b>",
        parse_mode="HTML", reply_markup=main_menu()
    )
    return ConversationHandler.END


async def cmd_cancel_sched(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Cancelled.", reply_markup=main_menu())
    return ConversationHandler.END


def schedule_conv():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_schedule_post, pattern="^schedule_post$")],
        states={
            SEL_POST: [
                CallbackQueryHandler(cb_sched_select_post, pattern="^sched_post:"),
            ],
            SEL_CHANNEL: [
                CallbackQueryHandler(cb_sched_select_channel, pattern="^sched_ch:"),
            ],
            WAIT_DATETIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_schedule_time),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel_sched)],
        per_message=False
    )


# ── Delete Scheduled ─────────────────────────────────────────────────────────

async def cb_delete_scheduled(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id   = q.from_user.id
    scheduled = db.get_scheduled_posts(user_id)

    if not scheduled:
        await q.edit_message_text(
            "⏰ No pending scheduled posts.", reply_markup=back_button()
        )
        return

    await q.edit_message_text(
        "🗑 <b>Delete Scheduled Post</b>\n\nTap a post to remove it:",
        parse_mode="HTML",
        reply_markup=scheduled_list_keyboard(scheduled)
    )


async def cb_del_sched_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    sched_id = int(q.data.split(":")[1])
    user_id  = q.from_user.id

    db.delete_scheduled(sched_id, user_id)
    db.log_event(user_id, "scheduled_deleted", f"Deleted scheduled post #{sched_id}")

    await q.edit_message_text(
        "🗑 Scheduled post removed.",
        reply_markup=back_button()
    )
