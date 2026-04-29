from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes import ventas, stats

app = FastAPI(title="ESPRIT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(ventas.router)
app.include_router(stats.router)

@app.get("/")
def root():
    return {"status": "ok", "api": "ESPRIT Ventas"}