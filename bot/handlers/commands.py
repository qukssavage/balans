from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_summary, delete_last_transaction, get_user_lang, set_user_lang
from reports import format_summary, format_undo
from lang import t


def get_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(lang, "btn_month"), t(lang, "btn_week")],
            [t(lang, "btn_budget")], [t(lang, "btn_undo")],
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
        # Первый раз — спрашиваем язык
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

async def cmd_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущие бюджеты или установить новый"""
    from database import get_budgets, get_summary
    user = update.effective_user
    lang = await get_user_lang(user.id) or "ru"

    budgets = await get_budgets()
    data    = await get_summary(period="month")

    if not budgets:
        if lang == "uz":
            text = (
                "🎯 *Byudjet limitlari*\n\n"
                "Hali hech qanday limit o'rnatilmagan.\n\n"
                "Limit o'rnatish uchun yozing:\n"
                "_«Ijara limiti 10 mln»_\n"
                "_«Maosh limiti 20 mln»_"
            )
        else:
            text = (
                "🎯 *Бюджетные лимиты*\n\n"
                "Лимиты ещё не установлены.\n\n"
                "Чтобы установить лимит, напишите:\n"
                "_«Лимит аренда 10 млн»_\n"
                "_«Лимит зарплата 20 млн»_"
            )
        await update.message.reply_text(text, parse_mode="Markdown")
        return

    lines = ["🎯 *Бюджетные лимиты*\n" if lang == "ru" else "🎯 *Byudjet limitlari*\n"]
    for b in budgets:
        spent = data["expense"].get(b["category"], {}).get("total", 0)
        pct   = spent / b["monthly_limit"] * 100 if b["monthly_limit"] > 0 else 0
        filled = min(int(pct // 10), 10)
        if pct >= 100:
            bar = "🟥" * 10
        elif pct >=80:
            bar = "🟧" * filled + "⬜️" * (10 - filled)
        else:
            bar = "🟩" * filled + "⬜️" * (10 - filled)
        status = "❌" if pct >= 100 else "⚠️" if pct >= 80 else "✅"
        lines.append(
            f"{status} *{b['category']}*\n"
            f"{bar} {pct:.0f}%\n"
            f"{spent/1e6:.1f}M / {b['monthly_limit']/1e6:.1f}M сум\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_lang(user.id) or "ru"
    
    from database import delete_all_budgets, delete_all_transactions
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗑 Все транзакции", callback_data="reset:transactions"),
            InlineKeyboardButton("🎯 Все бюджеты",   callback_data="reset:budgets"),
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="reset:cancel")],
    ])
    
    await update.message.reply_text(
        "⚠️ *Что хотите сбросить?*\n\n_Это действие нельзя отменить._",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )