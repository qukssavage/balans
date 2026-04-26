import uuid
import aiohttp
import aiosqlite
from datetime import datetime, timedelta
from config import DB_PATH

API_URL = "https://balans-production.up.railway.app"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          TEXT PRIMARY KEY,
                user_id     INTEGER NOT NULL,
                username    TEXT,
                amount      REAL NOT NULL,
                type        TEXT NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                note        TEXT DEFAULT '',
                created_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                lang        TEXT DEFAULT 'ru',
                created_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS budgets (
                id          TEXT PRIMARY KEY,
                category    TEXT NOT NULL UNIQUE,
                monthly_limit REAL NOT NULL,
                created_at  TEXT NOT NULL
            );
        """)
        await db.commit()
    print("✅ База данных готова")


async def set_user_lang(user_id: int, username: str, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (user_id, username, lang, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang""",
            (user_id, username, lang, datetime.now().isoformat()),
        )
        await db.commit()


async def get_user_lang(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT lang FROM users WHERE user_id=?", (user_id,)
        )
        row = await cursor.fetchone()
    return row[0] if row else None


async def save_transaction(user_id, username, amount, type_, category, date, note=""):
    txn_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO transactions
               (id, user_id, username, amount, type, category, date, note, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (txn_id, user_id, username, amount, type_, category, date, note,
             datetime.now().isoformat()),
        )
        await db.commit()

    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{API_URL}/transactions",
                json={"id": txn_id, "amount": amount, "type": type_,
                      "category": category, "date": date, "note": note or "", "username": username},
                timeout=aiohttp.ClientTimeout(total=5),
            )
    except Exception as e:
        print(f"⚠️ API sync failed: {e}")

    return txn_id


async def delete_last_transaction(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        txn = dict(row)
        await db.execute("DELETE FROM transactions WHERE id=?", (txn["id"],))
        await db.commit()

    try:
        async with aiohttp.ClientSession() as session:
            await session.delete(
                f"{API_URL}/transactions/{txn['id']}",
                timeout=aiohttp.ClientTimeout(total=5),
            )
    except Exception as e:
        print(f"⚠️ API delete failed: {e}")

    return txn

async def delete_transactions_by_category(category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM transactions WHERE category=?", (category,))
        await db.commit()

async def delete_all_transactions():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM transactions")
        await db.commit()


async def get_summary(period="month"):
    if period == "today":
        since = datetime.now().date().isoformat()
    elif period == "week":
        since = (datetime.now() - timedelta(days=7)).date().isoformat()
    else:
        since = datetime.now().replace(day=1).date().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT type, category, SUM(amount) as total, COUNT(*) as cnt
               FROM transactions WHERE date>=?
               GROUP BY type, category ORDER BY total DESC""",
            (since,),
        )
        rows = await cursor.fetchall()

    result = {"income": {}, "expense": {}, "period": period}
    for row in rows:
        result[row[0]][row[1]] = {"total": row[2], "count": row[3]}
    return result


async def get_recent(limit=5):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ── Бюджеты ───────────────────────────────────────────────
async def set_budget(category: str, monthly_limit: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO budgets (id, category, monthly_limit, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit""",
            (str(uuid.uuid4()), category, monthly_limit, datetime.now().isoformat()),
        )
        await db.commit()


async def get_budgets() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM budgets")
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def check_budget_alerts(category: str, lang: str = "ru") -> str | None:
    """Проверяет бюджет категории и возвращает предупреждение если нужно"""
    since = datetime.now().replace(day=1).date().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем лимит
        cursor = await db.execute(
            "SELECT monthly_limit FROM budgets WHERE category=?", (category,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        limit = row[0]

        # Считаем потраченное
        cursor = await db.execute(
            """SELECT SUM(amount) FROM transactions
               WHERE type='expense' AND category=? AND date>=?""",
            (category, since),
        )
        row = await cursor.fetchone()
        spent = row[0] or 0

    pct = spent / limit * 100 if limit > 0 else 0

    if pct >= 100:
        if lang == "uz":
            return f"❌ *{category}* bo'yicha limit oshib ketdi!\nSarflandi: {spent/1e6:.1f}M — {(spent-limit)/1e6:.1f}M so'm ortiqcha"
        return f"❌ Превышен лимит! *{category}*\nПотрачено: {spent/1e6:.1f}M — превышение на {(spent-limit)/1e6:.1f}M сум"
    elif pct >= 80:
        if lang == "uz":
            return f"⚠️ Diqqat! *{category}* — {pct:.0f}% ishlatildi\n{spent/1e6:.1f}M / {limit/1e6:.1f}M so'm"
        return f"⚠️ Внимание! *{category}* использована на {pct:.0f}%\nПотрачено: {spent/1e6:.1f}M из {limit/1e6:.1f}M сум"

    return None

async def delete_budget(category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM budgets WHERE category=?", (category,))
        await db.commit()

async def delete_all_budgets():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM budgets")
        await db.commit()