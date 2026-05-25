import os
import base64
import tempfile
import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

from app.core.config import settings
from app.services.firebase_service import FirebaseDBManager
from app.services.azure_document_service import AzureDocumentService
from app.services.financial_calculator import FinancialCalculator

# Servicios
router = APIRouter()
_db_manager = FirebaseDBManager()
_azure_service = AzureDocumentService()
_calculator = FinancialCalculator()

# Variable global para la inicialización de firebase
_is_initialized = False


def _build_period_key(period_date: str, periodicidad: str) -> Optional[str]:
    """Reconstruye la clave del periodo (mismo formato que el frontend) para
    cruzar contra la salida de _detect_period_columns.

    Ejemplos:
      anual + "2024-03"  -> "2024"
      mensual + "2024-03" -> "2024-03"
      trimestral + "2024-03" -> "2024-Q1"
    """
    if not period_date:
        return None
    p = (periodicidad or "").lower().strip()
    if p == "anual":
        m = re.search(r"\b(20\d{2})\b", str(period_date))
        return m.group(1) if m else None
    parts = str(period_date).split("-")
    if len(parts) < 2:
        return None
    year = parts[0]
    month = parts[1].zfill(2)
    if p == "mensual":
        return f"{year}-{month}"
    if p == "trimestral":
        try:
            q = (int(month) + 2) // 3
        except ValueError:
            return None
        return f"{year}-Q{q}"
    return None


def _ensure_firebase_initialized() -> None:
    global _is_initialized

    if _is_initialized:
        return

    credenciales_path = settings.FIREBASE_CREDENTIALS_PATH

    firebase_base64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")

    if firebase_base64:
        temp_path = os.path.join(
            tempfile.gettempdir(),
            "firebase-service-account.json"
        )

        with open(temp_path, "wb") as f:
            f.write(base64.b64decode(firebase_base64))

        credenciales_path = temp_path

    if not credenciales_path:
        raise HTTPException(
            status_code=500,
            detail="No se configuró FIREBASE_CREDENTIALS_PATH ni FIREBASE_SERVICE_ACCOUNT_BASE64."
        )

    if not settings.FIREBASE_STORAGE_BUCKET:
        raise HTTPException(
            status_code=500,
            detail="No se configuró FIREBASE_STORAGE_BUCKET."
        )

    _db_manager.inicializar_app(
        credenciales_path,
        settings.FIREBASE_STORAGE_BUCKET,
    )

    _is_initialized = True


# --- CONSTANTES IA ---

REQUIRED_FINANCIAL_BLOCKS = [
    {"block_key": "rentabilidad", "block_name": "Rentabilidad"},
    {"block_key": "liquidez", "block_name": "Liquidez"},
    {"block_key": "endeudamiento", "block_name": "Endeudamiento"},
    {"block_key": "rotacion", "block_name": "Rotación de Activos"},
    {"block_key": "estructura", "block_name": "Estructura Financiera"},
]


INTERNAL_STATUS_REPLACEMENTS = {
    "ok": "nivel saludable",
    "warn": "nivel de atención",
    "danger": "situación crítica",
    "status": "evaluación",
}


# --- MODELOS DE DATOS ---

# Modelo viejo, revisar después si quitar...
class SolicitudProcesamientoAzure(BaseModel):
    project_id: str
    period_id: str
    file_uuid: str
    file_url: str
    file_type: str


# Nuevo modelo
class SolicitudAnalisisPeriodo(BaseModel):
    project_id: str
    period_id: str
    balance_url: str
    resultados_url: str
    periodicidad: str
    col_index: int = 0  # legacy; usado si los duales no vienen
    col_index_balance: Optional[int] = None
    col_index_resultados: Optional[int] = None
    formato_perfil: str = "vertical_simple"
    period_date: str = ""
    period_label: str = ""


# Modelo para solicitar análisis con IA
class SolicitudAnalisisIA(BaseModel):
    project_id: str
    analysis_payload: Dict[str, Any]


# --- MODELOS DE RESPUESTA IA ---

class ExecutiveSummaryIA(BaseModel):
    overall_status: str
    title: str
    summary: str
    paragraphs: List[str]


class TrendSummaryIA(BaseModel):
    positive_trends: List[str]
    negative_trends: List[str]


class IndicatorExplanationIA(BaseModel):
    label: str
    value: str
    reading: str
    meaning: str
    service_business_implication: str
    possible_impact: str


class BlockInterpretationIA(BaseModel):
    block_key: str
    block_name: str
    status: str
    title: str
    interpretation: str
    paragraphs: List[str]
    main_findings: List[str]
    indicators_explained: List[IndicatorExplanationIA]


class KeyImplicationIA(BaseModel):
    title: str
    indicator: str
    value: str
    reading: str
    implication: str
    possible_impact: str


