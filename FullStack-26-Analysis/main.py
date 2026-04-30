from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes import ventas, stats
from routes import dev          # herramientas de desarrollo / testing

app = FastAPI(
    title="ESPRIT — API de Ventas",
    description="""
    Microservicio Python que gestiona ventas y análisis de datos.

    **Servicios disponibles:**
    - `/api/ventas`  → CRUD de ventas (guardadas en SQLite)
    - `/api/stats`   → Dashboard y análisis para las gráficas del front
    - `/api/dev`     → Herramientas de desarrollo (seed, limpieza, errores simulados)

    **Nota:** La autenticación de usuarios corre en Spring Boot :8080
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # En producción: reemplazar por la URL real del front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tabla ventas si no existe
init_db()

# Registrar todos los routers
app.include_router(ventas.router)
app.include_router(stats.router)
app.include_router(dev.router)

@app.get("/", tags=["Root"])
def root():
    return {
        "status": "ok",
        "api":    "ESPRIT Ventas",
        "docs":   "http://localhost:8000/docs"
    }