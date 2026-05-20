"""
Servicio de Embeddings Semánticos para PymeScope.

Usa Gemini Embedding API para encontrar conceptos financieros
por similitud semántica cuando el diccionario de keywords falla.
"""

import json
import math
import os
from typing import Dict, List, Optional, Tuple

from google import genai
from google.genai import types


# ─── Conceptos Canónicos ─────────────────────────────────────────────────────
# Descripciones enriquecidas de cada concepto financiero.
# El texto es lo que se embedea como "ancla" para comparar contra filas OCR.
CONCEPTOS_CANONICOS: Dict[str, str] = {
    # === Rentabilidad (Estado de Resultados) ===
    "ventas_netas": "Ventas netas totales, ingresos totales, ingresos propios netos o ingresos operativos de la empresa",
    "utilidad_neta": "Utilidad neta consolidada, utilidad o pérdida neta, resultado neto del ejercicio",
    "utilidad_antes_impuestos": "Utilidad antes de impuestos, utilidad o pérdida antes de ISR y PTU",
    "impuestos": "ISR, provisión de ISR, impuesto sobre la renta o impuestos a la utilidad",

    # === Liquidez (Balance General) ===
    "activo_circulante": "Total de activo circulante, suma activo circulante, activos corrientes a corto plazo",
    "pasivo_circulante": "Total de pasivo circulante, suma pasivo circulante, pasivos corrientes a corto plazo",
    "inventario": "Inventarios, mercancías o almacén de productos",

    # === Endeudamiento ===
    "activo_total": "Total de activos, suma activo, activo total de la empresa",
    "capital_contable": "Capital contable total, patrimonio neto, hacienda pública o recursos propios de los accionistas",
    "pasivo_total": "Pasivo total, suma pasivo, total de deudas y obligaciones de la empresa",
    "utilidad_operacion": "Utilidad de operación, resultado operativo o ganancia operativa",
    "gastos_financieros": "Gastos financieros, costo integral de financiamiento, resultado integral de financiamiento",

    # === Rotación ===
    "cuentas_por_cobrar": "Cuentas por cobrar a clientes o deudores comerciales",
    "costo_de_ventas": "Costo de ventas, costo de lo vendido o costo de servicios",
    "activo_fijo": "Activo fijo neto, propiedad planta y equipo o activo no circulante",

    # === Estructura ===
    "capital_social": "Capital social contribuido o aportado por los socios, aportaciones de capital",
    "pasivo_largo_plazo": "Pasivo a largo plazo, pasivo no circulante o deuda a largo plazo",
}


