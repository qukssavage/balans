from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from parser import parse
from database import save_transaction, get_summary, delete_last_transaction, get_user_lang, set_user_lang
from reports import confirm_transaction, format_summary, format_undo, format_unclear
from handlers.commands import get_keyboard, lang_keyboard
from config import CATEGORIES
from lang import t


def make_category_keyboard(type_: str, lang: str) -> InlineKeyboardMarkup:
    cats = CATEGORIES[type_]
    rows = []
    for i in range(0, len(cats), 2):
        row = [InlineKeyboardButton(cats[i], callback_data=f"cat:{type_}:{cats[i]}")]
        if i + 1 < len(cats):
            row.append(InlineKeyboardButton(cats[i+1], callback_data=f"cat:{type_}:{cats[i+1]}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def make_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t(lang, "btn_income"),  callback_data="type:income"),
        InlineKeyboardButton(t(lang, "btn_expense"), callback_data="type:expense"),
    ]])


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    lang = await get_user_lang(user.id) or "ru"

    # Кнопки главного меню (на обоих языках)
    if text in ("📊 Отчёт за месяц", "📊 Oylik hisobot"):
        data = await get_summary(period="month")
        return await update.message.reply_text(format_summary(data, lang), parse_mode="Markdown")
    if text in ("📅 Отчёт за неделю", "📅 Haftalik hisobot"):
        data = await get_summary(period="week")
        return await update.message.reply_text(format_summary(data, lang), parse_mode="Markdown")
    if text in ("↩️ Отменить последнее", "↩️ Oxirgini bekor qilish"):
        deleted = await delete_last_transaction(user.id)
        if deleted:
            return await update.message.reply_text(format_undo(deleted, lang), parse_mode="Markdown")
        return await update.message.reply_text(t(lang, "nothing_to_undo"))

    result = parse(text)
    intent = result["intent"]

    if intent == "transaction":
        if result["category"] in ("Прочие доходы", "Прочие расходы"):
            context.user_data["pending"] = result
            await update.message.reply_text(
                f"{t(lang, 'ask_category')}\n\nСумма: *{result['amount']:,.0f} сум*",
                parse_mode="Markdown",
                reply_markup=make_category_keyboard(result["type"], lang),
            )
            return
        await _save_and_confirm(update, context, result, lang)

    elif intent == "query":
        data = await get_summary(period=result["period"])
        await update.message.reply_text(format_summary(data, lang), parse_mode="Markdown")

    elif intent == "undo":
        deleted = await delete_last_transaction(user.id)
        if deleted:
            await update.message.reply_text(format_undo(deleted, lang), parse_mode="Markdown")
        else:
            await update.message.reply_text(t(lang, "nothing_to_undo"))

    elif intent == "budget":
        from database import set_budget
        if result.get("amount") and result.get("category") not in ("Прочие расходы", "Прочие доходы"):
            await set_budget(result["category"], result["amount"])
            cat = result["category"]
            amt = result["amount"]
            if lang == "uz":
                msg = f"🎯 *{cat}* uchun limit o'rnatildi: {amt/1e6:.1f}M so'm/oy"
            else:
                msg = f"🎯 Лимит установлен для *{cat}*: {amt/1e6:.1f}M сум/месяц"
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("Укажите категорию и сумму. Например: _Лимит аренда 10 млн_", parse_mode="Markdown")

    else:
        reason = result.get("reason", "")
        if reason == "no_type" and "amount" in result:
            context.user_data["pending"] = result
            await update.message.reply_text(
                f"*{result['amount']:,.0f} сум* — {t(lang, 'ask_type')}",
                parse_mode="Markdown",
                reply_markup=make_type_keyboard(lang),
            )
        else:
            await update.message.reply_text(format_unclear(reason, lang), parse_mode="Markdown")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data
    user  = update.effective_user
    lang  = await get_user_lang(user.id) or "ru"

    # Выбор языка
    if data.startswith("lang:"):
        chosen_lang = data.split(":")[1]
        await set_user_lang(user.id, user.username or user.first_name, chosen_lang)
        await query.edit_message_text(t(chosen_lang, "lang_set"))
        await update.effective_message.reply_text(
            t(chosen_lang, "start_msg"),
            parse_mode="Markdown",
            reply_markup=get_keyboard(chosen_lang),
        )
        return

    # Выбор типа
    if data.startswith("type:"):
        type_   = data.split(":")[1]
        pending = context.user_data.get("pending", {})
        pending["type"] = type_
        context.user_data["pending"] = pending
        await query.edit_message_text(
            f"{t(lang, 'ask_category')}\n\nСумма: *{pending.get('amount', 0):,.0f} сум*",
            parse_mode="Markdown",
            reply_markup=make_category_keyboard(type_, lang),
        )
        return

    # Выбор категории
    if data.startswith("cat:"):
        _, type_, category = data.split(":", 2)
        pending = context.user_data.pop("pending", None)
        if not pending:
            await query.edit_message_text("Что-то пошло не так. Напиши заново.")
            return
        pending["type"]     = type_
        pending["category"] = category
        txn_id = await save_transaction(
            user_id  = user.id,
            username = user.username or user.first_name,
            amount   = pending["amount"],
            type_    = pending["type"],
            category = pending["category"],
            date     = pending["date"],
            note     = pending.get("note", ""),
        )
        txn = {**pending, "id": txn_id, "username": user.username or user.first_name}
        await query.edit_message_text(confirm_transaction(txn, lang), parse_mode="Markdown")


async def _save_and_confirm(update, context, result, lang):
    user   = update.effective_user
    txn_id = await save_transaction(
        user_id  = user.id,
        username = user.username or user.first_name,
        amount   = result["amount"],
        type_    = result["type"],
        category = result["category"],
        date     = result["date"],
        note     = result.get("note", ""),
    )
    txn = {**result, "id": txn_id, "username": user.username or user.first_name}
    await update.message.reply_text(
        confirm_transaction(txn, lang),
        parse_mode="Markdown",
        reply_markup=get_keyboard(lang),
    )
    # Проверяем бюджет если это расход
    if result["type"] == "expense":
        from database import check_budget_alerts
        alert = await check_budget_alerts(result["category"], lang)
        if alert:
            await update.message.reply_text(alert, parse_mode="Markdown")
