# from fastapi import APIRouter, UploadFile, File
# from app.services.azure_document_service import analizar_documento
# from app.services.firebase_service import guardar_resultado

# router = APIRouter()

# @router.post("/documents/analyze")
# async def analyze(file: UploadFile = File(...)):
#     content = await file.read()
#     result = analizar_documento(content)

#     guardar_resultado({"resultado": str(result)})

#     return {"status": "ok"}