class AlertIA(BaseModel):
    severity: str
    block_key: str
    indicator_key: Optional[str] = None
    title: str
    message: str
    evidence: str
    implication: str


class RecommendationIA(BaseModel):
    priority: str
    block_key: str
    title: str
    description: str
    reason: str
    related_indicators: List[str]
    expected_impact: str


class RecommendationByBlockItemIA(BaseModel):
    title: str
    description: str
    reason: str
    priority: str
    expected_impact: str


class RecommendationsByBlockIA(BaseModel):
    block_key: str
    block_name: str
    title: str
    recommendations: List[RecommendationByBlockItemIA]


class RespuestaAnalisisFinancieroIA(BaseModel):
    executive_summary: ExecutiveSummaryIA
    trend_summary: TrendSummaryIA
    key_implications: List[KeyImplicationIA]
    block_interpretations: List[BlockInterpretationIA]
    alerts: List[AlertIA]
    alerts_by_block: List[AlertIA]
    recommendations: List[RecommendationIA]
    recommendations_by_block: List[RecommendationsByBlockIA]
    data_quality_notes: List[str]
    disclaimer: str


def validate_document_date(text: str, period_date: str, periodicity: str, doc_name: str, period_label: str):
    if not text or not period_date:
        return
        
    text_lower = text.lower()
    parts = period_date.split("-")
    year = parts[0]
    year_short = year[2:]  # "2025" -> "25"
    
    if periodicity.lower() == "anual":
        if not re.search(r'\b' + year + r'\b', text_lower):
            raise ValueError(f"DATE_MISMATCH|{doc_name}|{year}|{period_label}")

    elif periodicity.lower() == "trimestral":
        month = parts[1] if len(parts) > 1 else ""
        if not month:
            return

        month_int = int(month)
        quarter = (month_int - 1) // 3 + 1  # 01-03→1, 04-06→2, 07-09→3, 10-12→4

        # Meses que componen cada trimestre
        quarter_months_map = {
            1: {"start": "01", "end": "03"},
            2: {"start": "04", "end": "06"},
            3: {"start": "07", "end": "09"},
            4: {"start": "10", "end": "12"},
        }
        q_info = quarter_months_map[quarter]

        # Nombres de todos los meses del trimestre para buscar en el texto
        all_months = {
            "01": ["enero", "january", "jan", "ene"],
            "02": ["febrero", "february", "feb"],
            "03": ["marzo", "march", "mar"],
            "04": ["abril", "april", "abr", "apr"],
            "05": ["mayo", "may"],
            "06": ["junio", "june", "jun"],
            "07": ["julio", "july", "jul"],
            "08": ["agosto", "august", "ago", "aug"],
            "09": ["septiembre", "september", "sep"],
            "10": ["octubre", "october", "oct"],
            "11": ["noviembre", "november", "nov"],
            "12": ["diciembre", "december", "dic", "dec"],
        }

        # Recolectar nombres de los 3 meses del trimestre
        q_month_names = []
        for m in range(int(q_info["start"]), int(q_info["end"]) + 1):
            q_month_names.extend(all_months.get(f"{m:02d}", []))

        # Nombres ordinales del trimestre en español
        ordinal_names = {
            1: ["primer", "1er", "primero", "first"],
            2: ["segundo", "2do", "2°", "second"],
            3: ["tercer", "3er", "tercero", "third"],
            4: ["cuarto", "4to", "4°", "fourth"],
        }

        # Patrones de detección trimestral (cualquiera que coincida es suficiente)
        found = False

        # Patrón 1: Formato corporativo "1T25", "1T2025", "1T 25", "1T 2025"
        # Nota: No usamos \b entre el dígito y la T porque "1t25" es alfanumérico continuo
        corp_pattern = r'(?<!\w)' + str(quarter) + r't\s*(?:' + year + r'|' + year_short + r')(?!\w)'
        if re.search(corp_pattern, text_lower):
            found = True

        # Patrón 2: Formato internacional "Q1 2025", "Q1 25", "Q12025"
        if not found:
            intl_pattern = r'(?<!\w)q' + str(quarter) + r'\s*(?:' + year + r'|' + year_short + r')(?!\w)'
            if re.search(intl_pattern, text_lower):
                found = True

        # Para los siguientes patrones, verificamos que el año exista en el documento
        if not found:
            year_found = bool(re.search(r'\b' + year + r'\b', text_lower)) or bool(re.search(r'(?<!\d)' + year_short + r'(?!\d)', text_lower))
            if not year_found:
                raise ValueError(f"DATE_MISMATCH|{doc_name}|Q{quarter} {year}|{period_label}")

        # Patrón 3: Texto en español "primer trimestre", "1er trimestre", "trimestre 1"
        if not found:
            ordinals = ordinal_names.get(quarter, [])
            for ordinal in ordinals:
                if re.search(re.escape(ordinal) + r'\s+trimestre', text_lower):
                    found = True
                    break
                if re.search(r'trimestre\s+' + re.escape(ordinal), text_lower):
                    found = True
                    break
            # También: "trimestre 1", "trimestre 2", etc.
            if not found and re.search(r'trimestre\s+' + str(quarter) + r'\b', text_lower):
                found = True

        # Patrón 4: Rango de meses "enero a marzo", "enero-marzo", "ene-mar", "de enero a marzo"
        if not found:
            start_names = all_months.get(q_info["start"], [])
            end_names = all_months.get(q_info["end"], [])
            for s_name in start_names:
                for e_name in end_names:
                    range_pattern = r'\b' + re.escape(s_name) + r'\s*(?:a|al|-|–)\s*' + re.escape(e_name) + r'\b'
                    if re.search(range_pattern, text_lower):
                        found = True
                        break
                if found:
                    break

        # Patrón 5: Cualquier mes del trimestre mencionado junto con el año
        # (ej. "Mar, 2025", "marzo 2025", "mar 2025")
        if not found:
            any_month_pattern = r'\b(' + '|'.join(q_month_names) + r')\.?,?\s*(?:de\s*|del\s*)?' + r'(?:' + year + r'|' + year_short + r')\b'
            if re.search(any_month_pattern, text_lower):
                found = True

        # Patrón 6: Formato numérico (ej. "31/03/2026", "2026-03-31")
        if not found:
            months_str = '|'.join([f"{m:02d}" for m in range(int(q_info["start"]), int(q_info["end"]) + 1)])
            numeric_date_pattern = r'\b\d{1,2}[/-](' + months_str + r')[/-](?:' + year + r'|' + year_short + r')\b'
            numeric_date_pattern_2 = r'\b(?:' + year + r'|' + year_short + r')[/-](' + months_str + r')[/-]\d{1,2}\b'
            if re.search(numeric_date_pattern, text_lower) or re.search(numeric_date_pattern_2, text_lower):
                found = True

        if not found:
            raise ValueError(f"DATE_MISMATCH|{doc_name}|Q{quarter} {year}|{period_label}")

    elif periodicity.lower() == "semestral":
        month = parts[1] if len(parts) > 1 else ""
        if not month:
            return

        month_int = int(month)
        semester = 1 if month_int <= 6 else 2

        all_months = {
            "01": ["enero", "january", "jan", "ene"],
            "02": ["febrero", "february", "feb"],
            "03": ["marzo", "march", "mar"],
            "04": ["abril", "april", "abr", "apr"],
            "05": ["mayo", "may"],
            "06": ["junio", "june", "jun"],
            "07": ["julio", "july", "jul"],
            "08": ["agosto", "august", "ago", "aug"],
            "09": ["septiembre", "september", "sep"],
            "10": ["octubre", "october", "oct"],
            "11": ["noviembre", "november", "nov"],
            "12": ["diciembre", "december", "dic", "dec"],
        }

        sem_range = range(1, 7) if semester == 1 else range(7, 13)
        s_month_names = []
        for m in sem_range:
            s_month_names.extend(all_months.get(f"{m:02d}", []))

        start_month = "01" if semester == 1 else "07"
        end_month = "06" if semester == 1 else "12"

        ordinal_sem = {
            1: ["primer", "1er", "primero", "first"],
            2: ["segundo", "2do", "2°", "second"],
        }

        found = False

        # Patrón 1: "1S25", "1S2025"
        corp_pattern = r'(?<!\w)' + str(semester) + r's\s*(?:' + year + r'|' + year_short + r')(?!\w)'
        if re.search(corp_pattern, text_lower):
            found = True

        # Patrón 2: "H1 2025" (half)
        if not found:
            intl_pattern = r'(?<!\w)h' + str(semester) + r'\s*(?:' + year + r'|' + year_short + r')(?!\w)'
            if re.search(intl_pattern, text_lower):
                found = True

        # Para los siguientes patrones, verificamos que el año exista en el documento
        if not found:
            year_found = bool(re.search(r'\b' + year + r'\b', text_lower)) or bool(re.search(r'(?<!\d)' + year_short + r'(?!\d)', text_lower))
            if not year_found:
                raise ValueError(f"DATE_MISMATCH|{doc_name}|S{semester} {year}|{period_label}")

        # Patrón 3: "primer semestre", "1er semestre", "semestre 1"
        if not found:
            ordinals = ordinal_sem.get(semester, [])
            for ordinal in ordinals:
                if re.search(re.escape(ordinal) + r'\s+semestre', text_lower):
                    found = True
                    break
                if re.search(r'semestre\s+' + re.escape(ordinal), text_lower):
                    found = True
                    break
            if not found and re.search(r'semestre\s+' + str(semester) + r'\b', text_lower):
                found = True

        # Patrón 4: Rango de meses "enero a junio", "julio-diciembre"
        if not found:
            start_names = all_months.get(start_month, [])
            end_names = all_months.get(end_month, [])
            for s_name in start_names:
                for e_name in end_names:
                    range_pattern = r'\b' + re.escape(s_name) + r'\s*(?:a|al|-|–)\s*' + re.escape(e_name) + r'\b'
                    if re.search(range_pattern, text_lower):
                        found = True
                        break
                if found:
                    break

        # Patrón 5: Cualquier mes del semestre + año
        if not found:
            any_month_pattern = r'\b(' + '|'.join(s_month_names) + r')\.?,?\s*(?:de\s*|del\s*)?' + r'(?:' + year + r'|' + year_short + r')\b'
            if re.search(any_month_pattern, text_lower):
                found = True

        # Patrón 6: Formato numérico (ej. "30/06/2026", "2026-06-30")
        if not found:
            months_str = '|'.join([f"{m:02d}" for m in sem_range])
            numeric_date_pattern = r'\b\d{1,2}[/-](' + months_str + r')[/-](?:' + year + r'|' + year_short + r')\b'
            numeric_date_pattern_2 = r'\b(?:' + year + r'|' + year_short + r')[/-](' + months_str + r')[/-]\d{1,2}\b'
            if re.search(numeric_date_pattern, text_lower) or re.search(numeric_date_pattern_2, text_lower):
                found = True

        if not found:
            raise ValueError(f"DATE_MISMATCH|{doc_name}|S{semester} {year}|{period_label}")

    else:
        # Mensual (lógica original sin cambios)
        month = parts[1] if len(parts) > 1 else ""
        months = {
            "01": ["enero", "january", "jan", "ene"],
            "02": ["febrero", "february", "feb"],
            "03": ["marzo", "march", "mar"],
            "04": ["abril", "april", "abr", "apr"],
            "05": ["mayo", "may"],
            "06": ["junio", "june", "jun"],
            "07": ["julio", "july", "jul"],
            "08": ["agosto", "august", "ago", "aug"],
            "09": ["septiembre", "september", "sep"],
            "10": ["octubre", "october", "oct"],
            "11": ["noviembre", "november", "nov"],
            "12": ["diciembre", "december", "dic", "dec"]
        }
        month_names = months.get(month, [])
        if not month_names:
            return
            
        month_pattern = r'\b(' + '|'.join(month_names) + r')\.?'
        middle_pattern = r'\s*(?:\d{1,2}\s*,?\s*)?(?:de\s*|del\s*)?'
        pattern = month_pattern + middle_pattern + year + r'\b'
        
        numeric_month = str(int(month)) if month.isdigit() else month
        numeric_month_padded = month
        numeric_pattern = r'(?<!\d[\/\-])\b(?:' + numeric_month + r'|' + numeric_month_padded + r')[\/\-]' + year + r'\b'
        
        full_date_pattern = r'\b(?:al|de|del|periodo|mes)\s*(?:3[01]|[12][0-9]|0?[1-9])[\/\-](?:' + numeric_month + r'|' + numeric_month_padded + r')[\/\-]' + year + r'\b'
        
        if not re.search(pattern, text_lower) and not re.search(numeric_pattern, text_lower) and not re.search(full_date_pattern, text_lower):
            expected_month_name = month_names[0].capitalize()
            raise ValueError(f"DATE_MISMATCH|{doc_name}|{expected_month_name} {year}|{period_label}")

