# ============================================================
#  routes/dev.py  —  Herramientas de desarrollo / testing
#
#  ⚠️  SOLO PARA DESARROLLO  ⚠️
#  Estos endpoints permiten:
#    1. Inyectar errores simulados (para probar el front)
#    2. Limpiar datos (tablas o registros específicos)
#    3. Sembrar datos de prueba (seed)
#    4. Consultar el estado actual del servidor
#
#  ENDPOINTS:
#  POST  /api/dev/seed                → Insertar ventas de prueba
#  POST  /api/dev/seed/custom         → Insertar N ventas aleatorias
#  DELETE /api/dev/limpiar            → Borrar TODAS las ventas
#  DELETE /api/dev/limpiar/rango      → Borrar ventas entre fechas
#  DELETE /api/dev/limpiar/vendedor   → Borrar ventas de un vendedor
#  POST  /api/dev/error/500           → Simular error 500
#  POST  /api/dev/error/404           → Simular error 404
#  POST  /api/dev/error/lento         → Simular respuesta lenta
#  POST  /api/dev/error/bd            → Simular fallo de base de datos
#  GET   /api/dev/estado              → Ver estado actual del servidor
# ============================================================

from fastapi      import APIRouter, HTTPException, Query
from database     import get_db
from models       import VentaIn
from pydantic     import BaseModel
from typing       import Optional
from datetime     import datetime, timedelta
import random
import time

router = APIRouter(prefix="/api/dev", tags=["🛠 Dev Tools"])

# ── Datos de ejemplo para el seed ────────────────────────────
VENDEDORES  = ["Samuel Soracá", "Daniel Arias", "Brahian Marin", "Juan David Rojas"]
PRODUCTOS   = ["Chaqueta", "Jeans", "Camiseta", "Vestidos"]
CANALES     = ["online", "fisica"]
PRECIOS     = {
    "Chaqueta": (189_000, 420_000),
    "Jeans":    (105_000, 340_990),
    "Camiseta": (249_900, 289_900),
    "Vestidos": (320_000, 390_990),
}

# ── Modelos de entrada ────────────────────────────────────────
class SeedCustomBody(BaseModel):
    cantidad:    int  = 20       # cuántas ventas generar
    meses_atras: int  = 6        # rango de fechas hacia atrás

class LimpiarRangoBody(BaseModel):
    fecha_inicio: str            # "YYYY-MM-DD"
    fecha_fin:    str            # "YYYY-MM-DD"

class LimpiarVendedorBody(BaseModel):
    vendedor: str

