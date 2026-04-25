import re
from datetime import datetime, timedelta
from config import (
    INCOME_KEYWORDS, EXPENSE_KEYWORDS, CATEGORY_KEYWORDS,
    IMPLICIT_EXPENSE_KEYWORDS, IMPLICIT_INCOME_KEYWORDS,
)


def parse(text: str) -> dict:
    text_lower = text.lower().strip()

    if is_undo(text_lower):
        return {"intent": "undo"}

    if is_query(text_lower):
        return {"intent": "query", "period": detect_period(text_lower)}

    amount = extract_amount(text_lower)
    if not amount:
        return {"intent": "unclear", "reason": "no_amount"}

    type_ = detect_type(text_lower)
    if not type_:
        return {"intent": "unclear", "reason": "no_type", "amount": amount, "date": detect_date(text_lower), "note": extract_note(text)}

    category = detect_category(text_lower, type_)
    date     = detect_date(text_lower)
    note     = extract_note(text)

    return {
        "intent":   "transaction",
        "amount":   amount,
        "type":     type_,
        "category": category,
        "date":     date,
        "note":     note,
    }


def extract_amount(text: str) -> float | None:
    patterns = [
        (r"(\d+[\.,]?\d*)\s*млн",   1_000_000),
        (r"(\d+[\.,]?\d*)\s*miln",  1_000_000),
        (r"(\d+[\.,]?\d*)\s*[мm]",  1_000_000),
        (r"(\d+[\.,]?\d*)\s*тыс",   1_000),
        (r"(\d+[\.,]?\d*)\s*ming",  1_000),
        (r"(\d+[\.,]?\d*)\s*[кk]",  1_000),
        (r"(\d[\d\s_]*\d|\d{5,})",  1),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1).replace(",", ".").replace(" ", "").replace("_", "")
            try:
                return float(raw) * multiplier
            except ValueError:
                continue
    return None


def detect_type(text: str) -> str | None:
    for kw in INCOME_KEYWORDS:
        if kw in text:
            return "income"
    for kw in EXPENSE_KEYWORDS:
        if kw in text:
            return "expense"
    for kw in IMPLICIT_EXPENSE_KEYWORDS:
        if kw in text:
            return "expense"
    for kw in IMPLICIT_INCOME_KEYWORDS:
        if kw in text:
            return "income"
    return None


def detect_category(text: str, type_: str) -> str:
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return "Прочие доходы" if type_ == "income" else "Прочие расходы"


def detect_date(text: str) -> str:
    today = datetime.now().date()

    if "сегодня" in text or "bugun" in text:
        return today.isoformat()
    if "вчера" in text or "kecha" in text:
        return (today - timedelta(days=1)).isoformat()
    if "позавчера" in text:
        return (today - timedelta(days=2)).isoformat()

    clean = re.sub(r"\d+[\.,]\d*\s*(млн|тыс|миллион|[мкmk])\b", "", text)
    match = re.search(r"\b(\d{1,2})[./\-](\d{1,2})(?:[./\-](\d{2,4}))?\b", clean)
    if match:
        day   = int(match.group(1))
        month = int(match.group(2))
        year  = int(match.group(3)) if match.group(3) else today.year
        if year < 100:
            year += 2000
        if 1 <= day <= 31 and 1 <= month <= 12:
            try:
                return datetime(year, month, day).date().isoformat()
            except ValueError:
                pass

    return today.isoformat()


def is_query(text: str) -> bool:
    keywords = [
        "сколько", "отчёт", "отчет", "итог", "итоги",
        "сводка", "статистика", "доходы", "расходы",
        "баланс", "hisobot", "qancha",
    ]
    return any(kw in text for kw in keywords)


def detect_period(text: str) -> str:
    if "сегодня" in text or "bugun" in text:
        return "today"
    if "неделю" in text or "неделя" in text or "hafta" in text:
        return "week"
    return "month"

def is_undo(text: str) -> bool:
    keywords = [
        "отмени", "отменить", "удали", "удалить",
        "undo", "назад", "не то", "bekor",
    ]
    return any(kw in text for kw in keywords)


def extract_note(text: str) -> str:
    return text.strip()[:100]