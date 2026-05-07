from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from app.models.projections import ProyeccionSupuestosRequest, ProyeccionBalanceRequest
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
            supuestos_impuestos=payload.impuestos
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
            "utilidad_neta": res_proy["utilidad_neta"]
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
        # 1. Extraer datos crudos del periodo base (PDF del Balance General)
        print(f"\n-> Analizando PDF base con Azure (Balance General)...")
        ocr_data = await _azure_service.process_financial_document_async(payload.results_url)
        print(f"   ✅ OCR completado. Tablas encontradas: {len(ocr_data.get('tables_data', []))}")

        # 2. Calcular la proyección
        print(f"\n-> Calculando proyección de Balance General (FER / Plug Account)...")
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
            inflacion_esperada=payload.inflacion_esperada
        )

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