# ════════════════════════════════════════════════════════════
#  1. SEED — Insertar ventas de prueba predefinidas
#     POST /api/dev/seed
#
#  Inserta un set fijo de 16 ventas (2 por producto por canal)
#  repartidas en los últimos 6 meses para que todas las
#  gráficas del dashboard muestren datos visibles.
# ════════════════════════════════════════════════════════════
@router.post("/seed", status_code=201)
def seed_datos():
    conn = get_db()
    try:
        hoy = datetime.today()
        insertadas = 0

        # Generar una venta por cada combinación vendedor + producto + canal
        for i, vendedor in enumerate(VENDEDORES):
            for j, producto in enumerate(PRODUCTOS):
                canal  = CANALES[(i + j) % 2]
                precio = random.uniform(*PRECIOS[producto])
                # Distribuir fechas en los últimos 6 meses
                dias_atras = random.randint(0, 180)
                fecha = (hoy - timedelta(days=dias_atras)).strftime("%Y-%m-%d")

                conn.execute("""
                    INSERT INTO ventas (vendedor, fecha, local, producto, canal, costo)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (vendedor, fecha, "San Diego", producto, canal, round(precio, 2)))
                insertadas += 1

        conn.commit()
        return {
            "ok":        True,
            "mensaje":   f"✅ Se insertaron {insertadas} ventas de prueba",
            "insertadas": insertadas
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al insertar seed: {str(e)}")
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#  2. SEED CUSTOM — Insertar N ventas aleatorias
#     POST /api/dev/seed/custom
#     Body: { "cantidad": 30, "meses_atras": 3 }
# ════════════════════════════════════════════════════════════
@router.post("/seed/custom", status_code=201)
def seed_custom(body: SeedCustomBody):
    if body.cantidad < 1 or body.cantidad > 500:
        raise HTTPException(status_code=400, detail="cantidad debe estar entre 1 y 500")
    if body.meses_atras < 1 or body.meses_atras > 24:
        raise HTTPException(status_code=400, detail="meses_atras debe estar entre 1 y 24")

    conn = get_db()
    try:
        hoy = datetime.today()
        dias_rango = body.meses_atras * 30

        for _ in range(body.cantidad):
            vendedor = random.choice(VENDEDORES)
            producto = random.choice(PRODUCTOS)
            canal    = random.choice(CANALES)
            precio   = random.uniform(*PRECIOS[producto])
            dias     = random.randint(0, dias_rango)
            fecha    = (hoy - timedelta(days=dias)).strftime("%Y-%m-%d")

            conn.execute("""
                INSERT INTO ventas (vendedor, fecha, local, producto, canal, costo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (vendedor, fecha, "San Diego", producto, canal, round(precio, 2)))

        conn.commit()
        return {
            "ok":        True,
            "mensaje":   f"✅ Se generaron {body.cantidad} ventas aleatorias en los últimos {body.meses_atras} meses",
            "insertadas": body.cantidad
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar ventas: {str(e)}")
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#  3. LIMPIAR TODO — Borrar TODAS las ventas
#     DELETE /api/dev/limpiar
#
#  Vacía la tabla ventas completamente y reinicia el
#  autoincremento del ID para empezar desde 1.
# ════════════════════════════════════════════════════════════
@router.delete("/limpiar")
def limpiar_todo():
    conn = get_db()
    try:
        # Contar cuántas había antes
        total_antes = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]

        conn.execute("DELETE FROM ventas")
        # Reiniciar el autoincremento
        conn.execute("DELETE FROM sqlite_sequence WHERE name='ventas'")
        conn.commit()

        return {
            "ok":              True,
            "mensaje":         f"🗑 Se eliminaron {total_antes} ventas. La tabla está limpia.",
            "eliminadas":      total_antes,
            "tabla_vacia":     True
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al limpiar: {str(e)}")
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#  4. LIMPIAR POR RANGO DE FECHAS
#     DELETE /api/dev/limpiar/rango
#     Body: { "fecha_inicio": "2025-01-01", "fecha_fin": "2025-03-31" }
# ════════════════════════════════════════════════════════════
@router.delete("/limpiar/rango")
def limpiar_por_rango(body: LimpiarRangoBody):
    try:
        datetime.strptime(body.fecha_inicio, "%Y-%m-%d")
        datetime.strptime(body.fecha_fin,    "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD")

    conn = get_db()
    try:
        affected = conn.execute(
            "DELETE FROM ventas WHERE fecha BETWEEN ? AND ?",
            (body.fecha_inicio, body.fecha_fin)
        ).rowcount
        conn.commit()

        return {
            "ok":         True,
            "mensaje":    f"🗑 Se eliminaron {affected} ventas entre {body.fecha_inicio} y {body.fecha_fin}",
            "eliminadas": affected
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#  5. LIMPIAR POR VENDEDOR
#     DELETE /api/dev/limpiar/vendedor
#     Body: { "vendedor": "Samuel Soracá" }
# ════════════════════════════════════════════════════════════
@router.delete("/limpiar/vendedor")
def limpiar_por_vendedor(body: LimpiarVendedorBody):
    if not body.vendedor.strip():
        raise HTTPException(status_code=400, detail="El campo vendedor no puede estar vacío")

    conn = get_db()
    try:
        affected = conn.execute(
            "DELETE FROM ventas WHERE vendedor = ?",
            (body.vendedor,)
        ).rowcount
        conn.commit()

        if affected == 0:
            return {
                "ok":         True,
                "mensaje":    f"No se encontraron ventas del vendedor '{body.vendedor}'",
                "eliminadas": 0
            }

        return {
            "ok":         True,
            "mensaje":    f"🗑 Se eliminaron {affected} ventas de '{body.vendedor}'",
            "eliminadas": affected
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#  6. SIMULAR ERROR 500
#     POST /api/dev/error/500
#
#  El front debe mostrar su mensaje de error de servidor.
#  Útil para probar el bloque catch() del fetch en el JS.
# ════════════════════════════════════════════════════════════
@router.post("/error/500")
def simular_error_500():
    raise HTTPException(
        status_code=500,
        detail="💥 Error interno simulado. Esto es una prueba del servidor."
    )


# ════════════════════════════════════════════════════════════
#  7. SIMULAR ERROR 404
#     POST /api/dev/error/404
#
#  El front debe mostrar su mensaje de recurso no encontrado.
# ════════════════════════════════════════════════════════════
@router.post("/error/404")
def simular_error_404():
    raise HTTPException(
        status_code=404,
        detail="🔍 Recurso no encontrado (simulado). Esto es una prueba."
    )


# ════════════════════════════════════════════════════════════
#  8. SIMULAR RESPUESTA LENTA
#     POST /api/dev/error/lento?segundos=5
#
#  Retrasa la respuesta N segundos para probar timeouts,
#  loaders y el comportamiento del front bajo latencia.
# ════════════════════════════════════════════════════════════
@router.post("/error/lento")
def simular_lentitud(segundos: int = Query(default=3, ge=1, le=15)):
    time.sleep(segundos)
    return {
        "ok":      True,
        "mensaje": f"⏱ Respuesta retrasada {segundos} segundos intencionalmente.",
        "segundos": segundos
    }


# ════════════════════════════════════════════════════════════
#  9. SIMULAR FALLO DE BASE DE DATOS
#     POST /api/dev/error/bd
#
#  Intenta una operación inválida en SQLite para generar
#  un error real de BD y ver cómo lo maneja el sistema.
# ════════════════════════════════════════════════════════════
@router.post("/error/bd")
def simular_error_bd():
    conn = get_db()
    try:
        # Consulta a una tabla que no existe → error real de SQLite
        conn.execute("SELECT * FROM tabla_que_no_existe")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"🗄 Error de base de datos simulado: {str(e)}"
        )
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#  10. ESTADO DEL SERVIDOR
#      GET /api/dev/estado
#
#  Devuelve un snapshot del estado actual: cuántas ventas hay,
#  rango de fechas, ingresos totales, y si la BD responde.
# ════════════════════════════════════════════════════════════
@router.get("/estado")
def estado_servidor():
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]

        if total == 0:
            return {
                "ok":          True,
                "bd_activa":   True,
                "total_ventas": 0,
                "ingresos_totales": 0,
                "fecha_primera": None,
                "fecha_ultima":  None,
                "vendedores_activos": [],
                "mensaje": "La tabla ventas está vacía"
            }

        row = conn.execute("""
            SELECT
                MIN(fecha)        AS fecha_primera,
                MAX(fecha)        AS fecha_ultima,
                SUM(costo)        AS ingresos_totales
            FROM ventas
        """).fetchone()

        vendedores = [
            r[0] for r in conn.execute(
                "SELECT DISTINCT vendedor FROM ventas ORDER BY vendedor"
            ).fetchall()
        ]

        return {
            "ok":                 True,
            "bd_activa":          True,
            "total_ventas":       total,
            "ingresos_totales":   round(row["ingresos_totales"], 2),
            "fecha_primera":      row["fecha_primera"],
            "fecha_ultima":       row["fecha_ultima"],
            "vendedores_activos": vendedores,
            "timestamp_consulta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar estado: {str(e)}")
    finally:
        conn.close()