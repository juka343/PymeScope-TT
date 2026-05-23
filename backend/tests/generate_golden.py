"""
Genera los archivos JSON de referencia (golden files) usando el output ACTUAL
del FinancialCalculator.

Ejecutar UNA vez (o cuando se haga un cambio intencional y verificado):
    cd backend
    python -m tests.generate_golden

Los archivos se guardan en tests/golden/<caso>_<modulo>.json
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.financial_calculator import FinancialCalculator
from tests.conftest import ALL_CASES, GOLDEN_DIR

MODULOS = ["rentabilidad", "liquidez", "endeudamiento", "rotacion", "estructura"]

def _disable_embeddings(calc):
    """Desactiva el embedding service para pruebas deterministas."""
    calc._embedding_service = None


def _run_case(calc, case_name, cfg):
    balance = cfg["balance"]
    resultados = cfg["resultados"]
    p = cfg["periodicidad"]
    ci = cfg["col_index"]

    return {
        "rentabilidad": calc.calcular_rentabilidad(balance, resultados, p, ci),
        "liquidez":     calc.calcular_liquidez(balance, p, ci),
        "endeudamiento":calc.calcular_endeudamiento(balance, resultados, p, ci),
        "rotacion":     calc.calcular_rotacion(balance, resultados, p, ci),
        "estructura":   calc.calcular_estructura(balance, p, ci),
    }

def main():
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    calc = FinancialCalculator()
    _disable_embeddings(calc)  # Garantiza determinismo: solo keywords + math rescue

    for case_name, cfg in ALL_CASES.items():
        print(f"\n--- {case_name.upper()} ({cfg['periodicidad']}) ---")
        results = _run_case(calc, case_name, cfg)

        for modulo, output in results.items():
            path = os.path.join(GOLDEN_DIR, f"{case_name}_{modulo}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            # Imprimir resumen rápido
            datos = output.get("datos_crudos", {})
            kpis  = output.get("kpis", [])
            kpi_str = " | ".join(f"{k['label'][:10]}={k['value']}({k['status']})" for k in kpis)
            print(f"  {modulo:14s}: {kpi_str}")

    print(f"\n✅ Golden files generados en {GOLDEN_DIR}")

if __name__ == "__main__":
    main()
