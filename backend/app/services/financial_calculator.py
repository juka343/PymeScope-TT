import re
from typing import List, Dict, Any, Optional

class FinancialCalculator:
    """
    Motor universal para extraer cuentas de estados financieros a partir de tablas OCR.
    Espera: balance_data/resultados_data con clave 'tables_data' que contiene:
      tables_data: List[table]
      table: List[cell]
      cell: Dict con al menos 'row', 'col', 'text'
    """

    def __init__(self) -> None:
        # ===== Rentabilidad =====
        self.kw_utilidad_neta = [
            "utilidad neta", "resultado neto", "ganancia neta",
            "utilidad del ejercicio", "utilidad (pérdida) neta",
            "resultado del ejercicio", "resultado del periodo",
            "resultado del año", "resultado del mes",
            "utilidad del periodo", "utilidad final",
            "resultado final", "beneficio neto", "pérdida neta",
            "resul. ejerc. en curso", "resul ejerc en curso",
            "resultado ejerc en curso", "resultado del ejerc en curso",
            "resultado del ejercicio en curso",
        ]

        self.kw_utilidad_antes_impuestos = [
            "utilidad antes de impuestos", "resultado antes de impuestos",
            "resultado antes del impuesto", "utilidad antes del impuesto",
        ]

        self.kw_ventas_netas = [
            "ventas netas", "ventas totales", "ingresos netos",
            "ingresos totales", "total de ingresos", "ingresos por servicios",
            "ingresos operativos", "facturación total", "total ventas",
            "importe de ventas", "productos y servicios",
            "ingresos por venta", "venta de inmuebles",
            "ingresos por arrendamiento", "ingresos por rentas",
        ]

        self.kw_activo_total = [
            "total de activos", "activo total", "suma del activo",
            "activos totales", "total del activo", "activo general",
            "activo circulante y fijo", "activo corriente y no corriente",
        ]

        self.kw_capital = [
            "capital contable", "total capital contable", "patrimonio neto",
            "total patrimonio", "total capital", "capital y reservas",
            "capital propio", "capital financiero", "patrimonio",
            "capital social",
        ]

        # ===== Liquidez =====
        self.kw_activo_circulante = [
            "activo circulante", "total activo circulante",
            "total de activo circulante", "activos corrientes",
            "total de activos corrientes", "suma del activo circulante",
        ]

        self.kw_pasivo_circulante = [
            "pasivo circulante", "total pasivo circulante",
            "total de pasivo circulante", "pasivos corrientes",
            "total de pasivos corrientes", "suma del pasivo circulante",
            "pasivo a corto plazo",
        ]

        self.kw_inventario = [
            "inventario", "inventarios", "almacén",
            "almacen", "mercancías", "mercancias",
        ]

    # -------------------------------------------------------------------------
    # Parsing de números
    # -------------------------------------------------------------------------
    def _clean_number(self, text: str) -> Optional[float]:
        if text is None:
            return None
        raw = str(text).strip()
        if not raw:
            return None
        if not re.search(r"\d", raw):
            return None

        # Detectar negativos incluso si el signo está al final (ej. 136,933.46-)
        is_negative = ("(" in raw and ")" in raw) or raw.startswith("-") or raw.endswith("-")

        s = raw.lower()
        s = s.replace(" ", "").replace("$", "").replace("mxn", "").replace("usd", "")
        s = s.replace("(", "").replace(")", "")
        s = re.sub(r"[^0-9,\.]", "", s)

        if "," in s and "." in s:
            last_comma = s.rfind(",")
            last_dot = s.rfind(".")
            if last_comma > last_dot:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s and "." not in s:
            if s.count(",") == 1 and re.search(r",\d{1,2}$", s):
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        else:
            if s.count(".") > 1:
                parts = s.split(".")
                s = "".join(parts[:-1]) + "." + parts[-1]

        try:
            val = float(s)
            return -abs(val) if is_negative else val
        except ValueError:
            return None

    # -------------------------------------------------------------------------
    # Búsqueda de valores en tablas OCR (Proximidad Inteligente)
    # -------------------------------------------------------------------------
    def _find_value(self, tables_data: List[List[Dict[str, Any]]], keywords: List[str], take_last: bool = False) -> float:
        for table in reversed(tables_data):
            rows: Dict[int, List[Dict[str, Any]]] = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)

            for r_idx in sorted(rows.keys(), reverse=True):
                row_cells = rows[r_idx]
                row_cells.sort(key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])

                for kw in keywords:
                    if kw in row_text:
                        kw_col_index = -1
                        for cell in row_cells:
                            if kw in str(cell.get("text", "")).lower():
                                kw_col_index = int(cell.get("col", 0))
                                break

                        found_values = []
                        for cell in row_cells:
                            if int(cell.get("col", 0)) > kw_col_index:
                                val = self._clean_number(cell.get("text", ""))
                                if val is not None and abs(val) > 0:
                                    found_values.append(float(val))

                        if found_values:
                            # --- FILTRO ANTI-PORCENTAJES (Nivel Experto) ---
                            max_magnitude = max(abs(v) for v in found_values)
                            
                            # Conservamos el número si es mayor a 1000 (dinero real), 
                            # o si de plano es el número más grande de la fila.
                            val_monetarios = [v for v in found_values if abs(v) > 1000 or abs(v) == max_magnitude]
                            
                            if val_monetarios:
                                return val_monetarios[-1] if take_last else val_monetarios[0]
                            else:
                                return found_values[-1] if take_last else found_values[0]
                            
                        # Fallback si texto y número están pegados en la misma celda
                        for cell in row_cells:
                            if kw in str(cell.get("text", "")).lower():
                                val = self._clean_number(cell.get("text", ""))
                                if val is not None and abs(val) > 0:
                                    return float(val)
        return 0.0

    # -------------------------------------------------------------------------
    # KPIs
    # -------------------------------------------------------------------------
    def calcular_rentabilidad(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any]) -> Dict[str, Any]:
        tablas_resultados = resultados_data.get("tables_data", []) or []
        tablas_balance = balance_data.get("tables_data", []) or []

        # 1) Ventas/Ingresos (en Resultados, tomamos el acumulado con take_last=True)
        ventas_netas = self._find_value(tablas_resultados, self.kw_ventas_netas, take_last=True)

        # 2) Utilidad neta (en Resultados, tomamos el acumulado con take_last=True)
        utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_neta, take_last=True)
        
        # 2a) Fallback: buscar utilidad neta en el Balance (aquí no usamos take_last)
        if utilidad_neta == 0:
            utilidad_neta = self._find_value(tablas_balance, self.kw_utilidad_neta)

        # 2b) Fallback: utilidad antes de impuestos
        if utilidad_neta == 0:
            utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_antes_impuestos, take_last=True)
            if utilidad_neta == 0:
                utilidad_neta = self._find_value(tablas_balance, self.kw_utilidad_antes_impuestos)

        # 3) Balance
        activo_total = self._find_value(tablas_balance, self.kw_activo_total)
        capital_contable = self._find_value(tablas_balance, self.kw_capital)

        # 4) Cálculos
        margen_utilidad = (utilidad_neta / ventas_netas) if ventas_netas else 0
        roa = (utilidad_neta / activo_total) if activo_total else 0
        roe = (utilidad_neta / capital_contable) if capital_contable else 0

        return {
            "datos_crudos": {
                "utilidad_neta": utilidad_neta,
                "ventas_netas": ventas_netas,
                "activo_total": activo_total,
                "capital_contable": capital_contable,
            },
            "kpis": [
                {
                    "label": "Margen de Rentabilidad",
                    "value": f"{margen_utilidad * 100:.2f}%",
                    "status": "ok" if margen_utilidad >= 0.10 else "warn",
                },
                {
                    "label": "Rendimiento sobre Activos Totales (RAT)",
                    "value": f"{roa * 100:.2f}%",
                    "status": "ok" if roa >= 0.05 else "warn",
                },
                {
                    "label": "Rendimiento sobre el Patrimonio",
                    "value": f"{roe * 100:.2f}%",
                    "status": "ok" if roe >= 0.10 else "warn",
                },
            ],
        }

    def calcular_liquidez(self, balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula indicadores de liquidez basados en el Balance General."""
        tablas_balance = balance_data.get("tables_data", []) or []

        activo_circulante = self._find_value(tablas_balance, self.kw_activo_circulante)
        pasivo_circulante = self._find_value(tablas_balance, self.kw_pasivo_circulante)
        inventario = self._find_value(tablas_balance, self.kw_inventario)

        if pasivo_circulante < 0:
            pasivo_circulante = abs(pasivo_circulante)

        razon_liquidez = (activo_circulante / pasivo_circulante) if pasivo_circulante else 0
        prueba_acido = ((activo_circulante - inventario) / pasivo_circulante) if pasivo_circulante else 0
        capital_trabajo = activo_circulante - pasivo_circulante

        return {
            "datos_crudos": {
                "activo_circulante": activo_circulante,
                "pasivo_circulante": pasivo_circulante,
                "inventario": inventario,
            },
            "kpis": [
                {
                    "label": "Razón de Liquidez",
                    "value": f"{razon_liquidez:.2f}",
                    "status": "ok" if razon_liquidez >= 1.0 else "warn",
                },
                {
                    "label": "Prueba del Ácido",
                    "value": f"{prueba_acido:.2f}",
                    "status": "ok" if prueba_acido >= 0.8 else "warn",
                },
                {
                    "label": "Capital de Trabajo",
                    "value": f"${capital_trabajo:,.2f}",
                    "status": "ok" if capital_trabajo > 0 else "warn",
                },
            ],
        }