class EmbeddingService:
    """
    Servicio singleton para búsquedas semánticas de conceptos financieros.
    
    Uso:
        service = EmbeddingService(api_key="...", model="gemini-embedding-001")
        concept, score = service.find_best_match("Gasto financiero neto")
        # → ("gastos_financieros", 0.938)
    """

    _instance: Optional["EmbeddingService"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str = None, model: str = "gemini-embedding-001"):
        if EmbeddingService._initialized:
            return
        
        self._api_key = api_key
        self._model = model
        self._client: Optional[genai.Client] = None
        self._canonical_embeddings: Dict[str, List[float]] = {}
        self._row_cache: Dict[str, List[float]] = {}  # Cache para filas ya embebeadas
        
        # Cargar embeddings canónicos pre-calculados
        self._load_canonical_embeddings()
        
        # Inicializar cliente Gemini solo si hay API key
        if self._api_key:
            try:
                self._client = genai.Client(api_key=self._api_key)
                EmbeddingService._initialized = True
            except Exception as e:
                print(f"⚠️ EmbeddingService: No se pudo inicializar el cliente Gemini: {e}")
                self._client = None

    def _load_canonical_embeddings(self):
        """Carga embeddings pre-calculados desde archivo JSON."""
        embeddings_path = os.path.join(
            os.path.dirname(__file__), "canonical_embeddings.json"
        )
        if os.path.exists(embeddings_path):
            with open(embeddings_path, "r") as f:
                self._canonical_embeddings = json.load(f)
            print(f"✅ EmbeddingService: {len(self._canonical_embeddings)} embeddings canónicos cargados")
        else:
            print(f"⚠️ EmbeddingService: No se encontró {embeddings_path}. El fallback semántico estará deshabilitado.")

    def is_available(self) -> bool:
        """Verifica si el servicio está listo para usar."""
        return self._client is not None and len(self._canonical_embeddings) > 0

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Genera embedding de un texto usando Gemini API. Usa cache para evitar llamadas repetidas."""
        if not self._client:
            return None
        
        # Buscar en cache
        cache_key = text.lower().strip()
        if cache_key in self._row_cache:
            return self._row_cache[cache_key]
        
        try:
            response = self._client.models.embed_content(
                model=self._model,
                contents=text,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
            )
            embedding = response.embeddings[0].values
            # Guardar en cache
            self._row_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            print(f"⚠️ EmbeddingService: Error generando embedding: {e}")
            return None

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def find_best_match(self, text: str, threshold: float = 0.85) -> Tuple[Optional[str], float]:
        """
        Compara un texto contra todos los conceptos canónicos y retorna el mejor match.
        
        Args:
            text: Texto de la fila del documento (ej. "Gasto financiero neto")
            threshold: Umbral mínimo de similitud para considerar un match
            
        Returns:
            (concept_key, score) si score >= threshold, o (None, 0.0)
        """
        if not self.is_available():
            return None, 0.0
        
        embedding = self.get_embedding(text)
        if embedding is None:
            return None, 0.0
        
        best_concept = None
        best_score = 0.0
        
        for concept_key, canonical_embedding in self._canonical_embeddings.items():
            score = self.cosine_similarity(embedding, canonical_embedding)
            if score > best_score:
                best_score = score
                best_concept = concept_key
        
        if best_score >= threshold:
            return best_concept, best_score
        
        return None, best_score

    def find_match_for_concept(self, text: str, concept_key: str, threshold: float = 0.85) -> float:
        """
        Verifica si un texto corresponde a un concepto específico.
        
        Args:
            text: Texto de la fila del documento
            concept_key: Clave del concepto canónico a comparar (ej. "ventas_netas")
            threshold: Umbral mínimo de similitud
            
        Returns:
            Score de similitud si >= threshold, o 0.0
        """
        if not self.is_available() or concept_key not in self._canonical_embeddings:
            return 0.0
        
        embedding = self.get_embedding(text)
        if embedding is None:
            return 0.0
        
        canonical = self._canonical_embeddings[concept_key]
        score = self.cosine_similarity(embedding, canonical)
        
        return score if score >= threshold else 0.0

    def clear_cache(self):
        """Limpia el cache de embeddings de filas (entre documentos diferentes)."""
        self._row_cache.clear()

    @classmethod
    def reset(cls):
        """Resetea el singleton (para testing)."""
        cls._instance = None
        cls._initialized = False

    def generate_canonical_embeddings(self, output_path: str = None):
        """
        Genera los embeddings canónicos y los guarda en un archivo JSON.
        Solo necesita ejecutarse una vez (o cuando se agreguen nuevos conceptos).
        """
        if not self._client:
            raise RuntimeError("No se puede generar embeddings sin un cliente Gemini inicializado.")
        
        if output_path is None:
            output_path = os.path.join(
                os.path.dirname(__file__), "canonical_embeddings.json"
            )
        
        embeddings = {}
        for key, description in CONCEPTOS_CANONICOS.items():
            print(f"  Generando embedding para '{key}': \"{description}\"...")
            response = self._client.models.embed_content(
                model=self._model,
                contents=description,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
            )
            embeddings[key] = response.embeddings[0].values
        
        with open(output_path, "w") as f:
            json.dump(embeddings, f)
        
        print(f"\n✅ {len(embeddings)} embeddings canónicos guardados en {output_path}")
        self._canonical_embeddings = embeddings
        return embeddings
