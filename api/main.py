from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import transactions, summary

app = FastAPI(title="Balans API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router)
app.include_router(summary.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "Balans API"}