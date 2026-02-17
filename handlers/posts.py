from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler,
                           MessageHandler, filters, CallbackQueryHandler)

import database as db
from keyboards import main_menu, post_list_keyboard, back_button

# States
WAIT_POST_TITLE, WAIT_POST_CONTENT, WAIT_POST_MEDIA, WAIT_PUBLISH_CHANNEL = range(4)


# ── Create Post ──────────────────────────────────────────────────────────────

async def cb_create_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📝 <b>Create Post</b>\n\nSend me a <b>title</b> for your post (or /skip to skip).",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    ctx.user_data["new_post"] = {}
    return WAIT_POST_TITLE


async def recv_post_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new_post"]["title"] = update.message.text.strip()
    await update.message.reply_text(
        "✏️ Now send me the <b>post content / text</b>.",
        parse_mode="HTML"
    )
    return WAIT_POST_CONTENT


async def skip_post_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new_post"]["title"] = None
    await update.message.reply_text("✏️ Send me the <b>post content / text</b>.", parse_mode="HTML")
    return WAIT_POST_CONTENT


async def recv_post_content(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new_post"]["content"] = update.message.text.strip()
    await update.message.reply_text(
        "🖼 Optionally attach a <b>photo, video, or document</b>, or /skip to save as text only.",
        parse_mode="HTML"
    )
    return WAIT_POST_MEDIA


async def recv_post_media(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    post = ctx.user_data["new_post"]

    if msg.photo:
        post["media_file_id"] = msg.photo[-1].file_id
        post["media_type"]    = "photo"
    elif msg.video:
        post["media_file_id"] = msg.video.file_id
        post["media_type"]    = "video"
    elif msg.document:
        post["media_file_id"] = msg.document.file_id
        post["media_type"]    = "document"

    return await _save_post_and_offer(update, ctx)


async def skip_post_media(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    return await _save_post_and_offer(update, ctx)


async def _save_post_and_offer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    post     = ctx.user_data.get("new_post", {})
    user_id  = update.effective_user.id
    title    = post.get("title")
    content  = post.get("content", "")
    mfid     = post.get("media_file_id")
    mtype    = post.get("media_type")

    post_id = db.save_post(user_id, title, content, mfid, mtype)
    db.log_event(user_id, "post_created", f"Post '{title or 'Untitled'}' saved as draft", post_id=post_id)

    channels = db.get_channels(user_id)

    keyboard = []
    for ch in channels:
        keyboard.append([InlineKeyboardButton(
            f"📢 Publish to {ch['channel_name'] or ch['channel_id']}",
            callback_data=f"publish:{post_id}:{ch['channel_id']}"
        )])
    keyboard.append([InlineKeyboardButton("💾 Save as Draft", callback_data="main_menu")])

    await update.message.reply_text(
        f"✅ Post saved (ID #{post_id})!\n\nPublish now or save as draft:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


# ── Publish immediately ──────────────────────────────────────────────────────

async def cb_publish_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, post_id, channel_id = q.data.split(":", 2)
    post_id = int(post_id)
    user_id = q.from_user.id

    post = db.get_post(post_id)
    if not post:
        await q.edit_message_text("❌ Post not found.", reply_markup=main_menu())
        return

    try:
        if post["media_file_id"] and post["media_type"] == "photo":
            await ctx.bot.send_photo(chat_id=channel_id, photo=post["media_file_id"],
                                     caption=post["content"])
        elif post["media_file_id"] and post["media_type"] == "video":
            await ctx.bot.send_video(chat_id=channel_id, video=post["media_file_id"],
                                     caption=post["content"])
        elif post["media_file_id"] and post["media_type"] == "document":
            await ctx.bot.send_document(chat_id=channel_id, document=post["media_file_id"],
                                        caption=post["content"])
        else:
            await ctx.bot.send_message(chat_id=channel_id, text=post["content"])

        db.log_event(user_id, "post_published",
                     f"Post #{post_id} published to {channel_id}",
                     channel_id=channel_id, post_id=post_id)
        await q.edit_message_text("✅ Post published!", reply_markup=main_menu())

    except Exception as e:
        await q.edit_message_text(
            f"❌ Failed to publish:\n<code>{e}</code>",
            parse_mode="HTML", reply_markup=main_menu()
        )


# ── My Posts (Draft Manager) ─────────────────────────────────────────────────

async def cb_my_posts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    posts   = db.get_posts(user_id)

    if not posts:
        await q.edit_message_text("📂 You have no posts yet.",
                                  reply_markup=back_button())
        return

    await q.edit_message_text(
        "📂 <b>My Posts</b>\n\nSelect a post to view or delete:",
        parse_mode="HTML",
        reply_markup=post_list_keyboard(posts, "view_post")
    )


async def cb_view_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    post_id = int(q.data.split(":")[1])
    post    = db.get_post(post_id)
    user_id = q.from_user.id

    if not post or post["user_id"] != user_id:
        await q.edit_message_text("❌ Post not found.", reply_markup=back_button("my_posts"))
        return

    text = (
        f"📄 <b>{post['title'] or 'Untitled'}</b>\n\n"
        f"{post['content'] or ''}\n\n"
        f"<i>Status: {post['status']} | Created: {post['created_at']}</i>"
    )

    channels  = db.get_channels(user_id)
    kbd_rows  = [
        [InlineKeyboardButton(
            f"📢 Publish to {ch['channel_name'] or ch['channel_id']}",
            callback_data=f"publish:{post_id}:{ch['channel_id']}"
        )]
        for ch in channels
    ]
    kbd_rows.append([
        InlineKeyboardButton("🗑 Delete", callback_data=f"delete_post:{post_id}"),
        InlineKeyboardButton("« Back",  callback_data="my_posts"),
    ])

    await q.edit_message_text(text, parse_mode="HTML",
                              reply_markup=InlineKeyboardMarkup(kbd_rows))


async def cb_delete_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    post_id = int(q.data.split(":")[1])
    user_id = q.from_user.id
    db.delete_post(post_id, user_id)
    db.log_event(user_id, "post_deleted", f"Post #{post_id} deleted", post_id=post_id)
    await q.edit_message_text("🗑 Post deleted.", reply_markup=back_button("my_posts"))


# ── Conversation handler ─────────────────────────────────────────────────────

def create_post_conv():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_create_post, pattern="^create_post$")],
        states={
            WAIT_POST_TITLE: [
                CommandHandler("skip", skip_post_title),
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_post_title),
            ],
            WAIT_POST_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_post_content),
            ],
            WAIT_POST_MEDIA: [
                CommandHandler("skip", skip_post_media),
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, recv_post_media),
                MessageHandler(filters.TEXT & ~filters.COMMAND, skip_post_media),
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_message=False
    )
