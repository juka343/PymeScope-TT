from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
import json
import asyncio
import traceback
from google import genai
from google.genai import types
from app.models.projections import (
    ProyeccionSupuestosRequest, 
    ProyeccionBalanceRequest, 
    LineaSupuesto,
    SolicitudAnalisisFER,
    RespuestaFERIA
)
from app.services.azure_document_service import AzureDocumentService
from app.services.projection_calculator import ProjectionCalculator
from app.services.firebase_service import FirebaseDBManager
from app.core.config import settings

router = APIRouter()
_azure_service = AzureDocumentService()
_projection_calculator = ProjectionCalculator()
_db_manager = FirebaseDBManager()

_is_initialized = False

def _ensure_firebase_initialized() -> None:
    global _is_initialized
    if _is_initialized:
        return
    if not settings.FIREBASE_CREDENTIALS_PATH:
        raise HTTPException(status_code=500, detail="FIREBASE_CREDENTIALS_PATH is not set.")
    _db_manager.inicializar_app(settings.FIREBASE_CREDENTIALS_PATH, settings.FIREBASE_STORAGE_BUCKET)
    _is_initialized = True


def _resolver_montos_a_pct(
    supuestos: List[LineaSupuesto],
    ocr_data: dict,
    calculator,
    periodo_base: str = None,
    inflacion_esperada: float = 0.0,
    es_balance: bool = False
) -> List[LineaSupuesto]:
    """
    Para supuestos que traen monto en lugar de variacion,
    extrae el valor_base del OCR y calcula el % equivalente.
    Regla de 3: % = ((monto / valor_base) - 1) * 100
    Si no encuentra valor_base -> mantener_igual=True (congela la cuenta).
    """
    tablas_ocr = ocr_data.get("tables_data", [])
    target_col = calculator._detectar_columna_periodo(tablas_ocr, periodo_base)
    resueltos = []

    for sup in supuestos:
        if sup.monto is not None and not sup.mantener_igual:
            if sup.monto == 0:
                # Usuario escribió $0 explícitamente -> proyectar la cuenta a $0
                # Se traduce en variacion=-100% para que el motor calcule:
                # base x (1 + (-100)/100) = base x 0 = $0
                resueltos.append(LineaSupuesto(
                    concepto=sup.concepto,
                    variacion=-100.0,
                    mantener_igual=False,
                    monto=sup.monto
                ))
                continue
            
            # ── Caso especial: Ventas netas usa keywords propios del motor ──
            if sup.concepto == "Ventas netas / Ingresos por servicios":
                tablas_ocr_data = {"tables_data": tablas_ocr}
                valor_base = calculator._get_exact_first(tablas_ocr_data, "ing por servicios", target_col_index=target_col)
                if valor_base is None:
                    valor_base = calculator._get_exact_first(tablas_ocr_data, "ingresos por servicios", target_col_index=target_col)
                if valor_base is None:
                    valor_base = calculator._get_exact_first(tablas_ocr_data, "ingresos", target_col_index=target_col)
            else:
                # ── Resto de cuentas — usar concept_keywords ──
                kw = calculator.concept_keywords.get(sup.concepto, [sup.concepto.lower()])
                valor_base = None
                for keyword in kw:
                    resultado = calculator._get_exact_first(
                        {"tables_data": tablas_ocr},
                        keyword,
                        target_col_index=target_col
                    )
                    if resultado is not None:
                        valor_base = resultado
                        break
                if valor_base is None:
                    # Fallback sin restricción de columna — _find_value tiene su propia
                    # lógica de detección. Riesgo bajo: solo afecta PDFs comparativos
                    # sin header donde _get_exact_first también falló.
                    valor_base = calculator._find_value(
                        tablas_ocr, kw,
                        take_last=False
                    )

            if valor_base and abs(float(valor_base)) > 0:
                if es_balance:
                    # BG: solve_balance_rubro NO multiplica inflación
                    # Fórmula inversa exacta: pct = (monto/base - 1) * 100
                    pct = ((sup.monto / float(valor_base)) - 1) * 100
                else:
                    # ER: solve_rubro SÍ multiplica inflación en CASO 3
                    # Fórmula inversa exacta: pct = (monto/base/(1+infl/100) - 1) * 100
                    inflacion_factor = 1 + (inflacion_esperada / 100)
                    pct = ((sup.monto / float(valor_base) / inflacion_factor) - 1) * 100
                pct = round(pct, 4)
                print(f"  \U0001f4b1 Monto->%: '{sup.concepto}' "
                      f"base={float(valor_base):,.2f} "
                      f"monto={sup.monto:,.2f} -> {pct:.4f}%")
                resueltos.append(LineaSupuesto(
                    concepto=sup.concepto,
                    variacion=pct,
                    mantener_igual=False,
                    monto=sup.monto
                ))
            else:
                print(f"  \u26a0\ufe0f Monto->%: '{sup.concepto}' "
                      f"sin valor base en PDF -- se congela")
                resueltos.append(LineaSupuesto(
                    concepto=sup.concepto,
                    variacion=0.0,
                    mantener_igual=True,
                    monto=sup.monto
                ))
        else:
            resueltos.append(sup)

    return resueltos

