from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings

class AzureDocIntelClient:
    def __init__(self):
        self.client = DocumentAnalysisClient(
            endpoint=settings.AZURE_DOC_INTEL_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOC_INTEL_KEY)
        )

    def analyze_document_from_url(self, file_url: str):
        """
        Envía una URL a Azure y espera el resultado.
        Usamos el modelo 'prebuilt-layout' que es ideal para tablas financieras.
        """
        print(f"Enviando a Azure: {file_url}")
        
        # Iniciamos el análisis (es una operación larga, por eso el 'begin')
        poller = self.client.begin_analyze_document_from_url(
            "prebuilt-layout", document_url=file_url
        )
        
        # Esperamos a que termine
        result = poller.result()
        
        print("Análisis de Azure completado.")
        return result