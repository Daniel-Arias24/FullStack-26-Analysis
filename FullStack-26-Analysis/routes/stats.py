from fastapi import APIRouter
from database import get_db
from datetime import datetime

router = APIRouter(prefix="/api/stats", tags=["Análisis"])

MESES = ["Ene","Feb","Mar","Abr","May","Jun",
         "Jul","Ago","Sep","Oct","Nov","Dic"]

def cargar_ventas():
    conn = get_db()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM ventas").fetchall()]
    finally:
        conn.close()

@router.get("/dashboard")
def stats_dashboard():
    ventas = cargar_ventas()

    mensuales = [0] * 12
    for v in ventas:
        try:
            mes = datetime.strptime(v["fecha"], "%Y-%m-%d").month - 1
            mensuales[mes] += 1
        except:
            pass

    productos_map = {}
    for v in ventas:
        p = v["producto"]
        productos_map[p] = productos_map.get(p, 0) + 1

    vendedores_map = {}
    for v in ventas:
        nombre = v["vendedor"].split(" ")[0]
        vendedores_map[nombre] = vendedores_map.get(nombre, 0) + 1

    online = sum(v["costo"] for v in ventas if v["canal"] == "online")
    fisica = sum(v["costo"] for v in ventas if v["canal"] == "fisica")

    return {
        "ventas_mensuales": { "labels": MESES, "data": mensuales },
        "productos":         { "labels": list(productos_map.keys()), "data": list(productos_map.values()) },
        "vendedores":        { "labels": list(vendedores_map.keys()), "data": list(vendedores_map.values()) },
        "ingresos":          { "labels": ["Online","Tienda física"], "data": [online, fisica] },
        "total_ventas":      len(ventas),
        "total_ingresos":    sum(v["costo"] for v in ventas)
    }

@router.get("/vendedores")
def ranking_vendedores():
    ventas = cargar_ventas()
    ranking = {}
    for v in ventas:
        vend = v["vendedor"]
        if vend not in ranking:
            ranking[vend] = {"ventas": 0, "ingresos": 0}
        ranking[vend]["ventas"]   += 1
        ranking[vend]["ingresos"] += v["costo"]

    resultado = [
        { "vendedor": k, "ventas": v["ventas"], "ingresos": round(v["ingresos"], 2) }
        for k, v in ranking.items()
    ]
    return sorted(resultado, key=lambda x: x["ingresos"], reverse=True)

@router.get("/productos")
def analisis_productos():
    ventas = cargar_ventas()
    productos = {}
    for v in ventas:
        p = v["producto"]
        if p not in productos:
            productos[p] = {"unidades": 0, "ingresos": 0}
        productos[p]["unidades"] += 1
        productos[p]["ingresos"] += v["costo"]

    resultado = [
        { "producto": k, "unidades": v["unidades"], "ingresos": round(v["ingresos"], 2) }
        for k, v in productos.items()
    ]
    return sorted(resultado, key=lambda x: x["ingresos"], reverse=True)

@router.get("/resumen")
def resumen_general():
    ventas = cargar_ventas()
    if not ventas:
        return { "mensaje": "Sin ventas registradas aún" }

    total_ingresos = sum(v["costo"] for v in ventas)
    venta_max = max(ventas, key=lambda x: x["costo"])
    venta_min = min(ventas, key=lambda x: x["costo"])
    online = sum(v["costo"] for v in ventas if v["canal"] == "online")
    fisica = sum(v["costo"] for v in ventas if v["canal"] == "fisica")

    return {
        "total_ventas":    len(ventas),
        "total_ingresos":  round(total_ingresos, 2),
        "promedio_venta":  round(total_ingresos / len(ventas), 2),
        "venta_mas_alta":  { "producto": venta_max["producto"], "costo": venta_max["costo"], "vendedor": venta_max["vendedor"] },
        "venta_mas_baja":  { "producto": venta_min["producto"], "costo": venta_min["costo"], "vendedor": venta_min["vendedor"] },
        "ingresos_online": round(online, 2),
        "ingresos_fisica": round(fisica, 2),
    }