@router.post("/projections/estado-resultados")
async def generar_proyeccion_estado_resultados(payload: ProyeccionSupuestosRequest) -> Dict[str, Any]:
    """
    Recibe los supuestos del Frontend, extrae datos base del PDF y devuelve la proyección.
    Nota: Es un endpoint stateless, no guarda en BD (el Front se encarga de eso).
    """
    print(f"\n{'='*60}")
    print(f"  PROYECCIÓN - Proyecto: {payload.project_id}")
    print(f"  Periodo proyectado: {payload.periodo_proyectado_label}")
    print(f"  Inflación esperada: {payload.inflacion_esperada}%")
    print(f"  Periodo base (dinámico): {payload.periodo_base}")
    print(f"{'='*60}")

    try:
        # 1. Extraer datos crudos del periodo base (PDF del Estado de Resultados)
        print(f"\n-> Analizando PDF base con Azure...")
        print(f"   URL: {payload.results_url[:80]}...")
        ocr_data = await _azure_service.process_financial_document_async(payload.results_url)
        print(f"   ✅ OCR completado. Tablas encontradas: {len(ocr_data.get('tables_data', []))}")

        payload.ingresos = _resolver_montos_a_pct(
            payload.ingresos, ocr_data, _projection_calculator,
            payload.periodo_base,
            inflacion_esperada=payload.inflacion_esperada,
            es_balance=False
        )
        payload.costos = _resolver_montos_a_pct(
            payload.costos, ocr_data, _projection_calculator,
            payload.periodo_base,
            inflacion_esperada=payload.inflacion_esperada,
            es_balance=False
        )

        # 2. Calcular la proyección
        print(f"\n-> Calculando proyección matemática (Porcentaje de Ventas)...")
        res_proy = _projection_calculator.calcular_proyeccion_edo_resultados(
            ocr_data=ocr_data,
            supuestos_ingresos=payload.ingresos,
            supuestos_costos=payload.costos,
            supuestos_impuestos=payload.impuestos,
            inflacion_esperada=payload.inflacion_esperada,
            periodo_base=payload.periodo_base
        )

        filas_proyectadas = res_proy["tablas_proyectadas"]

        # 3. Mostrar resultados detallados en consola
        print(f"\n{'─'*60}")
        print(f"  RESULTADOS DE PROYECCIÓN")
        print(f"{'─'*60}")
        print(f"  {'Concepto':<42} {'Base':>12} {'Var%':>6} {'Proyectado':>14}")
        print(f"  {'─'*42} {'─'*12} {'─'*6} {'─'*14}")
        for fila in filas_proyectadas:
            base = f"${fila['valor_base']:>12,.2f}"
            var  = f"{fila['variacion_aplicada']:>5.1f}%"
            proy = f"${fila['valor_proyectado']:>12,.2f}"
            flag = " [=]" if fila['variacion_aplicada'] == 0.0 else ""
            print(f"  {fila['concepto']:<42} {base} {var} {proy}{flag}")
        
        print(f"{'─'*60}")
        print(f"  {'Utilidad Bruta:':<42} ${res_proy['utilidad_bruta']:>25,.2f}")
        print(f"  {'Utilidad Operativa:':<42} ${res_proy['utilidad_operativa']:>25,.2f}")
        print(f"  {'Utilidad antes Impuestos:':<42} ${res_proy['utilidad_antes_impuestos']:>25,.2f}")
        print(f"  {'Impuestos (ISR):':<42} ${res_proy['impuestos_totales']:>25,.2f}")
        print(f"  {'UTILIDAD NETA:':<42} ${res_proy['utilidad_neta']:>25,.2f}")
        print(f"{'='*60}\n")

        # 4. Retornar los resultados al Frontend (Endpoint Stateless)
        return {
            "estatus": "Completado",
            "project_id": payload.project_id,
            "periodo_base_id": payload.period_id,
            "tablas_proyectadas": filas_proyectadas,
            "ventas": res_proy["ventas"],
            "utilidad_bruta": res_proy["utilidad_bruta"],
            "utilidad_operativa": res_proy["utilidad_operativa"],
            "utilidad_antes_impuestos": res_proy["utilidad_antes_impuestos"],
            "impuestos": res_proy["impuestos"],
            "impuestos_totales": res_proy["impuestos_totales"],
            "utilidad_neta": res_proy["utilidad_neta"],
            "utilidad_neta_base": res_proy.get("utilidad_neta_base", 0.0)
        }

    except Exception as e:
        print(f"\n❌ Error en proyección ER: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en motor de proyecciones (ER): {str(e)}")


