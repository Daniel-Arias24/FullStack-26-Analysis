from fastapi import APIRouter, HTTPException
from database import get_db
from models import VentaIn, VentaOut

router = APIRouter(prefix="/api/ventas", tags=["Ventas"])

@router.post("", response_model=VentaOut, status_code=201)
def registrar_venta(venta: VentaIn):
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO ventas (vendedor, fecha, local, producto, canal, costo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (venta.vendedor, venta.fecha, venta.local,
              venta.producto, venta.canal, venta.costo))
        conn.commit()
        nueva = conn.execute(
            "SELECT * FROM ventas WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return dict(nueva)
    finally:
        conn.close()

@router.get("", response_model=list[VentaOut])
def obtener_ventas():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM ventas ORDER BY fecha DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get("/{venta_id}", response_model=VentaOut)
def obtener_venta(venta_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM ventas WHERE id = ?", (venta_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        return dict(row)
    finally:
        conn.close()

@router.delete("/{venta_id}", status_code=204)
def eliminar_venta(venta_id: int):
    conn = get_db()
    try:
        affected = conn.execute(
            "DELETE FROM ventas WHERE id = ?", (venta_id,)
        ).rowcount
        conn.commit()
        if affected == 0:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
    finally:
        conn.close()