import uuid
import aiosqlite
from datetime import datetime, timedelta
from config import DB_PATH


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
    return txn


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
               FROM transactions
               WHERE date>=?
               GROUP BY type, category
               ORDER BY total DESC""",
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
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]