# --- HELPERS IA ---

def _pydantic_to_dict(parsed_result: Any) -> Dict[str, Any]:
    """
    Convierte una respuesta parseada de Pydantic a dict.
    Compatible con Pydantic v1 y v2, porque la vida ya tiene suficientes errores.
    """
    if hasattr(parsed_result, "model_dump"):
        return parsed_result.model_dump()

    if hasattr(parsed_result, "dict"):
        return parsed_result.dict()

    if isinstance(parsed_result, dict):
        return parsed_result

    return json.loads(json.dumps(parsed_result, default=lambda o: o.__dict__))


def _replace_internal_words_in_text(text: str) -> str:
    """
    Evita que lleguen al frontend palabras internas como ok/warn/danger/status.
    """
    if not isinstance(text, str):
        return text

    clean = text

    replacements = {
        r"\bok\b": "nivel saludable",
        r"\bOK\b": "nivel saludable",
        r"\bwarn\b": "nivel de atención",
        r"\bWARN\b": "nivel de atención",
        r"\bdanger\b": "situación crítica",
        r"\bDANGER\b": "situación crítica",
        r"\bstatus\b": "evaluación",
        r"\bSTATUS\b": "evaluación",
    }

    for pattern, replacement in replacements.items():
        clean = re.sub(pattern, replacement, clean)

    return clean