@router.post("/projections/balance-general")
async def generar_proyeccion_balance_general(payload: ProyeccionBalanceRequest) -> Dict[str, Any]:
    """
    Recibe los supuestos del Balance General, extrae datos base del PDF y devuelve la proyección.
    Persiste los datos en Firestore (subcolección proyecciones).
    """
    print(f"\n{'='*60}")
    print(f"  PROYECCIÓN BALANCE - Proyecto: {payload.project_id}")
    print(f"  Periodo proyectado: {payload.periodo_proyectado_label}")
    print(f"  Inflación esperada: {payload.inflacion_esperada}%")
    print(f"{'='*60}")

    try:
        # --- INYECCIÓN AUTOMÁTICA DE DEPRECIACIÓN ---
        # Si el Frontend no envía la Depreciación Acumulada, la inyectamos silenciosamente
        # para que el motor la busque en el PDF, reste el valor histórico y el FER cuadre.
        tiene_dep = any("depreciaci" in sup.concepto.lower() for sup in payload.activo_no_circulante)
        if not tiene_dep:
            payload.activo_no_circulante.append(
                LineaSupuesto(
                    concepto="Depreciación acumulada",
                    variacion=0.0,
                    mantener_igual=True
                )
            )

        # 1. Extraer datos crudos del periodo base (PDF del Balance General)
        print(f"\n-> Analizando PDF base con Azure (Balance General)...")
        ocr_data = await _azure_service.process_financial_document_async(payload.results_url)
        print(f"   ✅ OCR completado. Tablas encontradas: {len(ocr_data.get('tables_data', []))}")

        payload.activo_circulante    = _resolver_montos_a_pct(payload.activo_circulante,    ocr_data, _projection_calculator, es_balance=True)
        payload.activo_no_circulante = _resolver_montos_a_pct(payload.activo_no_circulante, ocr_data, _projection_calculator, es_balance=True)
        payload.pasivo_corto_plazo   = _resolver_montos_a_pct(payload.pasivo_corto_plazo,   ocr_data, _projection_calculator, es_balance=True)
        payload.pasivo_largo_plazo   = _resolver_montos_a_pct(payload.pasivo_largo_plazo,   ocr_data, _projection_calculator, es_balance=True)
        payload.capital_contribuido  = _resolver_montos_a_pct(payload.capital_contribuido,  ocr_data, _projection_calculator, es_balance=True)
        payload.capital_ganado       = _resolver_montos_a_pct(payload.capital_ganado,       ocr_data, _projection_calculator, es_balance=True)

        # 2. Calcular la proyección
        print(f"\n-> Calculando proyección de Balance General (FER / Plug Account)...")
        try:
            res_proy = _projection_calculator.calcular_proyeccion_balance(
                ocr_data=ocr_data,
                activo_circulante=payload.activo_circulante,
                activo_no_circulante=payload.activo_no_circulante,
                pasivo_corto_plazo=payload.pasivo_corto_plazo,
                pasivo_largo_plazo=payload.pasivo_largo_plazo,
                capital_contribuido=payload.capital_contribuido,
                capital_ganado=payload.capital_ganado,
                utilidad_neta_proforma=payload.utilidad_neta_proforma,
                ventas_proy_incremento_pct=payload.ventas_proy_incremento_pct,
                inflacion_esperada=payload.inflacion_esperada,
                total_impuestos_proforma=payload.total_impuestos_proforma,
                utilidad_neta_base=payload.utilidad_neta_base,
                periodicidad=payload.periodicidad
            )
        except Exception as e:
            traceback.print_exc()  # ← imprime el traceback completo en la terminal uvicorn
            raise e

        filas_proyectadas = res_proy["tablas_proyectadas"]

        # 3. Mostrar resultados detallados en consola (Estilo consistente con ER)
        print(f"\n{'─'*42} {'─'*12} {'─'*6} {'─'*14}")
        for fila in filas_proyectadas:
            base = f"${fila['valor_base']:>12,.2f}"
            var  = f"{fila['variacion_aplicada']:>5.1f}%"
            proy = f"${fila['valor_proyectado']:>12,.2f}"
            flag = " [=]" if fila['variacion_aplicada'] == 0.0 else ""
            print(f"  {fila['concepto']:<42} {base} {var} {proy}{flag}")
        
        print(f"{'─'*60}")
        print(f"  {'Total Activo:':<42} ${res_proy['total_activo']:>25,.2f}")
        print(f"  {'Total Pasivo:':<42} ${res_proy['total_pasivo']:>25,.2f}")
        print(f"  {'Total Capital:':<42} ${res_proy['total_capital']:>25,.2f}")
        print(f"{'─'*60}")
        print(f"  {'FONDOS EXTERNOS REQUERIDOS (FER):':<42} ${res_proy['fer']:>25,.2f}")
        print(f"{'='*60}\n")

        # 4. Retornar resultados al Frontend (Endpoint Stateless)
        return {
            "estatus": "Completado",
            "project_id": payload.project_id,
            "tablas_proyectadas": filas_proyectadas,
            "total_activo": res_proy["total_activo"],
            "total_pasivo": res_proy["total_pasivo"],
            "total_capital": res_proy["total_capital"],
            "fer": res_proy["fer"],
            "utilidad_neta_proforma": payload.utilidad_neta_proforma
        }

    except Exception as e:
        print(f"\n❌ Error en proyección de balance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en motor de proyecciones (Balance): {str(e)}")

