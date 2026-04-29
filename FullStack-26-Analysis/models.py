from pydantic import BaseModel
from typing import Optional

class VentaIn(BaseModel):
    vendedor: str
    fecha: str
    local: Optional[str] = ""
    producto: str
    canal: str = "fisica"
    costo: float

class VentaOut(VentaIn):
    id: int
    creado_en: str