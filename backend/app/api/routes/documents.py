from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.services.firebase_service import FirebaseDBManager
from app.services.azure_document_service import AzureDocumentService

#Servicios
router = APIRouter()
_db_manager = FirebaseDBManager()
_azure_service = AzureDocumentService()

#Varuiable global para la inicialización de firebase
_is_initialized = False


def _ensure_firebase_initialized() -> None:
	global _is_initialized
	if _is_initialized:
		return
	if not settings.FIREBASE_CREDENTIALS_PATH:
		raise HTTPException(status_code=500, detail="FIREBASE_CREDENTIALS_PATH is not set.")
	if not settings.FIREBASE_STORAGE_BUCKET:
		raise HTTPException(status_code=500, detail="FIREBASE_STORAGE_BUCKET is not set.")
	_db_manager.inicializar_app(settings.FIREBASE_CREDENTIALS_PATH, settings.FIREBASE_STORAGE_BUCKET)
	_is_initialized = True

# --- MODELOS DE DATOS ---
class SolicitudProcesamientoAzure(BaseModel):
    project_id: str
    period_id: str
    file_uuid: str
    file_url: str
    file_type: str

# --- ENDPOINTS ---
@router.post("/documents/process-azure")
async def procesar_documento_con_azure(payload: SolicitudProcesamientoAzure) -> Dict[str, Any]:
    """
    Recibe la URL de Firebase del Frontend, la envía a Azure,
    y devuelve la data extraída.
    """
    _ensure_firebase_initialized() # Aseguramos que Firebase esté listo por si queremos guardar logs
    
    print(f"Iniciando procesamiento Azure para: {payload.file_uuid}")

    try:
        # 1. Llamar al servicio de Azure que creamos antes
        # Nota: Asegúrate de que payload.file_url sea la URL descargable (https), no gs://
        resultado_azure = _azure_service.process_financial_document(payload.file_url)

        # 2. Guardar el resultado en Firebase automáticamente
        # Así ya queda respaldado en la BD sin que el Frontend tenga que enviarlo de regreso.
        # _db_manager.actualizar_datos_ocr(payload.file_uuid, resultado_azure)

        # 3. Retornar al Frontend
        return {
            "uuid": payload.file_uuid,
            "estatus": "Procesado",
            "project_id": payload.project_id,
            "tipo": payload.file_type,
            "data": resultado_azure # Aquí va el JSON con tablas y texto
        }

    except Exception as e:
        print(f"Error procesando con Azure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en motor de IA: {str(e)}")