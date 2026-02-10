# from app.clients.azure_doc_intel_client import get_azure_doc_client

# def analizar_documento(document_bytes: bytes):
#     client = get_azure_doc_client()

#     poller = client.begin_analyze_document(
#         model_id="prebuilt-document",
#         document=document_bytes
#     )

#     result = poller.result()
#     return result
