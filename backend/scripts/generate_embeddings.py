"""
Script para generar los embeddings canónicos pre-calculados.

Uso:
    cd backend
    python scripts/generate_embeddings.py

Esto crea: backend/app/services/canonical_embeddings.json
"""

import sys
import os

# Agregar el directorio del backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.services.embedding_service import EmbeddingService

def main():
    if not settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY no está configurada en .env")
        sys.exit(1)
    
    print("🔧 Generando embeddings canónicos con Gemini...\n")
    
    # Resetear singleton para asegurar limpieza
    EmbeddingService.reset()
    
    service = EmbeddingService(
        api_key=settings.GEMINI_API_KEY,
        model=getattr(settings, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    )
    
    embeddings = service.generate_canonical_embeddings()
    
    print(f"\n📊 Resumen:")
    print(f"   Conceptos generados: {len(embeddings)}")
    print(f"   Dimensiones por vector: {len(list(embeddings.values())[0])}")
    print(f"   Tamaño estimado: ~{os.path.getsize(os.path.join(os.path.dirname(__file__), '..', 'app', 'services', 'canonical_embeddings.json')) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
