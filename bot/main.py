import logging
import traceback
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, TypeHandler
)
from config import TELEGRAM_BOT_TOKEN
from database import init_db
from handlers.commands import cmd_start, cmd_report, cmd_undo, cmd_help
from handlers.text_handler import handle_text, handle_callback

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)


async def post_init(application):
    await init_db()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Ошибка:", exc_info=context.error)
    traceback.print_exception(type(context.error), context.error, context.error.traceback)


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("undo",   cmd_undo))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    logging.info("Бот запущен.")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,  # явно получаем все типы включая callback
    )


if __name__ == "__main__":
    main()