from pydantic import BaseModel, HttpUrl
from typing import Optional

# Este es el esquema de lo que RECIBE el backend del frontend
class DocumentoMetadata(BaseModel):
    project_id: str          # ID del proyecto en Firebase
    period_id: str           # ID del periodo (ej. "Trimestre 1")
    file_uuid: str           # El UUID que generaste en el front
    file_url: HttpUrl        # La URL de descarga de Firebase
    file_type: str           # "balance_general" o "estado_resultados"

# Este es un esquema simple de respuesta (lo mejoraremos luego con los datos reales)
class DocumentoProcesado(BaseModel):
    file_uuid: str
    status: str              # "success", "failed"
    data_extracted: dict     # Aquí vendrá el JSON crudo de Azure por ahora