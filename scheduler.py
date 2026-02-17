import asyncio
import logging
from datetime import datetime, timezone

import database as db

logger = logging.getLogger(__name__)


async def run_scheduler(app):
    """Background task: every 30 s check for due scheduled posts and send them."""
    while True:
        try:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            pending = db.get_pending_scheduled()

            for row in pending:
                sched_time = row["scheduled_time"]  # stored as "YYYY-MM-DD HH:MM"
                if sched_time <= now:
                    await _send_scheduled(app, row)

        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        await asyncio.sleep(30)


async def _send_scheduled(app, row):
    sched_id = row["id"]
    user_id  = row["user_id"]
    chan_id  = row["channel_id"]
    content  = row["content"] or ""
    mfid     = row["media_file_id"]
    mtype    = row["media_type"]

    try:
        if mfid and mtype == "photo":
            await app.bot.send_photo(chat_id=chan_id, photo=mfid, caption=content)
        elif mfid and mtype == "video":
            await app.bot.send_video(chat_id=chan_id, video=mfid, caption=content)
        elif mfid and mtype == "document":
            await app.bot.send_document(chat_id=chan_id, document=mfid, caption=content)
        else:
            await app.bot.send_message(chat_id=chan_id, text=content)

        db.mark_scheduled_sent(sched_id)
        db.log_event(user_id, "scheduled_sent",
                     f"Scheduled post sent to {row['channel_name'] or chan_id}",
                     channel_id=chan_id, post_id=row["post_id"])

        # Notify user
        await app.bot.send_message(
            chat_id=user_id,
            text=f"✅ Scheduled post sent to <b>{row['channel_name'] or chan_id}</b>",
            parse_mode="HTML"
        )

    except Exception as e:
        db.mark_scheduled_failed(sched_id)
        db.log_event(user_id, "scheduled_failed",
                     f"Failed to send scheduled post: {e}",
                     channel_id=chan_id)
        logger.error(f"Failed to send scheduled post {sched_id}: {e}")
        try:
            await app.bot.send_message(
                chat_id=user_id,
                text=f"❌ Failed to send scheduled post to <b>{row['channel_name'] or chan_id}</b>\n<code>{e}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass
