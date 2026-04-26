import logging
import traceback
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, TypeHandler
)
from config import TELEGRAM_BOT_TOKEN
from database import init_db
from handlers.commands import cmd_start, cmd_report, cmd_undo, cmd_help, cmd_language, cmd_budget, cmd_reset
from handlers.text_handler import handle_text, handle_callback
from scheduler import send_daily_report
import datetime

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)


async def post_init(application):
    await init_db()

    # Ежедневный отчёт в 18:00 по Ташкенту (13:00 UTC)
    application.job_queue.run_daily(
        callback=lambda ctx: send_daily_report(ctx.bot),
        time=datetime.time(hour=13, minute=0, tzinfo=datetime.timezone.utc),
        name="daily_report",
    )
    logging.info("Ежедневный отчёт запланирован на 18:00 (Ташкент)")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Ошибка:", exc_info=context.error)
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("report",   cmd_report))
    app.add_handler(CommandHandler("undo",     cmd_undo))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("language", cmd_language))
    app.add_handler(CommandHandler("budget",   cmd_budget))
    app.add_handler(CommandHandler("reset",    cmd_reset))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    logging.info("Бот запущен.")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()
