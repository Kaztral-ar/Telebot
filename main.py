import asyncio
import logging

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler
)

import database as db
import scheduler as sched
from config import BOT_TOKEN

from handlers.start    import cmd_start, cb_main_menu, cb_exit
from handlers.channel  import add_channel_conv
from handlers.posts    import (create_post_conv, cb_my_posts, cb_view_post,
                                cb_delete_post, cb_publish_post)
from handlers.multipost import multipost_conv
from handlers.schedule  import (schedule_conv, cb_delete_scheduled,
                                  cb_del_sched_confirm)
from handlers.logs      import cb_event_log, cb_clear_log
from handlers.settings  import (cb_settings, cb_toggle_notif, cb_set_timezone,
                                  cb_tz_pick, settings_tz_conv)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def build_app():
    db.init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # ── Commands ─────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", cmd_start))

    # ── Conversation handlers (must come before plain CallbackQueryHandlers) ─
    app.add_handler(add_channel_conv())
    app.add_handler(create_post_conv())
    app.add_handler(multipost_conv())
    app.add_handler(schedule_conv())
    app.add_handler(settings_tz_conv())

    # ── Plain callback handlers ───────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_main_menu,        pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(cb_exit,             pattern="^exit$"))

    # Posts
    app.add_handler(CallbackQueryHandler(cb_my_posts,         pattern="^my_posts$"))
    app.add_handler(CallbackQueryHandler(cb_view_post,        pattern="^view_post:"))
    app.add_handler(CallbackQueryHandler(cb_delete_post,      pattern="^delete_post:"))
    app.add_handler(CallbackQueryHandler(cb_publish_post,     pattern="^publish:"))

    # Schedule
    app.add_handler(CallbackQueryHandler(cb_delete_scheduled, pattern="^delete_scheduled$"))
    app.add_handler(CallbackQueryHandler(cb_del_sched_confirm,pattern="^del_sched:"))

    # Event log
    app.add_handler(CallbackQueryHandler(cb_event_log,        pattern="^event_log$"))
    app.add_handler(CallbackQueryHandler(cb_clear_log,        pattern="^clear_log$"))

    # Settings
    app.add_handler(CallbackQueryHandler(cb_settings,         pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(cb_toggle_notif,     pattern="^toggle_notif$"))
    app.add_handler(CallbackQueryHandler(cb_set_timezone,     pattern="^set_timezone$"))
    app.add_handler(CallbackQueryHandler(cb_tz_pick,          pattern="^tz:"))

    return app


async def main():
    app = build_app()

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("🤖 Telebot is running …")

        # Start background scheduler
        asyncio.create_task(sched.run_scheduler(app))

        # Run until interrupted
        await asyncio.Event().wait()

        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
