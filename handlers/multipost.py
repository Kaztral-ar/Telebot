from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler

import database as db
from keyboards import main_menu, post_list_keyboard, back_button

# States
SELECT_POST, SELECT_CHANNELS, CONFIRM = range(3)


async def cb_multipost(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    posts   = db.get_posts(user_id)

    if not posts:
        await q.edit_message_text(
            "📂 You have no posts. Create one first via 📝 Create Post.",
            reply_markup=back_button()
        )
        return SELECT_POST

    await q.edit_message_text(
        "📤 <b>Multipost</b>\n\nStep 1: Select the post you want to send:",
        parse_mode="HTML",
        reply_markup=post_list_keyboard(posts, "mp_post")
    )
    return SELECT_POST


async def cb_mp_select_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    post_id = int(q.data.split(":")[1])
    ctx.user_data["mp_post_id"]     = post_id
    ctx.user_data["mp_selected_ch"] = []

    user_id  = q.from_user.id
    channels = db.get_channels(user_id)

    if not channels:
        await q.edit_message_text(
            "❌ You have no channels. Add one via ➕ Add Channel.",
            reply_markup=back_button()
        )
        return ConversationHandler.END

    await _show_channel_picker(q, ctx, channels)
    return SELECT_CHANNELS


async def cb_mp_toggle_channel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    channel_id = q.data.split(":")[1]
    selected   = ctx.user_data.get("mp_selected_ch", [])

    if channel_id in selected:
        selected.remove(channel_id)
    else:
        selected.append(channel_id)
    ctx.user_data["mp_selected_ch"] = selected

    user_id  = q.from_user.id
    channels = db.get_channels(user_id)
    await _show_channel_picker(q, ctx, channels)
    return SELECT_CHANNELS


async def _show_channel_picker(q, ctx, channels):
    selected = ctx.user_data.get("mp_selected_ch", [])
    rows = []
    for ch in channels:
        chk = "✅" if ch["channel_id"] in selected else "⬜"
        rows.append([InlineKeyboardButton(
            f"{chk} {ch['channel_name'] or ch['channel_id']}",
            callback_data=f"mp_toggle:{ch['channel_id']}"
        )])
    rows.append([InlineKeyboardButton(
        f"📤 Send to {len(selected)} channel(s)",
        callback_data="mp_confirm"
    )])
    rows.append([InlineKeyboardButton("« Back", callback_data="main_menu")])
    await q.edit_message_text(
        "📤 <b>Multipost</b>\n\nStep 2: Select target channels (tap to toggle):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows)
    )


async def cb_mp_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q       = update.callback_query
    await q.answer()
    user_id = q.from_user.id

    post_id    = ctx.user_data.get("mp_post_id")
    selected   = ctx.user_data.get("mp_selected_ch", [])
    post       = db.get_post(post_id)

    if not selected:
        await q.answer("⚠️ Select at least one channel!", show_alert=True)
        return SELECT_CHANNELS

    if not post:
        await q.edit_message_text("❌ Post not found.", reply_markup=main_menu())
        return ConversationHandler.END

    results = []
    for channel_id in selected:
        try:
            if post["media_file_id"] and post["media_type"] == "photo":
                await ctx.bot.send_photo(channel_id, photo=post["media_file_id"],
                                         caption=post["content"])
            elif post["media_file_id"] and post["media_type"] == "video":
                await ctx.bot.send_video(channel_id, video=post["media_file_id"],
                                         caption=post["content"])
            elif post["media_file_id"] and post["media_type"] == "document":
                await ctx.bot.send_document(channel_id, document=post["media_file_id"],
                                            caption=post["content"])
            else:
                await ctx.bot.send_message(channel_id, text=post["content"])

            db.log_event(user_id, "multipost_sent",
                         f"Post #{post_id} sent to {channel_id}",
                         channel_id=channel_id, post_id=post_id)
            results.append(f"✅ {channel_id}")
        except Exception as e:
            results.append(f"❌ {channel_id}: {e}")

    summary = "\n".join(results)
    await q.edit_message_text(
        f"📤 <b>Multipost Results</b>\n\n{summary}",
        parse_mode="HTML", reply_markup=main_menu()
    )
    return ConversationHandler.END


def multipost_conv():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_multipost, pattern="^multipost$")],
        states={
            SELECT_POST: [
                CallbackQueryHandler(cb_mp_select_post, pattern="^mp_post:"),
            ],
            SELECT_CHANNELS: [
                CallbackQueryHandler(cb_mp_toggle_channel, pattern="^mp_toggle:"),
                CallbackQueryHandler(cb_mp_confirm, pattern="^mp_confirm$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^main_menu$")],
        per_message=False
    )