def _sanitize_ai_strings(value: Any) -> Any:
    """
    Recorre toda la respuesta de Gemini y limpia textos.
    No cambia nombres de llaves, solo valores string.
    """
    if isinstance(value, str):
        return _replace_internal_words_in_text(value)

    if isinstance(value, list):
        return [_sanitize_ai_strings(item) for item in value]

    if isinstance(value, dict):
        return {key: _sanitize_ai_strings(item) for key, item in value.items()}

    return value


def _find_first_by_block(items: List[Dict[str, Any]], block_key: str) -> Optional[Dict[str, Any]]:
    for item in items:
        if item.get("block_key") == block_key:
            return item
    return None


def _ensure_complete_ai_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Garantiza que existan los 5 bloques principales:
    - block_interpretations
    - alerts_by_block
    - recommendations_by_block

    Si Gemini omite uno, lo rellenamos con contenido neutral.
    Porque confiar ciegamente en una IA es una excelente forma de fabricar bugs con moño.
    """
    if not isinstance(result, dict):
        return result

    result.setdefault("executive_summary", {})
    result.setdefault("trend_summary", {"positive_trends": [], "negative_trends": []})
    result.setdefault("key_implications", [])
    result.setdefault("block_interpretations", [])
    result.setdefault("alerts", [])
    result.setdefault("alerts_by_block", [])
    result.setdefault("recommendations", [])
    result.setdefault("recommendations_by_block", [])
    result.setdefault("data_quality_notes", [])
    result.setdefault(
        "disclaimer",
        "Este análisis se basa exclusivamente en la información financiera proporcionada y no sustituye asesoría contable, fiscal, legal o financiera profesional.",
    )

    block_interpretations = result.get("block_interpretations") or []
    alerts = result.get("alerts") or []
    alerts_by_block = result.get("alerts_by_block") or []
    recommendations = result.get("recommendations") or []
    recommendations_by_block = result.get("recommendations_by_block") or []

    complete_block_interpretations = []
    complete_alerts_by_block = []
    complete_recommendations_by_block = []

    for block in REQUIRED_FINANCIAL_BLOCKS:
        block_key = block["block_key"]
        block_name = block["block_name"]

        existing_interpretation = _find_first_by_block(block_interpretations, block_key)

        if existing_interpretation:
            complete_block_interpretations.append(existing_interpretation)
        else:
            complete_block_interpretations.append(
                {
                    "block_key": block_key,
                    "block_name": block_name,
                    "status": "sin alerta crítica identificada",
                    "title": f"Lectura general de {block_name}",
                    "interpretation": (
                        f"No se identificó una alerta crítica específica para {block_name} con los datos disponibles. "
                        "Aun así, este bloque debe revisarse junto con los demás indicadores para entender el desempeño financiero integral."
                    ),
                    "paragraphs": [
                        (
                            f"El bloque de {block_name} no presentó una observación prioritaria dentro del análisis automático. "
                            "Esto no significa que deba ignorarse, sino que su lectura debe hacerse en conjunto con la tendencia general."
                        ),
                        (
                            "En una empresa de servicios, los indicadores financieros suelen estar conectados: presión en rentabilidad, liquidez o rotación puede reflejarse después en capacidad de pago, inversión operativa o crecimiento."
                        ),
                    ],
                    "main_findings": [
                        "No se detectó una alerta prioritaria específica para este bloque.",
                        "Se recomienda revisar su evolución frente al resto de razones financieras.",
                    ],
                    "indicators_explained": [],
                }
            )

        existing_alert = _find_first_by_block(alerts_by_block, block_key) or _find_first_by_block(alerts, block_key)

        if existing_alert:
            complete_alerts_by_block.append(existing_alert)
        else:
            complete_alerts_by_block.append(
                {
                    "severity": "baja",
                    "block_key": block_key,
                    "indicator_key": None,
                    "title": f"Sin alerta crítica en {block_name}",
                    "message": (
                        f"No se identificó una señal crítica específica en {block_name}. "
                        "Conviene mantener seguimiento para detectar cambios en periodos posteriores."
                    ),
                    "evidence": "No se identificó evidencia suficiente para clasificar una alerta mayor en este bloque.",
                    "implication": (
                        "El bloque debe monitorearse como parte del seguimiento financiero general, especialmente si otros indicadores muestran deterioro."
                    ),
                }
            )

        existing_recommendation_block = _find_first_by_block(recommendations_by_block, block_key)

        if existing_recommendation_block:
            complete_recommendations_by_block.append(existing_recommendation_block)
        else:
            block_recommendations = [
                rec for rec in recommendations if rec.get("block_key") == block_key
            ]

            if block_recommendations:
                complete_recommendations_by_block.append(
                    {
                        "block_key": block_key,
                        "block_name": block_name,
                        "title": f"Recomendaciones para {block_name}",
                        "recommendations": [
                            {
                                "title": rec.get("title", "Recomendación"),
                                "description": rec.get("description", ""),
                                "reason": rec.get("reason", ""),
                                "priority": rec.get("priority", "media"),
                                "expected_impact": rec.get("expected_impact", ""),
                            }
                            for rec in block_recommendations[:3]
                        ],
                    }
                )
            else:
                complete_recommendations_by_block.append(
                    {
                        "block_key": block_key,
                        "block_name": block_name,
                        "title": f"Recomendaciones para {block_name}",
                        "recommendations": [
                            {
                                "title": "Mantener seguimiento periódico",
                                "description": (
                                    f"Revisar la evolución de {block_name} en cada nuevo periodo para detectar desviaciones relevantes."
                                ),
                                "reason": (
                                    "Aunque no se identificó una alerta prioritaria, el seguimiento evita reaccionar tarde ante cambios financieros."
                                ),
                                "priority": "baja",
                                "expected_impact": (
                                    "Mayor control financiero y mejor capacidad para anticipar ajustes operativos."
                                ),
                            }
                        ],
                    }
                )

    result["block_interpretations"] = complete_block_interpretations
    result["alerts_by_block"] = complete_alerts_by_block
    result["recommendations_by_block"] = complete_recommendations_by_block

    # Para compatibilidad con vistas que lean alerts/recommendations generales.
    # Dejamos alerts/recommendations como resumen general, pero aseguramos que no estén vacíos.
    if not result["alerts"]:
        result["alerts"] = complete_alerts_by_block

    if not result["recommendations"]:
        flattened_recommendations = []

        for block_rec in complete_recommendations_by_block:
            for rec in block_rec.get("recommendations", []):
                flattened_recommendations.append(
                    {
                        "priority": rec.get("priority", "media"),
                        "block_key": block_rec.get("block_key"),
                        "title": rec.get("title", "Recomendación"),
                        "description": rec.get("description", ""),
                        "reason": rec.get("reason", ""),
                        "related_indicators": [],
                        "expected_impact": rec.get("expected_impact", ""),
                    }
                )

        result["recommendations"] = flattened_recommendations[:5]

    return _sanitize_ai_strings(result)


def _build_financial_ai_system_prompt() -> str:
    return """
