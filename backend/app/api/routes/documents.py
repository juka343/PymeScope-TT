from typing import Any, Dict
from pathlib import Path
import os
import tempfile
import uuid as uuid_lib

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Form
from pydantic import BaseModel

from app.core.config import settings
from app.services.firebase_service import FirebaseDBManager

router = APIRouter()
_db_manager = FirebaseDBManager()
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


class RegistroInicialRequest(BaseModel):
	tipo_documento: str
	url_archivo: str


class DatosOCRRequest(BaseModel):
	datos_contables: Dict[str, Any]


class AnalisisRequest(BaseModel):
	analisis_financiero: Dict[str, Any]


class RecomendacionesRequest(BaseModel):
	recomendaciones: Dict[str, Any]


@router.post("/documents/register")
def registrar_documento(payload: RegistroInicialRequest) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	doc_uuid = str(uuid_lib.uuid4())
	_db_manager.registrar_carga_inicial(doc_uuid, payload.tipo_documento, payload.url_archivo)
	return {"uuid": doc_uuid, "estatus": "Recibido"}


@router.post("/documents/{uuid}/ocr")
def actualizar_ocr(uuid: str, payload: DatosOCRRequest) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	try:
		_db_manager.actualizar_datos_ocr(uuid, payload.datos_contables)
		return {"uuid": uuid, "estatus": "Extraido"}
	except ValueError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/documents/{uuid}/analysis")
def guardar_analisis(uuid: str, payload: AnalisisRequest) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	try:
		_db_manager.guardar_resultados_analisis(uuid, payload.analisis_financiero)
		return {"uuid": uuid, "message": "analisis_guardado"}
	except ValueError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/documents/{uuid}/recommendations")
def guardar_recomendaciones(uuid: str, payload: RecomendacionesRequest) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	try:
		_db_manager.finalizar_con_recomendaciones(uuid, payload.recomendaciones)
		return {"uuid": uuid, "estatus": "Finalizado"}
	except ValueError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/documents/{uuid}")
def obtener_documento(uuid: str) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	try:
		doc = _db_manager.obtener_documento(uuid)
		return {"uuid": uuid, "documento": doc}
	except ValueError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/documents/upload-and-register")
async def subir_y_registrar(
	tipo_documento: str = Form(...),
	file: UploadFile = File(...),
	destination_path: str | None = Form(None),
) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	doc_uuid = str(uuid_lib.uuid4())
	filename = file.filename or f"{doc_uuid}.bin"
	default_path = f"analisis_financieros/{doc_uuid}/{filename}"
	blob_path = destination_path or default_path
	suffix = Path(filename).suffix
	with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
		temp_path = temp_file.name
		temp_file.write(await file.read())
	try:
		_db_manager.subir_archivo_storage(temp_path, blob_path)
		gs_url = f"gs://{settings.FIREBASE_STORAGE_BUCKET}/{blob_path}"
		_db_manager.registrar_carga_inicial(doc_uuid, tipo_documento, gs_url)
		return {"uuid": doc_uuid, "path": blob_path, "estatus": "Recibido"}
	finally:
		if os.path.exists(temp_path):
			os.remove(temp_path)


@router.post("/storage/upload")
async def subir_archivo_storage(destination_path: str, file: UploadFile = File(...)) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	suffix = Path(file.filename or "").suffix
	with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
		temp_path = temp_file.name
		temp_file.write(await file.read())
	try:
		_db_manager.subir_archivo_storage(temp_path, destination_path)
		return {
			"path": destination_path,
			"gs_url": f"gs://{settings.FIREBASE_STORAGE_BUCKET}/{destination_path}",
		}
	finally:
		if os.path.exists(temp_path):
			os.remove(temp_path)


@router.get("/storage/signed-url")
def obtener_url_firmada(
	blob_path: str,
	expiration_minutes: int = Query(60, ge=1, le=1440),
) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	try:
		url = _db_manager.generar_url_firmada_storage(blob_path, expiration_minutes)
		return {"url": url, "expires_in_minutes": expiration_minutes}
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/storage/{blob_path:path}")
def eliminar_archivo_storage(blob_path: str) -> Dict[str, Any]:
	_ensure_firebase_initialized()
	_db_manager.eliminar_archivo_storage(blob_path)
	return {"path": blob_path, "deleted": True}
