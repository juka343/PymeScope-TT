from app.clients.azure_doc_intel_client import AzureDocIntelClient

class AzureDocumentService:
    def __init__(self):
        self.azure_client = AzureDocIntelClient()

    def process_financial_document(self, file_url: str):
        try:
            # 1. Llamar a Azure
            raw_result = self.azure_client.analyze_document_from_url(file_url)

            # 2. Extraer información básica (Simplificado para esta etapa)
            # Aquí luego meteremos la lógica "inteligente" para diferenciar activos/pasivos
            extracted_content = {
                "tables_count": len(raw_result.tables),
                "text_content": raw_result.content[:500] + "...", # Solo una muestra
                "tables_data": []
            }

            # Ejemplo rápido de extracción de tablas
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