# --- ENDPOINTS PARA IA (PROYECCIONES) ---

def _build_fer_ai_system_prompt() -> str:
    return """
Eres un intérprete financiero. Tu trabajo es explicarle a un dueño de PyME el resultado de su Balance General Proforma, enfocándote EXCLUSIVAMENTE en el FER (Fondos Externos Requeridos).

PRINCIPIOS ESTRICTOS ANTI-ALUCINACIÓN:
- Interpretas SOLO los números que te dan. ESTÁ ESTRICTAMENTE PROHIBIDO inventar porcentajes, tendencias, o cifras que no estén en el payload.
- Todo tu análisis, alertas y recomendaciones deben girar en torno al FER y a las cuentas clave proporcionadas.
- Si no tienes datos suficientes de una cuenta, no la menciones.
- Tu tono es directo y profesional, sin jerga financiera compleja.
- Devuelves JSON puro sin markdown.

LOGICA DE ANALISIS DEL FER:
- FER = Total Activos - (Total Pasivos + Total Capital)
- FER > 0 significa que los activos proyectados superan lo que la empresa puede financiar con sus propios recursos y deudas actuales. Necesita fondos externos.
- FER < 0 significa que la empresa genera más financiamiento del que necesita. Habrá excedente de efectivo.
- FER = 0 es el equilibrio perfecto.
- La brecha entre Utilidad Neta Proforma y el FER revela si las ganancias proyectadas son suficientes para autofinanciar el crecimiento.
"""

