from azure.ai.formrecognizer.aio import DocumentAnalysisClient # <-- Versión asíncrona
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings

class AzureDocIntelClient:
    async def analyze_document_from_url_async(self, file_url: str):
        print(f"Enviando a Azure (Paralelo): {file_url}")
        
        # El bloque async with maneja la conexión eficientemente
        async with DocumentAnalysisClient(
            endpoint=settings.AZURE_DOC_INTEL_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOC_INTEL_KEY)
        ) as client:
            
            poller = await client.begin_analyze_document_from_url(
                "prebuilt-layout", document_url=file_url
            )
            
            result = await poller.result()
            print("Análisis de Azure completado.")
            return result