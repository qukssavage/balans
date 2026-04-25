import uuid
import aiosqlite
from fastapi import APIRouter, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/transactions", tags=["transactions"])

DB_PATH = "../bot/balans.db"


class TransactionIn(BaseModel):
    amount:     float
    type:       str
    category:   str
    date:       str
    note:       Optional[str] = ""


@router.get("")
async def get_transactions(
    type:     Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    from_date:Optional[str] = Query(None),
    to_date:  Optional[str] = Query(None),
    limit:    int = Query(100),
):
    query  = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if type:
        query += " AND type=?"
        params.append(type)
    if category:
        query += " AND category=?"
        params.append(category)
    if from_date:
        query += " AND date>=?"
        params.append(from_date)
    if to_date:
        query += " AND date<=?"
        params.append(to_date)

    query += " ORDER BY date DESC, created_at DESC LIMIT ?"
    params.append(limit)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows   = await cursor.fetchall()

    return [dict(r) for r in rows]


@router.post("")
async def add_transaction(txn: TransactionIn):
    txn_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO transactions
               (id, user_id, username, amount, type, category, date, note, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (txn_id, 0, "dashboard", txn.amount, txn.type,
             txn.category, txn.date, txn.note, datetime.now().isoformat()),
        )
        await db.commit()
    return {"id": txn_id, **txn.dict()}


@router.delete("/{txn_id}")
async def delete_transaction(txn_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
        await db.commit()
    return {"deleted": txn_id}


@router.put("/{txn_id}")
async def update_transaction(txn_id: str, txn: TransactionIn):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE transactions
               SET amount=?, type=?, category=?, date=?, note=?
               WHERE id=?""",
            (txn.amount, txn.type, txn.category, txn.date, txn.note, txn_id),
        )
        await db.commit()
    return {"id": txn_id, **txn.dict()}