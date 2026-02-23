import re
from typing import List, Dict, Any, Optional

class FinancialCalculator:
    """
    Motor universal para extraer cuentas de estados financieros.
    """
    def __init__(self):
        # Rentabilidad
        self.kw_utilidad_neta = [
            'utilidad neta',
            'resultado neto',
            'ganancia neta',
            'utilidad del ejercicio',
            'utilidad (pérdida) neta',
            'resultado del ejercicio',
            'resultado del periodo',
            'resultado del año',
            'resultado del mes',
            'utilidad del periodo',
            'utilidad final',
            'resultado final',
            'beneficio neto',
            'pérdida neta',
        ]

        self.kw_ventas_netas = [
            'ventas netas',
            'ventas totales',
            'ingresos netos',
            'ingresos totales',
            'total de ingresos',
            'ingresos por servicios',         
            'ingresos operativos',
            'facturación total',
            'total ventas',
            'importe de ventas',
            'productos y servicios'
        ]

        self.kw_activo_total = [
            'total de activos',
            'activo total',
            'suma del activo',
            'activos totales',
            'total del activo',
            'activo general',
            'activo circulante y fijo',
            'activo corriente y no corriente'
        ]

        self.kw_capital = [
            'capital contable',
            'total capital contable',
            'patrimonio neto',
            'total patrimonio',
            'total capital',
            'capital y reservas',
            'capital propio',
            'capital financiero',
            'patrimonio'
        ]
        # 5. Cuentas para Liquidez
        self.kw_activo_circulante = [
            'activo circulante', 'total activo circulante', 'total de activo circulante',
            'activos corrientes', 'total de activos corrientes', 'suma del activo circulante'
        ]
        self.kw_pasivo_circulante = [
            'pasivo circulante', 'total pasivo circulante', 'total de pasivo circulante',
            'pasivos corrientes', 'total de pasivos corrientes', 'suma del pasivo circulante',
            'pasivo a corto plazo'
        ]
        self.kw_inventario = [
            'inventario', 'inventarios', 'almacén', 'almacen', 'mercancías', 'mercancias'
        ]

    def _clean_number(self, text: str) -> Optional[float]:
        """Limpia la basura visual para dejar solo números reales."""
        clean_text = text.lower().replace(" ", "")
        if not re.search(r'\d', clean_text):
            return None

        is_negative = False
        if '(' in clean_text and ')' in clean_text:
            is_negative = True

        clean_text = re.sub(r'[^\d\.\-]', '', clean_text)
        
        try:
            val = float(clean_text)
            return -val if is_negative else val
        except ValueError:
            return None

    def _find_value(self, tables_data: List[List[Dict]], keywords: List[str]) -> float:
        """
        TÁCTICA MAESTRA: Busca de ABAJO hacia ARRIBA y de DERECHA a IZQUIERDA.
        """
        # 1. Recorrer tablas de atrás hacia adelante
        for table in reversed(tables_data):
            rows = {}
            for cell in table:
                r_idx = cell.get('row', 0)
                if r_idx not in rows:
                    rows[r_idx] = []
                rows[r_idx].append(cell)

            # 2. Ordenar las filas al revés (de la última fila hacia la primera)
            sorted_row_indices = sorted(rows.keys(), reverse=True)

            for r_idx in sorted_row_indices:
                row_cells = rows[r_idx]
                
                # Juntar el texto de la fila para identificar si es la cuenta correcta
                row_cells.sort(key=lambda x: x.get('col', 0))
                row_text = " ".join([c.get('text', '').lower() for c in row_cells])
                
                for kw in keywords:
                    if kw in row_text:
                        # 3. Leer columnas de derecha a izquierda (para atrapar Totales/Acumulados)
                        for cell in reversed(row_cells):
                            val = self._clean_number(cell.get('text', ''))
                            if val is not None and val != 0:
                                return val
        return 0.0

    def calcular_rentabilidad(self, balance_data: Dict, resultados_data: Dict) -> Dict[str, Any]:
        tablas_resultados = resultados_data.get('tables_data', [])
        tablas_balance = balance_data.get('tables_data', [])

        # 1. Ventas Netas (En Resultados)
        ventas_netas = self._find_value(tablas_resultados, self.kw_ventas_netas)

        # 2. Utilidad Neta (Doble Chequeo)
        utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_neta)
        if utilidad_neta == 0:
            # Si no está clara en el estado de resultados, búscala en el balance general
            utilidad_neta = self._find_value(tablas_balance, self.kw_utilidad_neta)

        # 3. Balance General
        activo_total = self._find_value(tablas_balance, self.kw_activo_total)
        capital_contable = self._find_value(tablas_balance, self.kw_capital)

        # 4. Cálculos seguros
        margen_utilidad = (utilidad_neta / ventas_netas) if ventas_netas else 0
        roa = (utilidad_neta / activo_total) if activo_total else 0
        roe = (utilidad_neta / capital_contable) if capital_contable else 0

        return {
            "datos_crudos": {
                "utilidad_neta": utilidad_neta,
                "ventas_netas": ventas_netas,
                "activo_total": activo_total,
                "capital_contable": capital_contable
            },
            "kpis": [
                {
                    "label": "Margen de Rentabilidad",
                    "value": f"{margen_utilidad * 100:.2f}%",
                    "status": "ok" if margen_utilidad >= 0.10 else "warn"
                },
                {
                    "label": "Rendimiento sobre Activos Totales (RAT)",
                    "value": f"{roa * 100:.2f}%",
                    "status": "ok" if roa >= 0.05 else "warn"
                },
                {
                    "label": "Rendimiento sobre el Patrimonio",
                    "value": f"{roe * 100:.2f}%",
                    "status": "ok" if roe >= 0.10 else "warn"
                }
            ]
        }
    
    def calcular_liquidez(self, balance_data: Dict) -> Dict[str, Any]:
        """Calcula los indicadores de liquidez basados en el Balance General."""
        tablas_balance = balance_data.get('tables_data', [])

        activo_circulante = self._find_value(tablas_balance, self.kw_activo_circulante)
        pasivo_circulante = self._find_value(tablas_balance, self.kw_pasivo_circulante)
        inventario = self._find_value(tablas_balance, self.kw_inventario) # Puede ser 0 en empresas de servicios

        # Fórmulas de la imagen
        razon_liquidez = (activo_circulante / pasivo_circulante) if pasivo_circulante else 0
        prueba_acido = ((activo_circulante - inventario) / pasivo_circulante) if pasivo_circulante else 0
        capital_trabajo = activo_circulante - pasivo_circulante

        return {
            "datos_crudos": {
                "activo_circulante": activo_circulante,
                "pasivo_circulante": pasivo_circulante,
                "inventario": inventario
            },
            "kpis": [
                {
                    "label": "Razón de Liquidez",
                    "value": f"{razon_liquidez:.2f}",
                    "status": "ok" if razon_liquidez >= 1.0 else "warn"
                },
                {
                    "label": "Prueba del Ácido",
                    "value": f"{prueba_acido:.2f}",
                    "status": "ok" if prueba_acido >= 0.8 else "warn"
                },
                {
                    "label": "Capital de Trabajo",
                    # Usamos formato de moneda con separador de miles porque no es porcentaje, es dinero
                    "value": f"${capital_trabajo:,.2f}", 
                    "status": "ok" if capital_trabajo > 0 else "warn"
                }
            ]
        }

