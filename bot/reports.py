from datetime import datetime
from lang import t, translate_category

MONTHS_RU = {
    1:"января", 2:"февраля", 3:"марта", 4:"апреля",
    5:"мая", 6:"июня", 7:"июля", 8:"августа",
    9:"сентября", 10:"октября", 11:"ноября", 12:"декабря",
}
MONTHS_UZ = {
    1:"yanvar", 2:"fevral", 3:"mart", 4:"aprel",
    5:"may", 6:"iyun", 7:"iyul", 8:"avgust",
    9:"sentabr", 10:"oktabr", 11:"noyabr", 12:"dekabr",
}


def fmt_date(date_str: str, lang: str = "ru") -> str:
    d = datetime.fromisoformat(date_str)
    months = MONTHS_UZ if lang == "uz" else MONTHS_RU
    return f"{d.day} {months[d.month]} {d.year}"


def fmt_money(amount: float, lang: str = "ru") -> str:
    amount = round(amount)
    if lang == "uz":
        if abs(amount) >= 1_000_000_000:
            return f"{amount/1_000_000_000:.1f} mlrd so'm"
        if abs(amount) >= 1_000_000:
            return f"{amount/1_000_000:.1f} mln so'm"
        if abs(amount) >= 1_000:
            return f"{amount/1_000:.0f} ming so'm"
        return f"{amount:,} so'm"
    else:
        if abs(amount) >= 1_000_000_000:
            return f"{amount/1_000_000_000:.1f} млрд сум"
        if abs(amount) >= 1_000_000:
            return f"{amount/1_000_000:.1f} млн сум"
        if abs(amount) >= 1_000:
            return f"{amount/1_000:.0f} тыс сум"
        return f"{amount:,} сум"


def confirm_transaction(txn: dict, lang: str = "ru") -> str:
    if txn["type"] == "income":
        label = t(lang, "income_recorded")
        sign  = t(lang, "sign_income")
    else:
        label = t(lang, "expense_recorded")
        sign  = t(lang, "sign_expense")

    lines = [
        f"*{label}*",
        "",
        f"*{sign}{fmt_money(txn['amount'], lang)}*",
        f"📁 {translate_category(txn['category'], lang)}",
        f"📅 {fmt_date(txn['date'], lang)}",
    ]
    if txn.get("note"):
        lines.append(f"💬 _{txn['note']}_")
    if txn.get("username"):
        lines.append(f"👤 {txn['username']}")
    lines += ["", t(lang, "cancel_hint")]
    return "\n".join(lines)


def format_summary(data: dict, lang: str = "ru") -> str:
    period_key = {
        "today": "period_today",
        "week":  "period_week",
        "month": "period_month",
    }.get(data["period"], "period_month")
    period = t(lang, period_key)

    total_inc = sum(v["total"] for v in data["income"].values())
    total_exp = sum(v["total"] for v in data["expense"].values())
    net       = total_inc - total_exp
    net_emoji = "📈" if net >= 0 else "📉"
    pieces    = t(lang, "pieces")

    lines = [
        f"📊 *{period}*",
        "",
        f"💰 {t(lang, 'income_label')}: *{fmt_money(total_inc, lang)}*",
        f"💸 {t(lang, 'expense_label')}: *{fmt_money(total_exp, lang)}*",
        f"{net_emoji} {t(lang, 'profit_label')}: *{fmt_money(net, lang)}*",
    ]

    if data["income"]:
        lines.append(f"\n*{t(lang, 'income_cats')}*")
        for cat, d in sorted(data["income"].items(), key=lambda x: -x[1]["total"]):
            lines.append(f"  · {translate_category(cat, lang)} — {fmt_money(d['total'], lang)} ({d['count']} {pieces})")

    if data["expense"]:
        lines.append(f"\n*{t(lang, 'expense_cats')}*")
        for cat, d in sorted(data["expense"].items(), key=lambda x: -x[1]["total"]):
            lines.append(f"  · {translate_category(cat, lang)} — {fmt_money(d['total'], lang)} ({d['count']} {pieces})")

    if not data["income"] and not data["expense"]:
        lines.append(f"\n_{t(lang, 'no_data')}_")

    return "\n".join(lines)


def format_undo(txn: dict, lang: str = "ru") -> str:
    return (
        f"{t(lang, 'undo_done')}\n\n"
        f"{translate_category(txn['category'], lang)} — {fmt_money(txn['amount'], lang)}\n"
        f"_{fmt_date(txn['date'], lang)}_"
    )


def format_unclear(reason: str, lang: str = "ru") -> str:
    if reason == "no_amount":
        return t(lang, "no_amount")
    if reason == "no_type":
        return t(lang, "no_type")
    return t(lang, "unknown")