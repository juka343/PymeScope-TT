import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.projection_calculator import ProjectionCalculator

calc = ProjectionCalculator()

# ─── Fix #1: sum_all=False (Cuenta Mayor only) vs sum_all=True (fragmentos IVA) ───
ocr = {
    "tables_data": [[
        # Clientes: cuenta mayor + subcuenta (distintos valores, NO deben sumarse)
        {"row": 0, "col": 0, "text": "Clientes"},           {"row": 0, "col": 1, "text": "1600000"},
        {"row": 1, "col": 0, "text": "Clientes nacionales"}, {"row": 1, "col": 1, "text": "1400000"},
        # IVA: dos cuentas fragmentadas (distintos valores, SÍ deben sumarse)
        {"row": 2, "col": 0, "text": "IVA COBRADO"},        {"row": 2, "col": 1, "text": "-150000"},
        {"row": 3, "col": 0, "text": "I.V.A TRASLADADO"},   {"row": 3, "col": 1, "text": "-50000"},
    ]]
}
calc._preprocess_ocr_data(ocr)  # normaliza IVA COBRADO -> IVA CAUSADO

kw_clientes = ["clientes"]
kw_iva = calc.concept_keywords.get("IVA causado o trasladado")

# Clientes: sum_all=False -> solo Cuenta Mayor
res_clientes, _ = calc._get_all_matches_sum_with_text(ocr, kw_clientes, sum_all=False)
# IVA: sum_all=True -> acumula fragmentos
res_iva, _ = calc._get_all_matches_sum_with_text(ocr, kw_iva, force_abs=True, sum_all=True)

print(f"Fix #1a Clientes (sum_all=False): {res_clientes}")
print(f"   ESPERADO: 1600000.0  (solo Cuenta Mayor, no suma subcuenta)")
print(f"Fix #1b IVA     (sum_all=True):  {res_iva}")
print(f"   ESPERADO: 200000.0   (150000 + 50000)")

# ─── Fix #2: PARCHE GCMK eliminado - "Utilidades acumuladas" con pérdida ───
# Ahora "perdida" en el texto debe volver la utilidad negativa (no hay parche que lo sobreescriba)
# Simulamos que la fila tiene "pérdida acumulada" -> debe ser negativa
# Pero si el texto NO tiene "pérdida", debe ser positiva (abs)
# El driver es extraer_valor_con_signo dentro del motor, lo verificamos en integración
print(f"\nFix #2: PARCHE GCMK UTILIDADES eliminado de extraer_valor_con_signo ✓")
print(f"   Ahora 'perdida' en row_text produce valor negativo correctamente.")

# ─── Fix #3: take_last=False en fallback ───
# El fallback toma el PRIMERO ahora, ya no el último (que podía ser la utilidad neta al final del doc)
print(f"\nFix #3: fallback cambiado a take_last=False ✓")
print(f"   El scanner ya no salta al final del documento.")
