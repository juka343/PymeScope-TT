from fastapi import APIRouter, HTTPException
from typing import Any, Dict
import json
import asyncio
import traceback
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from google import genai
from google.genai import types
from app.models.projections import (
    ProyeccionSupuestosRequest, 
    ProyeccionBalanceRequest, 
    LineaSupuesto,
    SolicitudAnalisisFER,
    RespuestaFERIA,
    MultiPeriodoRequest,
    MultiPeriodoBGRequest,
    ERPeriodoResultado,
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
Eres un intérprete financiero. Tu trabajo es explicarle a un dueño de PyME el resultado de su Balance General Proforma en lenguaje sencillo.

PRINCIPIOS:
- Interpretas SOLO los números que te dan. No inventas cifras ni tendencias.
- Usas los campos numéricos del JSON para calcular diferencias, ratios y brechas.
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

GENERA el JSON con:
- "summary": 1 frase corta y directa que diga el impacto real del FER en el negocio (incluye el monto exacto del FER).
- "paragraph": 1 solo párrafo de máximo 2 oraciones. Explica POR QUE ocurre el FER usando los números (relación entre utilidad generada vs activos que crecieron). Sin repetir el FER como concepto.
- "alerts": 1 o 2 alertas concretas basadas en los datos de las cuentas anteriores.
- "recommendations": 2 o 3 acciones tácticas CONCRETAS para cubrir el déficit o usar el excedente, mencionando las cuentas específicas que lo justifican.
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

# ── ENDPOINT MULTIPERIODO ───────────────────────────────────────────────────

@router.post("/projections/multiperiodo")
async def generar_proyeccion_multiperiodo(payload: MultiPeriodoRequest):
    """
    Endpoint orquestador para proyecciones de hasta 5 periodos futuros.
    
    Flujo:
    1. Descarga OCR real de los PDFs base (ER y BG) una sola vez
    2. Para cada periodo: calcula ER → calcula BG
    3. Para trimestral/anual: construye OCR sintético para el siguiente periodo
    4. Para mensual: siempre usa el OCR real como base
    5. Retorna todos los periodos proyectados en una sola respuesta
    """
    try:
        resultados = []

        # ── PASO 1: Descargar OCR real UNA SOLA VEZ ────────────────────────
        print(f"\n-> Descargando OCR base para proyección multiperiodo...")
        print(f"   ER base: {payload.url_er_base}")
        print(f"   BG base: {payload.url_bg_base}")

        ocr_er = await _azure_service.process_financial_document_async(payload.url_er_base)
        ocr_bg = await _azure_service.process_financial_document_async(payload.url_bg_base)

        print(f"   ✅ OCR ER completado. Tablas: {len(ocr_er.get('tables_data', []))}")
        print(f"   ✅ OCR BG completado. Tablas: {len(ocr_bg.get('tables_data', []))}")

        # utilidad_neta_base viene del Firebase (guardada al generar el ER histórico)
        utilidad_neta_base_actual = payload.utilidad_neta_base

        # ── PASO 2: Bucle por cada periodo ─────────────────────────────────
        for i in range(payload.n_periodos):
            periodo_label = payload.periodos[i]
            col_er = payload.columnas_er[i]
            col_bg = payload.columnas_bg[i]

            print(f"\n-> Calculando periodo {i+1}/{payload.n_periodos}: {periodo_label}")

            # ── Calcular ER del periodo i ───────────────────────────────────
            er_result = _projection_calculator.calcular_proyeccion_edo_resultados(
                ocr_data=ocr_er,
                supuestos_ingresos=col_er.ingresos,
                supuestos_costos=col_er.costos,
                supuestos_impuestos=col_er.impuestos if col_er.impuestos else [],
                inflacion_esperada=col_er.inflacion_esperada,
                periodo_base=periodo_label,
            )

            print(f"   ✅ ER calculado. Utilidad neta: ${er_result.get('utilidad_neta', 0):,.2f}")

            # ── Calcular BG del periodo i ───────────────────────────────────
            bg_result = _projection_calculator.calcular_proyeccion_balance(
                ocr_data=ocr_bg,
                activo_circulante=col_bg.activo_circulante,
                activo_no_circulante=col_bg.activo_no_circulante,
                pasivo_corto_plazo=col_bg.pasivo_corto_plazo,
                pasivo_largo_plazo=col_bg.pasivo_largo_plazo,
                capital_contribuido=col_bg.capital_contribuido,
                capital_ganado=col_bg.capital_ganado,
                utilidad_neta_proforma=er_result.get("utilidad_neta", 0.0),
                ventas_proy_incremento_pct=col_er.ventas_incremento_pct,
                total_impuestos_proforma=er_result.get("impuestos_totales", 0.0),
                utilidad_neta_base=utilidad_neta_base_actual,
                periodicidad=payload.periodicidad,
                periodo_base=periodo_label,
            )

            print(f"   ✅ BG calculado. FER: ${bg_result.get('fer', 0):,.2f}")

            # ── Guardar resultado del periodo ───────────────────────────────
            resultados.append({
                "periodo": periodo_label,
                "numero": i + 1,
                "er": er_result,
                "bg": bg_result,
            })

            # ── PASO 3: Base rodante para trimestral y anual ────────────────
            if payload.periodicidad != "mensual":
                print(f"   -> Construyendo OCR sintético para siguiente periodo...")

                ocr_er = _projection_calculator.construir_ocr_sintetico(
                    tablas_proyectadas=er_result.get("tablas_proyectadas", []),
                    periodo_label=periodo_label
                )
                ocr_bg = _projection_calculator.construir_ocr_sintetico(
                    tablas_proyectadas=bg_result.get("tablas_proyectadas", []),
                    periodo_label=periodo_label
                )

                # Para anual: la utilidad base del siguiente periodo
                # es la utilidad neta proyectada del periodo actual
                if payload.periodicidad == "anual":
                    utilidad_neta_base_actual = er_result.get("utilidad_neta", 0.0)

                print(f"   ✅ OCR sintético construido para {periodo_label}")
            # Para mensual: ocr_er y ocr_bg no cambian — siempre el real

        print(f"\n✅ Proyección multiperiodo completada. {len(resultados)} periodos generados.")

        return {
            "success": True,
            "periodicidad": payload.periodicidad,
            "n_periodos": payload.n_periodos,
            "periodos_proyectados": resultados
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error en proyección multiperiodo: {str(e)}"
        )


# ── ENDPOINT MULTIPERIODO PASO 1: solo ER ──────────────────────────────────

@router.post("/projections/multiperiodo/er")
async def generar_multiperiodo_er(payload: MultiPeriodoRequest):
    """
    Paso 1 del flujo multiperiodo: calcula solo los ERs.
    El BG se calculará en un segundo paso cuando el usuario
    configure los supuestos del Balance General.
    """
    try:
        resultados_er = []

        print(f"\n-> [MULTI-ER] Descargando OCR base del ER...")
        ocr_er = await _azure_service.process_financial_document_async(payload.url_er_base)
        print(f"   [OK] OCR ER completado. Tablas: {len(ocr_er.get('tables_data', []))}")

        utilidad_neta_base_actual = payload.utilidad_neta_base

        for i in range(payload.n_periodos):
            periodo_label = payload.periodos[i]
            col_er = payload.columnas_er[i]

            print(f"\n-> [MULTI-ER] Calculando periodo {i+1}/{payload.n_periodos}: {periodo_label}")

            periodo_base_para_motor = (
                payload.periodo_base_label
                if str(payload.periodicidad).lower() == "mensual"
                else periodo_label
            )

            er_result = _projection_calculator.calcular_proyeccion_edo_resultados(
                ocr_data=ocr_er,
                supuestos_ingresos=col_er.ingresos,
                supuestos_costos=col_er.costos,
                supuestos_impuestos=col_er.impuestos if col_er.impuestos else [],
                inflacion_esperada=col_er.inflacion_esperada,
                periodo_base=periodo_base_para_motor,
            )

            print(f"\n{'='*60}")
            print(f"PERIODO {i+1}/{payload.n_periodos}: {periodo_label}")
            print(f"{'='*60}")
            print(f"  periodo_base_para_motor: '{periodo_base_para_motor}'")
            print(f"  ventas:                  ${er_result.get('ventas', 0):,.2f}")
            print(f"  costo_ventas:            ${er_result.get('costo_ventas', 0):,.2f}")
            print(f"  utilidad_bruta:          ${er_result.get('utilidad_bruta', 0):,.2f}")
            print(f"  gastos_operativos:       ${er_result.get('gastos_operativos', 0):,.2f}")
            print(f"  utilidad_operativa:      ${er_result.get('utilidad_operativa', 0):,.2f}")
            print(f"  gastos_financieros:      ${er_result.get('gastos_financieros', 0):,.2f}")
            print(f"  uai:                     ${er_result.get('utilidad_antes_impuestos', 0):,.2f}")
            print(f"  impuestos:               ${er_result.get('impuestos', 0):,.2f}")
            print(f"  utilidad_neta:           ${er_result.get('utilidad_neta', 0):,.2f}")
            print(f"  utilidad_neta_base:      ${er_result.get('utilidad_neta_base', 0):,.2f}")
            print(f"  tablas_count:            {len(er_result.get('tablas_proyectadas', []))}")
            print(f"{'='*60}\n")

            print(f"   [OK] ER calculado. Utilidad neta: ${er_result.get('utilidad_neta', 0):,.2f}")

            resultados_er.append({
                "periodo": periodo_label,
                "numero": i + 1,
                "er": er_result,
            })

            # Base rodante solo para trimestral y anual
            if payload.periodicidad != "mensual":
                ocr_er = _projection_calculator.construir_ocr_sintetico(
                    tablas_proyectadas=er_result.get("tablas_proyectadas", []),
                    periodo_label=periodo_label
                )
                if payload.periodicidad == "anual":
                    utilidad_neta_base_actual = er_result.get("utilidad_neta", 0.0)

        print(f"\n[OK] MULTI-ER Completado. {len(resultados_er)} periodos generados.")

        return {
            "success": True,
            "periodicidad": payload.periodicidad,
            "n_periodos": payload.n_periodos,
            "periodos_er": resultados_er
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error en proyección multiperiodo ER: {str(e)}"
        )


# ── ENDPOINT MULTIPERIODO PASO 2: solo BG ──────────────────────────────────

@router.post("/projections/multiperiodo/bg")
async def generar_multiperiodo_bg(payload: MultiPeriodoBGRequest):
    """
    Paso 2 del flujo multiperiodo: calcula los BGs usando los
    resultados del ER ya calculados en el paso 1.
    """
    try:
        resultados_bg = []

        print(f"\n-> [MULTI-BG] Descargando OCR base del BG...")
        ocr_bg = await _azure_service.process_financial_document_async(payload.url_bg_base)
        print(f"   [OK] OCR BG completado. Tablas: {len(ocr_bg.get('tables_data', []))}")

        utilidad_neta_base_actual = payload.utilidad_neta_base

        for i in range(payload.n_periodos):
            periodo_label = payload.periodos[i]
            col_bg = payload.columnas_bg[i]
            er_periodo = payload.resultados_er[i]

            print(f"\n-> [MULTI-BG] Calculando periodo {i+1}/{payload.n_periodos}: {periodo_label}")

            periodo_base_para_motor = (
                payload.periodo_base_label
                if str(payload.periodicidad).lower() == "mensual"
                else periodo_label
            )

            bg_result = _projection_calculator.calcular_proyeccion_balance(
                ocr_data=ocr_bg,
                activo_circulante=col_bg.activo_circulante,
                activo_no_circulante=col_bg.activo_no_circulante,
                pasivo_corto_plazo=col_bg.pasivo_corto_plazo,
                pasivo_largo_plazo=col_bg.pasivo_largo_plazo,
                capital_contribuido=col_bg.capital_contribuido,
                capital_ganado=col_bg.capital_ganado,
                utilidad_neta_proforma=er_periodo.utilidad_neta,
                ventas_proy_incremento_pct=0.0,
                total_impuestos_proforma=er_periodo.impuestos_totales,
                utilidad_neta_base=utilidad_neta_base_actual,
                periodicidad=payload.periodicidad,
                periodo_base=periodo_base_para_motor,
            )

            print(f"   [OK] BG calculado. FER: ${bg_result.get('fer', 0):,.2f}")

            resultados_bg.append({
                "periodo": periodo_label,
                "numero": i + 1,
                "bg": bg_result,
            })

            # Base rodante para trimestral y anual
            if payload.periodicidad != "mensual":
                ocr_bg = _projection_calculator.construir_ocr_sintetico(
                    tablas_proyectadas=bg_result.get("tablas_proyectadas", []),
                    periodo_label=periodo_label
                )
                if payload.periodicidad == "anual":
                    utilidad_neta_base_actual = er_periodo.utilidad_neta

        print(f"\n[OK] MULTI-BG Completado. {len(resultados_bg)} periodos generados.")

        return {
            "success": True,
            "periodicidad": payload.periodicidad,
            "n_periodos": payload.n_periodos,
            "periodos_bg": resultados_bg
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error en proyección multiperiodo BG: {str(e)}"
        )
