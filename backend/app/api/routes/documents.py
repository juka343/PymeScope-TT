import asyncio
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.services.firebase_service import FirebaseDBManager
from app.services.azure_document_service import AzureDocumentService
from app.services.financial_calculator import FinancialCalculator

#Servicios
router = APIRouter()
_db_manager = FirebaseDBManager()
_azure_service = AzureDocumentService()
_calculator = FinancialCalculator()

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
#modelo viejo, revisar después si quitar...
class SolicitudProcesamientoAzure(BaseModel):
    project_id: str
    period_id: str
    file_uuid: str
    file_url: str
    file_type: str

#nuevo modelo
class SolicitudAnalisisPeriodo(BaseModel):
    project_id: str
    period_id: str
    balance_url: str
    resultados_url: str
    periodicidad: str

# --- ENDPOINTS ---
@router.post("/documents/analyze-period")
async def analizar_periodo_completo(payload: SolicitudAnalisisPeriodo) -> Dict[str, Any]:
    _ensure_firebase_initialized()
    
    print(f"Iniciando análisis cruzado para el periodo: {payload.period_id}")

    try:
        # 1. Extraer datos crudos con Azure (Balance)
        print("-> Extrayendo Balance General y estado de resultados...")
        balance_data, resultados_data = await asyncio.gather(
            _azure_service.process_financial_document_async(payload.balance_url),
            _azure_service.process_financial_document_async(payload.resultados_url)
        )

        # 3. Pasar la data por tu Motor Extractor para calcular rentabilidad
        print("-> Calculando indicadores financieros...")
        analisis_rentabilidad = _calculator.calcular_rentabilidad(balance_data, resultados_data)
        analisis_liquidez = _calculator.calcular_liquidez(balance_data)
        analisis_endeudamiento = _calculator.calcular_endeudamiento(balance_data, resultados_data)
        analisis_rotacion = _calculator.calcular_rotacion(balance_data, resultados_data, periodicidad=payload.periodicidad)
        analisis_estructura = _calculator.calcular_estructura(balance_data)

        # 4. Retornar el paquete completo listo para el Dashboard de Vue
        return {
            "estatus": "Completado",
            "project_id": payload.project_id,
            "period_id": payload.period_id,
            "dashboard_data": {
                "rentabilidad": analisis_rentabilidad,
                "liquidez": analisis_liquidez,
                "endeudamiento": analisis_endeudamiento,
                "rotacion": analisis_rotacion,
                "estructura": analisis_estructura
            }
        }    

    except Exception as e:
        print(f"Error en análisis cruzado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando el periodo: {str(e)}")

#-----------------------------------------------------------------------------------------------------------
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