Actúa como analista financiero especializado en PyMEs del sector servicios en México.

Tu objetivo no es solo repetir indicadores, sino explicar qué significan y qué implican para la operación del negocio.

Contexto sectorial:
- El análisis se enfoca en empresas de servicios.
- En servicios, la rentabilidad depende mucho de precios, costos operativos, productividad del personal, capacidad instalada, cobranza y control de gastos.
- La liquidez es clave porque muchas empresas de servicios pueden vender, pero tardar en cobrar.
- La rotación de activos puede ser menor que en comercio o manufactura, pero aun así debe explicar si los activos están ayudando o no a generar ingresos.
- El inventario puede no ser central en servicios. Si aparece inventario, interprétalo sin asumir que es el principal motor del negocio.

Reglas obligatorias:
1. Usa únicamente los datos proporcionados.
2. No recalcules indicadores.
3. No inventes información faltante.
4. No uses palabras internas como "ok", "warn", "danger" o "status".
5. Traduce los estados internos de esta forma:
   - ok = "nivel saludable", "situación favorable", "dentro de un rango adecuado"
   - warn = "nivel de atención", "por debajo de lo recomendable", "área vulnerable"
   - danger = "situación crítica", "riesgo elevado", "deterioro importante"
6. Para cada indicador relevante explica:
   - valor observado
   - si es alto, bajo o adecuado
   - qué significa financieramente
   - qué implicación tiene para una empresa de servicios
   - qué efecto podría tener en liquidez, rentabilidad, operación, crecimiento o capacidad de pago
