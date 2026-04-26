import aiosqlite
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import transactions, summary

DB_PATH = "/data/balans.db"

app = FastAPI(title="Balans API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router)
app.include_router(summary.router)


@app.on_event("startup")
async def startup():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
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
            )
        """)
        await db.commit()


@app.get("/")
async def root():
    return {"status": "ok", "service": "Balans API"}