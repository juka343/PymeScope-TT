"""
Suite de regresión del FinancialCalculator.

Para cada empresa de prueba verifica que:
  1. Los datos_crudos (valores absolutos extraídos) no cambien.
  2. Los KPIs (valores formateados + status) no cambien.

Modo de uso:
    cd backend
    pytest tests/test_regression_financial.py -v

Si un cambio en el código es INTENCIONAL y produce outputs distintos:
    python -m tests.generate_golden   # actualizar los golden files
    pytest tests/test_regression_financial.py -v  # confirmar que pasan
"""

import json
import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.financial_calculator import FinancialCalculator
from tests.conftest import ALL_CASES, GOLDEN_DIR

MODULOS = ["rentabilidad", "liquidez", "endeudamiento", "rotacion", "estructura"]


@pytest.fixture(scope="module")
def calc():
    c = FinancialCalculator()
    c._embedding_service = None  # Determinismo: solo keywords + math rescue
    return c


def _load_golden(case_name, modulo):
    path = os.path.join(GOLDEN_DIR, f"{case_name}_{modulo}.json")
    if not os.path.exists(path):
        pytest.skip(f"Golden file ausente: {path}. Ejecuta generate_golden.py primero.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _run_modulo(calc, modulo, cfg):
    b  = cfg["balance"]
    r  = cfg["resultados"]
    p  = cfg["periodicidad"]
    ci = cfg["col_index"]
    if modulo == "rentabilidad":
        return calc.calcular_rentabilidad(b, r, p, ci)
    if modulo == "liquidez":
        return calc.calcular_liquidez(b, p, ci)
    if modulo == "endeudamiento":
        return calc.calcular_endeudamiento(b, r, p, ci)
    if modulo == "rotacion":
        return calc.calcular_rotacion(b, r, p, ci)
    if modulo == "estructura":
        return calc.calcular_estructura(b, p, ci)
    raise ValueError(f"Módulo desconocido: {modulo}")


# ─── Genera los parámetros para @pytest.mark.parametrize ─────────────────────
_params = [
    (case_name, modulo)
    for case_name in ALL_CASES
    for modulo in MODULOS
]


@pytest.mark.parametrize("case_name,modulo", _params,
                         ids=[f"{c}::{m}" for c, m in _params])
def test_regression(calc, case_name, modulo):
    cfg    = ALL_CASES[case_name]
    golden = _load_golden(case_name, modulo)
    actual = _run_modulo(calc, modulo, cfg)

    # ── 1. Verificar datos_crudos (valores numéricos extraídos) ──────────────
    golden_datos = golden.get("datos_crudos", {})
    actual_datos = actual.get("datos_crudos", {})

    for key, expected_val in golden_datos.items():
        if key in ("multiplicador", "fuentes") or key.startswith("_"):
            continue  # no es un valor extraído, es configuración
        assert key in actual_datos, (
            f"[{case_name}::{modulo}] Falta clave en datos_crudos: '{key}'"
        )
        actual_val = actual_datos[key]
        assert abs(actual_val - expected_val) < 1.0, (
            f"[{case_name}::{modulo}] datos_crudos['{key}'] cambió: "
            f"esperado={expected_val}, actual={actual_val}"
        )

    # ── 2. Verificar KPIs (value + status) ──────────────────────────────────
    golden_kpis = {k["label"]: k for k in golden.get("kpis", [])}
    actual_kpis = {k["label"]: k for k in actual.get("kpis", [])}

    for label, golden_kpi in golden_kpis.items():
        assert label in actual_kpis, (
            f"[{case_name}::{modulo}] KPI desaparecido: '{label}'"
        )
        actual_kpi = actual_kpis[label]

        assert actual_kpi["value"] == golden_kpi["value"], (
            f"[{case_name}::{modulo}] KPI '{label}' valor cambió: "
            f"esperado='{golden_kpi['value']}', actual='{actual_kpi['value']}'"
        )
        assert actual_kpi["status"] == golden_kpi["status"], (
            f"[{case_name}::{modulo}] KPI '{label}' status cambió: "
            f"esperado='{golden_kpi['status']}', actual='{actual_kpi['status']}'"
        )


# ─── Conceptos esperados por módulo ──────────────────────────────────────────
_FUENTES_ESPERADAS = {
    "rentabilidad":  {"utilidad_neta", "ventas_netas", "activo_total", "capital_contable"},
    "liquidez":      {"activo_circulante", "pasivo_circulante", "inventario"},
    "endeudamiento": {"pasivo_total", "activo_total", "capital_contable", "utilidad_operacion", "gastos_financieros", "utilidad_neta", "impuestos"},
    "rotacion":      {"cuentas_por_cobrar", "inventario", "activo_fijo", "activo_total", "ventas_netas", "costo_de_ventas"},
    "estructura":    {"activo_total", "pasivo_total", "capital_social", "capital_contable", "activo_fijo", "pasivo_largo_plazo", "pasivo_circulante"},
}

# Usamos un solo caso representativo (cocacola) para validar la forma de fuentes
_FUENTES_CASE = "cocacola"


@pytest.mark.parametrize("modulo", MODULOS)
def test_fuentes_presentes(calc, modulo):
    """Verifica que datos_crudos incluye 'fuentes' con las claves NIF esperadas."""
    cfg    = ALL_CASES[_FUENTES_CASE]
    result = _run_modulo(calc, modulo, cfg)
    datos  = result.get("datos_crudos", {})

    assert "fuentes" in datos, f"[{modulo}] 'fuentes' ausente en datos_crudos"

    fuentes = datos["fuentes"]
    assert isinstance(fuentes, dict), f"[{modulo}] 'fuentes' debe ser un dict"
    assert len(fuentes) > 0, f"[{modulo}] 'fuentes' está vacío"

    for concepto in _FUENTES_ESPERADAS[modulo]:
        assert concepto in fuentes, f"[{modulo}] Concepto '{concepto}' ausente en fuentes"
        entrada = fuentes[concepto]
        assert "norma" in entrada, f"[{modulo}][{concepto}] Falta campo 'norma'"
        assert "cuenta_nif" in entrada, f"[{modulo}][{concepto}] Falta campo 'cuenta_nif'"
        assert entrada["norma"].startswith("NIF"), f"[{modulo}][{concepto}] 'norma' no es NIF: {entrada['norma']}"


# ─── Test perfiles de formato ────────────────────────────────────────────────
def _make_sabana_table(n_cols: int = 12):
    """Genera una tabla sintética con una fila de ventas y n_cols valores mensuales."""
    cells = [{"row": 0, "col": 0, "text": "Ventas netas"}]
    for i in range(n_cols):
        cells.append({"row": 0, "col": i + 1, "text": str((i + 1) * 10_000)})
    return {"tables_data": [cells]}


def test_perfil_sabana_mensual_vs_corporativo_bmv():
    """corporativo_bmv con col_index=0 en tabla de 12 columnas lee lista[0], NO el francotirador."""
    calc = FinancialCalculator()
    calc._embedding_service = None

    tabla = _make_sabana_table(12)

    # sabana_mensual con col_index=0, periodicidad trimestral → suma Q1 (cols 0,1,2) = 10k+20k+30k
    calc._current_periodicidad = "trimestral"
    calc._current_formato_perfil = "sabana_mensual"
    result_sabana = calc.calcular_rentabilidad(tabla, tabla, periodicidad="trimestral", col_index=0, formato_perfil="sabana_mensual")
    ventas_sabana = result_sabana["datos_crudos"]["ventas_netas"]

    # corporativo_bmv con col_index=0, mismo periodicidad → lee lista[0] = 10k (sin sumar)
    result_bmv = calc.calcular_rentabilidad(tabla, tabla, periodicidad="trimestral", col_index=0, formato_perfil="corporativo_bmv")
    ventas_bmv = result_bmv["datos_crudos"]["ventas_netas"]

    assert ventas_sabana != ventas_bmv, (
        f"sabana_mensual y corporativo_bmv deben producir valores distintos con 12 columnas; "
        f"sabana={ventas_sabana}, bmv={ventas_bmv}"
    )
    assert ventas_bmv == 10_000, f"corporativo_bmv col_index=0 debe leer el primer valor (10000), obtuvo {ventas_bmv}"


# ─── Test detección de periodos por columna (Fase 8) ─────────────────────────
@pytest.mark.parametrize("texto,esperado", [
    ("2024", "2024"),
    ("Enero 2024", "2024-01"),
    ("ene 2024", "2024-01"),
    ("Dic 2023", "2023-12"),
    ("Diciembre 2022", "2022-12"),
    ("1T24", "2024-Q1"),
    ("Q1 2024", "2024-Q1"),
    ("4T 2023", "2023-Q4"),
    ("2024-03", "2024-03"),
    ("03/2024", "2024-03"),
    ("Trimestre 2 2024", "2024-Q2"),
    ("Cuenta", None),
    ("", None),
    ("Total", None),
])
def test_parse_period_label(texto, esperado):
    calc = FinancialCalculator()
    assert calc._parse_period_label(texto) == esperado


def test_detect_period_columns_comparativo_anual():
    """Documento con 3 años en columnas → mapa {año: data_col_index}.

    Índice posicional entre columnas de periodo (0,1,2…), alineado con _find_value.
    """
    calc = FinancialCalculator()
    tabla = [
        {"row": 0, "col": 0, "text": "Cuenta"},
        {"row": 0, "col": 1, "text": "2024"},
        {"row": 0, "col": 2, "text": "2023"},
        {"row": 0, "col": 3, "text": "2022"},
        {"row": 1, "col": 0, "text": "Ventas"},
        {"row": 1, "col": 1, "text": "100"},
        {"row": 1, "col": 2, "text": "90"},
        {"row": 1, "col": 3, "text": "80"},
    ]
    detected = calc._detect_period_columns([tabla])
    assert detected == {"2024": 0, "2023": 1, "2022": 2}


def test_detect_period_columns_header_multifila():
    """Header con mes en una fila y año en la siguiente → combina."""
    calc = FinancialCalculator()
    tabla = [
        {"row": 0, "col": 1, "text": "Enero"},
        {"row": 0, "col": 2, "text": "Febrero"},
        {"row": 0, "col": 3, "text": "Marzo"},
        {"row": 1, "col": 1, "text": "2024"},
        {"row": 1, "col": 2, "text": "2024"},
        {"row": 1, "col": 3, "text": "2024"},
    ]
    detected = calc._detect_period_columns([tabla])
    assert detected == {"2024-01": 0, "2024-02": 1, "2024-03": 2}


def test_detect_period_columns_corporativo_bmv():
    """Comparativo trimestral típico BMV: trimestre actual vs anterior."""
    calc = FinancialCalculator()
    tabla = [
        {"row": 0, "col": 0, "text": "Concepto"},
        {"row": 0, "col": 1, "text": "4T 2024"},
        {"row": 0, "col": 2, "text": "4T 2023"},
    ]
    detected = calc._detect_period_columns([tabla])
    assert detected == {"2024-Q4": 0, "2023-Q4": 1}
