from app.clients.azure_doc_intel_client import AzureDocIntelClient

class AzureDocumentService:
    def __init__(self):
        self.azure_client = AzureDocIntelClient()

    async def process_financial_document_async(self, file_url: str):
        try:
            # 1. Llamar a Azure esperando la respuesta asíncrona
            raw_result = await self.azure_client.analyze_document_from_url_async(file_url)

            # 2. Extraer información básica (Tu código original)
            extracted_content = {
                "tables_count": len(raw_result.tables),
                "text_content": raw_result.content[:500] + "...",
                "tables_data": []
            }

            for table in raw_result.tables:
                table_info = []
                for cell in table.cells:
                    table_info.append({
                        "text": cell.content,
                        "row": cell.row_index,
                        "col": cell.column_index
                    })
                extracted_content["tables_data"].append(table_info)

            return extracted_content

        except Exception as e:
            print(f"Error en el servicio de Azure: {str(e)}")
            raise e