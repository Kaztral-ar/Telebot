from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")],
        [InlineKeyboardButton("📝 Create Post", callback_data="create_post")],
        [InlineKeyboardButton("📂 My Posts", callback_data="my_posts")],
        [InlineKeyboardButton("📤 Multipost", callback_data="multipost")],
        [InlineKeyboardButton("⏰ Schedule Post", callback_data="schedule_post")],
        [InlineKeyboardButton("🗑 Delete Scheduled", callback_data="delete_scheduled")],
        [InlineKeyboardButton("📊 Event Log", callback_data="event_log")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")],
        [InlineKeyboardButton("❌ Exit", callback_data="exit")],
    ]
    return InlineKeyboardMarkup(rows)


def back_button(target: str = "main_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« Back", callback_data=target)]
    ])


def post_list_keyboard(posts, prefix: str) -> InlineKeyboardMarkup:
    rows = []
    for post in posts:
        title = (post["title"] or post["content"] or "Untitled").strip()
        label = title[:32] + "…" if len(title) > 32 else title
        rows.append([
            InlineKeyboardButton(f"📝 #{post['id']} {label}", callback_data=f"{prefix}:{post['id']}")
        ])
    rows.append([InlineKeyboardButton("« Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def channel_list_keyboard(channels, prefix: str = "channel") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            f"📢 {ch['channel_name'] or ch['channel_id']}",
            callback_data=f"{prefix}:{ch['channel_id']}"
        )]
        for ch in channels
    ]
    rows.append([InlineKeyboardButton("« Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def scheduled_list_keyboard(scheduled_posts) -> InlineKeyboardMarkup:
    rows = []
    for item in scheduled_posts:
        when = str(item["scheduled_time"])[:16]
        name = item["channel_name"] or item["channel_id"]
        rows.append([
            InlineKeyboardButton(
                f"🗑 #{item['id']} {when} → {name}",
                callback_data=f"del_sched:{item['id']}"
            )
        ])
    rows.append([InlineKeyboardButton("« Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)
