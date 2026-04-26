import aiosqlite
from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter(prefix="/summary", tags=["summary"])

DB_PATH = "/data/balans.db"


@router.get("/month")
async def monthly_summary():
    months = []
    for i in range(5, -1, -1):
        d = datetime.now()
        d = d.replace(day=1)
        month = (d.month - i - 1) % 12 + 1
        year  = d.year - ((d.month - i - 1) // 12)
        since = f"{year}-{month:02d}-01"
        if month == 12:
            until = f"{year+1}-01-01"
        else:
            until = f"{year}-{month+1:02d}-01"

        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    """SELECT type, SUM(amount) FROM transactions
                       WHERE date>=? AND date<? GROUP BY type""",
                    (since, until),
                )
                rows = await cursor.fetchall()
        except:
            rows = []

        income = expense = 0
        for row in rows:
            if row[0] == "income": income = row[1] or 0
            else: expense = row[1] or 0

        months.append({
            "month":   f"{year}-{month:02d}",
            "label":   datetime(year, month, 1).strftime("%b"),
            "income":  income,
            "expense": expense,
            "net":     income - expense,
        })
    return months


@router.get("/categories")
async def categories_summary():
    since = datetime.now().replace(day=1).date().isoformat()
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                """SELECT type, category, SUM(amount) as total, COUNT(*) as cnt
                   FROM transactions WHERE date>=?
                   GROUP BY type, category ORDER BY total DESC""",
                (since,),
            )
            rows = await cursor.fetchall()
        return [{"type": r[0], "category": r[1], "total": r[2], "count": r[3]} for r in rows]
    except:
        return []


@router.get("/kpi")
async def kpi():
    cm = datetime.now().replace(day=1).date().isoformat()
    pm_date = datetime.now().replace(day=1) - timedelta(days=1)
    pm = pm_date.replace(day=1).date().isoformat()
    pm_end = cm

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async def period_agg(since, until):
                cursor = await db.execute(
                    """SELECT type, SUM(amount) FROM transactions
                       WHERE date>=? AND date<? GROUP BY type""",
                    (since, until),
                )
                rows = await cursor.fetchall()
                inc = exp = 0
                for r in rows:
                    if r[0] == "income": inc = r[1] or 0
                    else: exp = r[1] or 0
                return inc, exp

            this_inc, this_exp = await period_agg(cm, "9999-12-31")
            prev_inc, prev_exp = await period_agg(pm, pm_end)

            cursor = await db.execute(
                "SELECT COUNT(*) FROM transactions WHERE date>=?", (cm,)
            )
            txn_count = (await cursor.fetchone())[0]
    except:
        this_inc = this_exp = prev_inc = prev_exp = txn_count = 0

    return {
        "this_month": {"income": this_inc, "expense": this_exp, "net": this_inc - this_exp},
        "prev_month": {"income": prev_inc, "expense": prev_exp, "net": prev_inc - prev_exp},
        "txn_count":  txn_count,
    }