def _build_fer_ai_user_prompt(analysis_payload: Dict[str, Any]) -> str:
    fer = analysis_payload.get("fer", 0)
    utilidad = analysis_payload.get("utilidad_neta_proforma", 0)
    total_activo = analysis_payload.get("total_activo", 0)
    total_pasivo = analysis_payload.get("total_pasivo", 0)
    total_capital = analysis_payload.get("total_capital", 0)
    ventas_pct = analysis_payload.get("ventas_proy_incremento_pct", 0)

    fer_status = "DÉFICIT" if fer > 0.01 else ("EXCEDENTE" if fer < -0.01 else "EQUILIBRADO")
    brecha_utilidad_fer = utilidad - abs(fer) if fer > 0 else 0

    activo_circ = analysis_payload.get("activo_circulante", [])
    pasivo_cp = analysis_payload.get("pasivo_corto_plazo", [])
    capital_cuentas = analysis_payload.get("capital", [])

    def fmt_cuentas(lista):
        if not lista:
            return "  (sin cuentas registradas)"
        return "\n".join(
            f"  - {c['cuenta']}: base ${c['base']:,.0f} → proyectado ${c['proyectado']:,.0f}"
            for c in lista
        )

    return f"""
INTERPRETA los siguientes resultados del Balance General Proforma. No inventes datos fuera de los proporcionados.

=== RESUMEN EJECUTIVO ===
- Crecimiento de ventas proyectado: {ventas_pct}%
- Utilidad Neta Proforma generada: ${utilidad:,.2f}
- Total Activos proyectados: ${total_activo:,.2f}
- Total Pasivos proyectados: ${total_pasivo:,.2f}
- Total Capital proyectado: ${total_capital:,.2f}
- FER (Fondos Externos Requeridos): ${fer:,.2f} → Estado: {fer_status}
{f'- La utilidad generada ({utilidad:,.2f}) cubre {abs(brecha_utilidad_fer / fer * 100):.0f}% del deficit FER.' if fer > 0.01 and fer != 0 else ''}

=== CUENTAS CLAVE DEL ACTIVO CIRCULANTE ===
{fmt_cuentas(activo_circ)}

=== CUENTAS CLAVE DEL PASIVO A CORTO PLAZO ===
{fmt_cuentas(pasivo_cp)}

=== CAPITAL ===
{fmt_cuentas(capital_cuentas)}

GENERA el JSON estrictamente apegado a estos datos (NO INVENTES PORCENTAJES):
- "summary": 1 frase corta y directa que diga el impacto real del FER en el negocio (incluye el monto exacto del FER).
- "paragraph": 1 solo párrafo de máximo 2 oraciones. Explica POR QUE ocurre el FER conectando la Utilidad Neta con el crecimiento de activos/pasivos.
- "alerts": 1 o 2 alertas concretas basadas EXCLUSIVAMENTE en las cuentas mostradas arriba y su relación con el FER.
- "recommendations": 2 o 3 acciones tácticas CONCRETAS para gestionar el FER (cubrir déficit o usar excedente), justificadas SOLO con las cifras provistas.
"""

@router.post("/projections/fer-ai-analysis")
async def generar_analisis_fer_ia(payload: SolicitudAnalisisFER) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")

    print(f"\n-> Generando diagnóstico FER Inteligente para proyecto {payload.project_id}...")

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        system_prompt = _build_fer_ai_system_prompt()
        user_prompt = _build_fer_ai_user_prompt(payload.analysis_payload)

        def call_gemini():
            return client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=RespuestaFERIA,
                    temperature=0.2,
                ),
            )

        response = await asyncio.to_thread(call_gemini)

        if getattr(response, "parsed", None):
            result_dict = response.parsed.model_dump() if hasattr(response.parsed, 'model_dump') else response.parsed.dict()
        else:
            result_dict = json.loads(response.text)

        print("   ✅ Análisis FER generado con éxito.")
        return {
            "estatus": "Completado",
            "project_id": payload.project_id,
            "ai_result": result_dict,
        }

    except Exception as e:
        error_text = str(e)
        print(f"   ❌ Error generando análisis FER IA: {error_text}")
        
        if "503" in error_text or "overloaded" in error_text:
            raise HTTPException(status_code=503, detail="Gemini está temporalmente saturado. Intenta nuevamente.")
            
        raise HTTPException(status_code=500, detail=f"Error en Gemini: {error_text}")