7. Evita frases genéricas como "mejorar costos" si no explicas por qué.
8. No seas alarmista. Usa tono profesional, claro y práctico.
9. Usa párrafos breves.
10. No devuelvas texto corrido enorme. Devuelve secciones estructuradas.
11. Debes analizar exactamente estos cinco bloques:
    - rentabilidad
    - liquidez
    - endeudamiento
    - rotacion
    - estructura
12. No omitas ningún bloque.
13. Debes devolver exactamente una entrada por cada bloque en:
    - block_interpretations
    - alerts_by_block
    - recommendations_by_block
14. Si un bloque no tiene alerta grave, genera una alerta de severidad "baja" explicando que debe mantenerse en monitoreo.
15. recommendations_by_block debe contener mínimo una recomendación para cada bloque.
16. alerts puede contener las alertas generales más importantes.
17. recommendations puede contener las recomendaciones generales más importantes.
18. executive_summary.paragraphs debe tener párrafos breves para mostrarse con saltos de línea en frontend.
19. executive_summary.summary debe ser una versión breve compatible con pantallas existentes.
20. No incluyas Markdown. No uses viñetas con guiones dentro de strings. Solo JSON válido.
"""


def _build_financial_ai_user_prompt(analysis_payload: Dict[str, Any]) -> str:
    payload_json = json.dumps(analysis_payload, ensure_ascii=False, indent=2)

    return f"""
