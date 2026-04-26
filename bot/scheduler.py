import logging
from datetime import datetime
from telegram import Bot
from database import get_summary, get_recent
from reports import fmt_money, translate_category
from lang import t
import aiosqlite
from config import DB_PATH

log = logging.getLogger(__name__)

MONTHS_RU = {1:"января",2:"февраля",3:"марта",4:"апреля",5:"мая",6:"июня",7:"июля",8:"августа",9:"сентября",10:"октября",11:"ноября",12:"декабря"}
MONTHS_UZ = {1:"yanvar",2:"fevral",3:"mart",4:"aprel",5:"may",6:"iyun",7:"iyul",8:"avgust",9:"sentabr",10:"oktabr",11:"noyabr",12:"dekabr"}


def today_str(lang: str) -> str:
    d = datetime.now()
    if lang == "uz":
        return f"{d.day} {MONTHS_UZ[d.month]}"
    return f"{d.day} {MONTHS_RU[d.month]}"


async def get_all_users() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT user_id, lang FROM users")
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def send_daily_report(bot: Bot):
    users = await get_all_users()
    if not users:
        log.info("Нет пользователей для отчёта")
        return

    data   = await get_summary(period="today")
    recent = await get_recent(limit=3)

    total_inc = sum(v["total"] for v in data["income"].values())
    total_exp = sum(v["total"] for v in data["expense"].values())
    net = total_inc - total_exp

    for user in users:
        lang = user.get("lang", "ru")
        today = today_str(lang)
        try:
            if lang == "uz":
                header  = f"📊 *Kunlik hisobot — {today}*"
                no_data = "_Bugun hech qanday tranzaksiya yo'q._"
                last_label = "*Oxirgi yozuvlar:*"
                top_label  = "Topdan xarajat"
            else:
                header  = f"📊 *Итоги дня — {today}*"
                no_data = "_Сегодня транзакций не было._"
                last_label = "*Последние записи:*"
                top_label  = "Топ расход"

            if total_inc == 0 and total_exp == 0:
                await bot.send_message(
                    chat_id=user["user_id"],
                    text=f"{header}\n\n{no_data}",
                    parse_mode="Markdown",
                )
                continue

            net_emoji = "📈" if net >= 0 else "📉"
            lines = [
                header, "",
                f"💰 {t(lang, 'income_label')}: *{fmt_money(total_inc, lang)}*",
                f"💸 {t(lang, 'expense_label')}: *{fmt_money(total_exp, lang)}*",
                f"{net_emoji} {t(lang, 'profit_label')}: *{fmt_money(net, lang)}*",
            ]

            if data["expense"]:
                top_exp  = max(data["expense"].items(), key=lambda x: x[1]["total"])
                cat_name = translate_category(top_exp[0], lang)
                lines.append(f"\n🔺 {top_label}: {cat_name} — {fmt_money(top_exp[1]['total'], lang)}")

            if recent:
                lines.append(f"\n{last_label}")
                for r in recent:
                    sign = "+" if r["type"] == "income" else "−"
                    cat  = translate_category(r["category"], lang)
                    lines.append(f"  · {cat} {sign}{fmt_money(r['amount'], lang)}")

            await bot.send_message(
                chat_id=user["user_id"],
                text="\n".join(lines),
                parse_mode="Markdown",
            )
            log.info(f"Отчёт отправлен {user['user_id']}")

        except Exception as e:
            log.warning(f"Ошибка отправки {user['user_id']}: {e}")
