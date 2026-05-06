from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import timedelta
import os

import firebase_admin
from firebase_admin import credentials, storage as fb_storage
from firebase_admin import firestore  # <-- te faltaba esto


class FirebaseDBManager:
    """Firestore data access layer for financial analysis documents."""

    def __init__(self) -> None:
        self._db: Optional[firestore.Client] = None
        self._bucket = None  # tipo flexible para no pelear con hints

    # Flujo: Frontend -> Storage -> OCR -> Calculo -> IA -> Firestore
    def inicializar_app(self, credenciales_path: str, storage_bucket: str | None = None) -> None:
        if not firebase_admin._apps:
            cred = credentials.Certificate(credenciales_path)
            options = {"storageBucket": storage_bucket} if storage_bucket else None
            firebase_admin.initialize_app(cred, options)

        self._db = firestore.client()

        # Si pasas bucket, inicializa storage
        self._bucket = fb_storage.bucket() if storage_bucket else None

    def _get_db(self) -> firestore.Client:
        if self._db is None:
            raise RuntimeError("Firebase app not initialized. Call inicializar_app().")
        return self._db

    def _get_bucket(self):
        # Nota: fb_storage.bucket() regresa un google.cloud.storage.bucket.Bucket
        if self._bucket is None:
            raise RuntimeError("Storage not initialized. Call inicializar_app() with bucket.")
        return self._bucket

    def _get_doc_ref(self, uuid: str) -> firestore.DocumentReference:
        db = self._get_db()
        doc_ref = db.collection("analisis_financieros").document(uuid)
        if not doc_ref.get().exists:
            raise KeyError(f"UUID not found: {uuid}")
        return doc_ref

    # Flujo: Frontend -> Storage -> Firestore (registro inicial)
    def registrar_carga_inicial(self, uuid: str, tipo_doc: str, url_storage: str) -> None:
        db = self._get_db()
        doc_ref = db.collection("analisis_financieros").document(uuid)
        doc_ref.set(
            {
                "uid_archivo": uuid,
                "version": 1,
                "estatus": "Recibido",
                "tipo_documento": tipo_doc,
                "fecha_carga": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "url_archivo": url_storage,
                "error_message": None,
                "datos_contables": {},
                "analisis_financiero": {},
                "recomendaciones": {},
            }
        )

    # Flujo: OCR -> Firestore (datos crudos)
    def actualizar_datos_ocr(self, uuid: str, datos_json: Dict[str, Any]) -> None:
        try:
            doc_ref = self._get_doc_ref(uuid)
            doc_ref.update(
                {
                    "datos_contables": datos_json,
                    "estatus": "Extraido",
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )
        except KeyError as exc:
            raise ValueError("UUID does not exist in Firestore.") from exc

    # Flujo: Calculo Python -> Firestore (analisis financiero)
    def guardar_resultados_analisis(self, uuid: str, resultados_dict: Dict[str, Any]) -> None:
        try:
            doc_ref = self._get_doc_ref(uuid)
            doc_ref.set(
                {
                    "analisis_financiero": resultados_dict,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
                merge=True,
            )
        except KeyError as exc:
            raise ValueError("UUID does not exist in Firestore.") from exc

    # Flujo: IA -> Firestore (recomendaciones finales)
    def finalizar_con_recomendaciones(self, uuid: str, recomendaciones_dict: Dict[str, Any]) -> None:
        try:
            doc_ref = self._get_doc_ref(uuid)
            doc_ref.update(
                {
                    "recomendaciones": recomendaciones_dict,
                    "estatus": "Finalizado",
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )
        except KeyError as exc:
            raise ValueError("UUID does not exist in Firestore.") from exc

    # Flujo: Proyecciones -> Firestore (guardar escenario proforma)
    def guardar_proyeccion(self, uuid_proyecto: str, proyeccion_data: Dict[str, Any], collection_name: str = "proyecciones") -> str:
        try:
            db = self._get_db()
            # Acceder al documento del proyecto principal (Colección consistente con el Frontend)
            doc_ref = db.collection("proyectos").document(uuid_proyecto)
            
            # Crear una subcolección específica y un nuevo documento con ID autogenerado
            new_proy_ref = doc_ref.collection(collection_name).document()
            
            # Guardar el contenido con timestamp del servidor
            proyeccion_data["created_at"] = firestore.SERVER_TIMESTAMP
            new_proy_ref.set(proyeccion_data)
            
            return new_proy_ref.id
        except Exception as exc:
            raise ValueError(f"Error guardando proyección en Firestore: {str(exc)}")

    # Flujo: Frontend -> Firestore (consulta completa)
    def obtener_documento(self, uuid: str) -> Dict[str, Any]:
        try:
            doc_ref = self._get_doc_ref(uuid)
            snapshot = doc_ref.get()
            return snapshot.to_dict() or {}
        except KeyError as exc:
            raise ValueError("UUID does not exist in Firestore.") from exc

    # Storage: upload a local file to Cloud Storage.
    def subir_archivo_storage(self, local_file_path: str, destination_blob_path: str) -> None:
        bucket = self._get_bucket()
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Local file not found: {local_file_path}")
        blob = bucket.blob(destination_blob_path)
        blob.upload_from_filename(local_file_path)

    # Storage: download a file from Cloud Storage to local path.
    def descargar_archivo_storage(self, source_blob_path: str, destination_local_path: str) -> None:
        bucket = self._get_bucket()
        blob = bucket.blob(source_blob_path)
        if not blob.exists():
            raise FileNotFoundError(f"Blob not found: {source_blob_path}")
        blob.download_to_filename(destination_local_path)

    # Storage: generate a signed URL for temporary access.
    def generar_url_firmada_storage(self, blob_path: str, expiration_minutes: int = 60) -> str:
        bucket = self._get_bucket()
        blob = bucket.blob(blob_path)
        if not blob.exists():
            raise FileNotFoundError(f"Blob not found: {blob_path}")
        return blob.generate_signed_url(expiration=timedelta(minutes=expiration_minutes))

    # Storage: delete a file from Cloud Storage.
    def eliminar_archivo_storage(self, blob_path: str) -> None:
        bucket = self._get_bucket()
        blob = bucket.blob(blob_path)
        if not blob.exists():
            return
        blob.delete()