Analiza el siguiente JSON financiero limpio.

Necesito una respuesta JSON estructurada para un dashboard financiero multiperiodo.

Recuerda:
- Explica implicaciones, no solo describas si algo está alto o bajo.
- Enfoca la interpretación en empresas de servicios.
- No uses palabras internas como ok, warn, danger o status.
- Incluye obligatoriamente los cinco bloques: rentabilidad, liquidez, endeudamiento, rotacion y estructura.
- No omitas endeudamiento aunque no sea el bloque más problemático.
- Si un bloque se ve estable, explícalo como seguimiento preventivo.

JSON de entrada:
{payload_json}
"""


# --- ENDPOINTS ---

@router.post("/documents/analyze-period")
async def analizar_periodo_completo(payload: SolicitudAnalisisPeriodo) -> Dict[str, Any]:
    _ensure_firebase_initialized()

    print(f"Iniciando análisis cruzado para el periodo: {payload.period_id}")

    try:
        # 1. Extraer datos crudos con Azure
        print("-> Extrayendo Balance General y estado de resultados...")

        balance_data, resultados_data = await asyncio.gather(
            _azure_service.process_financial_document_async(payload.balance_url),
            _azure_service.process_financial_document_async(payload.resultados_url),
        )

        try:
            validate_document_date(balance_data.get("text_content", ""), payload.period_date, payload.periodicidad, "Balance General", payload.period_label)
            validate_document_date(resultados_data.get("text_content", ""), payload.period_date, payload.periodicidad, "Estado de Resultados", payload.period_label)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Resolución de col_index dual: si vienen los duales se usan; si no, fallback al legacy.
        idx_balance = payload.col_index_balance if payload.col_index_balance is not None else payload.col_index
        idx_resultados = payload.col_index_resultados if payload.col_index_resultados is not None else payload.col_index

        # Detección temprana de columnas + alerta de asimetría
        columnas_balance = _calculator._detect_period_columns(_calculator._get_tables(balance_data))
        columnas_resultados = _calculator._detect_period_columns(_calculator._get_tables(resultados_data))
        periodo_key = _build_period_key(payload.period_date, payload.periodicidad)
        warning_periodo: Optional[str] = None
        if periodo_key:
            en_balance = periodo_key in columnas_balance
            en_resultados = periodo_key in columnas_resultados
            if en_balance and not en_resultados and columnas_resultados:
                warning_periodo = (
                    f"El periodo '{periodo_key}' aparece en el Balance pero no en el Estado de Resultados. "
                    "Los KPIs que mezclan ambos documentos pueden estar cruzando periodos distintos."
                )
            elif en_resultados and not en_balance and columnas_balance:
                warning_periodo = (
                    f"El periodo '{periodo_key}' aparece en el Estado de Resultados pero no en el Balance. "
                    "Los KPIs que mezclan ambos documentos pueden estar cruzando periodos distintos."
                )

        # 2. Calcular indicadores financieros
        print(f"-> Calculando indicadores financieros (col_index balance={idx_balance}, resultados={idx_resultados})...")

        analisis_rentabilidad = _calculator.calcular_rentabilidad(
            balance_data,
            resultados_data,
            periodicidad=payload.periodicidad,
            col_index_balance=idx_balance,
            col_index_resultados=idx_resultados,
            formato_perfil=payload.formato_perfil,
        )

        analisis_liquidez = _calculator.calcular_liquidez(
            balance_data,
            periodicidad=payload.periodicidad,
            col_index_balance=idx_balance,
            formato_perfil=payload.formato_perfil,
        )

        analisis_endeudamiento = _calculator.calcular_endeudamiento(
            balance_data,
            resultados_data,
            periodicidad=payload.periodicidad,
            col_index_balance=idx_balance,
            col_index_resultados=idx_resultados,
            formato_perfil=payload.formato_perfil,
        )

        analisis_rotacion = _calculator.calcular_rotacion(
            balance_data,
            resultados_data,
            periodicidad=payload.periodicidad,
            col_index_balance=idx_balance,
            col_index_resultados=idx_resultados,
            formato_perfil=payload.formato_perfil,
        )

        analisis_estructura = _calculator.calcular_estructura(
            balance_data,
            periodicidad=payload.periodicidad,
            col_index_balance=idx_balance,
            formato_perfil=payload.formato_perfil,
        )

        # 3. Retornar paquete listo para Dashboard de Vue
        respuesta = {
            "estatus": "Completado",
            "project_id": payload.project_id,
            "period_id": payload.period_id,
            "dashboard_data": {
                "rentabilidad": analisis_rentabilidad,
                "liquidez": analisis_liquidez,
                "endeudamiento": analisis_endeudamiento,
                "rotacion": analisis_rotacion,
                "estructura": analisis_estructura,
            },
            "columnas_detectadas": {
                "balance": columnas_balance,
                "resultados": columnas_resultados,
            },
        }
        if warning_periodo:
            respuesta["warning_periodo_asimetrico"] = warning_periodo
            print(f"  ⚠️  {warning_periodo}")
        return respuesta

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en análisis cruzado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando el periodo: {str(e)}",
        )


class SolicitudDetectarColumnas(BaseModel):
    balance_url: str
    resultados_url: str


@router.post("/documents/detect-columns")
async def detectar_columnas_periodo(payload: SolicitudDetectarColumnas) -> Dict[str, Any]:
    """Devuelve un mapa {periodo: col_index} por cada documento.

    El frontend puede consultar este endpoint ANTES de llamar /analyze-period
    para saber a qué columna corresponde cada año/mes/trimestre detectado en
    los headers y así enviar el col_index correcto.
    """
    _ensure_firebase_initialized()

    try:
        balance_data, resultados_data = await asyncio.gather(
            _azure_service.process_financial_document_async(payload.balance_url),
            _azure_service.process_financial_document_async(payload.resultados_url),
        )

        return {
            "balance": _calculator._detect_period_columns(_calculator._get_tables(balance_data)),
            "resultados": _calculator._detect_period_columns(_calculator._get_tables(resultados_data)),
        }
    except Exception as e:
        print(f"Error detectando columnas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error detectando columnas: {str(e)}",
        )


@router.post("/documents/financial-ai-analysis")
async def generar_analisis_financiero_ia(payload: SolicitudAnalisisIA) -> Dict[str, Any]:
    """
    Recibe el JSON limpio generado por el frontend, lo manda a Gemini
    y devuelve una interpretación financiera estructurada para el dashboard.
    """

    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")

    print(f"Generando análisis financiero con Gemini para proyecto: {payload.project_id}")

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        system_prompt = _build_financial_ai_system_prompt()
        user_prompt = _build_financial_ai_user_prompt(payload.analysis_payload)

        def call_gemini():
            return client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=RespuestaAnalisisFinancieroIA,
                    temperature=0.2,
                ),
            )
        response = await asyncio.to_thread(call_gemini)
        if getattr(response, "parsed", None):
            result_dict = _pydantic_to_dict(response.parsed)
        else:
            result_dict = json.loads(response.text)

        result_dict = _ensure_complete_ai_result(result_dict)

        return {
            "estatus": "Completado",
            "project_id": payload.project_id,
            "model": settings.GEMINI_MODEL,
            "ai_result": result_dict,
        }

    except Exception as e:
        error_text = str(e)
        print(f"Error generando análisis con Gemini: {error_text}")

        if (
            "503" in error_text
            or "UNAVAILABLE" in error_text
            or "high demand" in error_text
            or "overloaded" in error_text
        ):
            raise HTTPException(
                status_code=503,
                detail="Gemini está temporalmente saturado. Intenta nuevamente en unos minutos.",
            )

        if "API key not valid" in error_text or "API_KEY_INVALID" in error_text:
            raise HTTPException(
                status_code=401,
                detail="La API key de Gemini no es válida.",
            )

        raise HTTPException(
            status_code=500,
            detail=f"Error generando análisis con Gemini: {error_text}",
        )


# -----------------------------------------------------------------------------------------------------------
@router.post("/documents/process-azure")
async def procesar_documento_con_azure(payload: SolicitudProcesamientoAzure) -> Dict[str, Any]:
    """
    Recibe la URL de Firebase del Frontend, la envía a Azure,
    y devuelve la data extraída.
    """
    _ensure_firebase_initialized()

    print(f"Iniciando procesamiento Azure para: {payload.file_uuid}")

    try:
        # 1. Llamar al servicio de Azure
        # Nota: Asegúrate de que payload.file_url sea la URL descargable (https), no gs://
        resultado_azure = _azure_service.process_financial_document(payload.file_url)

        # 2. Guardar el resultado en Firebase automáticamente
        # _db_manager.actualizar_datos_ocr(payload.file_uuid, resultado_azure)

        # 3. Retornar al Frontend
        return {
            "uuid": payload.file_uuid,
            "estatus": "Procesado",
            "project_id": payload.project_id,
            "tipo": payload.file_type,
            "data": resultado_azure,
        }

    except Exception as e:
        print(f"Error procesando con Azure: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en motor de IA: {str(e)}",
        )