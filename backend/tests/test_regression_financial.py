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
        if key == "multiplicador":
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
