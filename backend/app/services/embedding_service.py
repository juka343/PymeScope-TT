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
    # === Rentabilidad (Estado de Resultados — NIF B-3) ===
    # NIF B-3: "Ventas o Ingresos netos" — primer renglón del estado de resultados.
    "ventas_netas": (
        "Ventas netas, ingresos netos, ingresos operativos o facturación total de la empresa. "
        "Incluye: ventas totales, total ingresos, ingresos por servicios. "
        "NO incluye: utilidad bruta, utilidad de operación, utilidad neta."
    ),
    # NIF B-3: "Utilidad / pérdida del ejercicio" — último renglón después de impuestos.
    "utilidad_neta": (
        "Utilidad neta, resultado neto, utilidad del ejercicio o resultado final después de impuestos. "
        "Incluye: utilidad neta consolidada, ganancia neta, remanente del ejercicio. "
        "NO incluye: utilidad de operación, utilidad antes de impuestos, ingresos totales."
    ),
    # NIF B-3: subtotal entre utilidad de operación e impuestos.
    "utilidad_antes_impuestos": (
        "Utilidad antes de impuestos a la utilidad, resultado antes de ISR y PTU. "
        "Incluye: utilidad antes del impuesto sobre la renta, resultado antes de impuestos. "
        "NO incluye: utilidad neta (que ya descontó impuestos), utilidad de operación."
    ),
    # NIF B-3: "Impuestos a la utilidad" — ISR y PTU.
    "impuestos": (
        "ISR, impuesto sobre la renta, PTU o impuestos a la utilidad. "
        "Incluye: provisión de ISR, impuestos y PTU. "
        "NO incluye: IVA, impuestos por recuperar, impuestos al activo."
    ),

    # === Liquidez (Balance General — NIF B-6) ===
    # NIF B-6: clasificación "Corto plazo, circulante o corriente" del Activo.
    "activo_circulante": (
        "Total activo circulante, activos corrientes a corto plazo. "
        "Incluye: efectivo, cuentas por cobrar, inventarios, activos a corto plazo. "
        "Es la suma del ACTIVO corriente — NO del pasivo circulante."
    ),
    # NIF B-6: clasificación "A corto plazo" del Pasivo.
    "pasivo_circulante": (
        "Total pasivo circulante, pasivos corrientes a corto plazo. "
        "Incluye: proveedores, deudas a corto plazo, pasivos corrientes. "
        "Es la suma del PASIVO corriente — NO del activo circulante."
    ),
    # NIF B-6: cuenta "Inventarios" dentro del activo circulante.
    "inventario": "Inventarios, mercancías, almacén o existencias de productos para venta.",

    # === Endeudamiento (Balance General — NIF B-6) ===
    # NIF B-6: total estructural del Estado de Situación Financiera.
    "activo_total": (
        "Total de activos, suma del activo, activo total de la empresa. "
        "Es la suma del activo circulante más el activo no circulante (fijo). "
        "NO confundir con activo circulante ni activo fijo por separado."
    ),
    # NIF B-6: clasificación "Capital contribuido + Capital ganado".
    "capital_contable": (
        "Capital contable total, patrimonio neto, hacienda pública o recursos propios de los accionistas. "
        "Incluye: capital social más utilidades acumuladas y reservas."
    ),
    # NIF B-6: total estructural del Pasivo.
    "pasivo_total": (
        "Pasivo total, suma del pasivo, total de deudas y obligaciones de la empresa. "
        "Es la suma del pasivo circulante más el pasivo a largo plazo. "
        "NO confundir con pasivo circulante ni 'total pasivo + capital'."
    ),
    # NIF B-3: subtotal entre utilidad bruta y resultado financiero.
    "utilidad_operacion": (
        "Utilidad de operación, resultado operativo o ganancia operativa. "
        "Incluye: utilidad (pérdida) de operación, resultado de operación. "
        "NO incluye: ventas netas, ingresos totales, utilidad antes de impuestos."
    ),
    "gastos_financieros": (
        "Gastos financieros, costo integral de financiamiento o resultado integral de financiamiento. "
        "Incluye: intereses a cargo, gastos de financiamiento."
    ),

    # === Rotación (Balance General + Estado de Resultados) ===
    # NIF B-6: "Cuentas por cobrar a clientes".
    "cuentas_por_cobrar": "Cuentas por cobrar a clientes, deudores comerciales o cartera de clientes.",
    # NIF B-3: "Costo de ventas".
    "costo_de_ventas": "Costo de ventas, costo de lo vendido, costo de servicios prestados o costo de mercancía vendida.",
    # NIF B-6: "Propiedades, planta y equipo (activo fijo)".
    "activo_fijo": (
        "Activo fijo neto, propiedad planta y equipo, activo no circulante o activo a largo plazo. "
        "Incluye: maquinaria, equipo, terrenos, edificios (neto de depreciación)."
    ),

    # === Estructura (Balance General — NIF B-6) ===
    # NIF B-6: cuenta "Capital social" dentro de Capital contribuido.
    "capital_social": (
        "Capital social, capital aportado o contribuido por los socios o accionistas. "
        "Incluye: capital social fijo, capital social variable, aportaciones de socios. "
        "NO incluye: utilidades acumuladas, reservas, capital contable total."
    ),
    # NIF B-6: clasificación "A largo plazo" del Pasivo.
    "pasivo_largo_plazo": (
        "Pasivo a largo plazo, pasivo no circulante o deuda a largo plazo. "
        "Incluye: préstamos bancarios LP, pasivo fijo, créditos a largo plazo."
    ),
}


