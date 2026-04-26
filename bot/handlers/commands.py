from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_summary, delete_last_transaction, get_user_lang, set_user_lang
from reports import format_summary, format_undo
from lang import t


def get_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(lang, "btn_month"), t(lang, "btn_week")],
            [t(lang, "btn_undo")],
        ],
        resize_keyboard=True,
    )


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton("🇺🇿 O'zbek",  callback_data="lang:uz"),
    ]])


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_lang(user.id)

    if not lang:
        await update.message.reply_text(
            "👋 Tilni tanlang / Выберите язык:",
            reply_markup=lang_keyboard(),
        )
        return

    await update.message.reply_text(
        t(lang, "start_msg"),
        parse_mode="Markdown",
        reply_markup=get_keyboard(lang),
    )


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_lang(user.id) or "ru"
    data = await get_summary(period="month")
    await update.message.reply_text(
        format_summary(data, lang),
        parse_mode="Markdown",
    )


async def cmd_undo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_lang(user.id) or "ru"
    deleted = await delete_last_transaction(user.id)
    if deleted:
        await update.message.reply_text(
            format_undo(deleted, lang),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(t(lang, "nothing_to_undo"))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_lang(user.id) or "ru"
    await update.message.reply_text(
        t(lang, "help_msg"),
        parse_mode="Markdown",
        reply_markup=get_keyboard(lang),
    )

async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 Tilni tanlang / Выберите язык:",
        reply_markup=lang_keyboard(),
    )