# ─── Anti-Conceptos ──────────────────────────────────────────────────────────
# Pares de conceptos cuya redacción se confunde en el OCR. Cuando el embedding
# de una fila apunta a `concept_key`, si también puntúa alto contra alguno de
# sus anti-conceptos, se penaliza el score para evitar matches cruzados.
ANTI_CONCEPTOS: Dict[str, List[str]] = {
    "activo_circulante":  ["pasivo_circulante"],
    "pasivo_circulante":  ["activo_circulante"],
    "utilidad_operacion": ["ventas_netas", "utilidad_neta"],
    "ventas_netas":       ["utilidad_operacion", "utilidad_neta"],
    "utilidad_neta":      ["utilidad_operacion", "utilidad_antes_impuestos"],
    "activo_total":       ["pasivo_total", "capital_contable"],
    "pasivo_total":       ["activo_total", "capital_contable"],
    "capital_contable":   ["capital_social", "pasivo_total"],
    "capital_social":     ["capital_contable"],
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

    def find_match_with_anticoncepts(
        self, text: str, concept_key: str
    ) -> Tuple[float, float, float]:
        """
        Calcula el score crudo del concepto, el score máximo de sus anti-conceptos
        y un score ajustado que penaliza la confusión entre pares conflictivos.

        Reusa un solo embedding por fila — no realiza llamadas Gemini extra.

        Returns:
            (score_raw, score_anti_max, score_adjusted)
            score_adjusted = score_raw - 0.5 * score_anti_max
        """
        if not self.is_available() or concept_key not in self._canonical_embeddings:
            return 0.0, 0.0, 0.0

        embedding = self.get_embedding(text)
        if embedding is None:
            return 0.0, 0.0, 0.0

        canonical = self._canonical_embeddings[concept_key]
        score_raw = self.cosine_similarity(embedding, canonical)

        score_anti_max = 0.0
        for anti_key in ANTI_CONCEPTOS.get(concept_key, []):
            anti_canonical = self._canonical_embeddings.get(anti_key)
            if anti_canonical is None:
                continue
            anti_score = self.cosine_similarity(embedding, anti_canonical)
            if anti_score > score_anti_max:
                score_anti_max = anti_score

        score_adjusted = score_raw - 0.5 * score_anti_max
        return score_raw, score_anti_max, score_adjusted

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
