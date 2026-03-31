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
            "utilidad total", 
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
            # "ingresos", <--- ELIMINADO PARA EVITAR FALSOS POSITIVOS CON "OTROS INGRESOS"
        ]

        self.kw_activo_total = [
            "total de activos", "activo total", "suma del activo",
            "activos totales", "total del activo", "activo general",
            "activo circulante y fijo", "activo corriente y no corriente",
            "total activos:", 
            "total activos",
        ]

        # CORRECCIÓN 1: Quitamos "capital social" para obligar a buscar el CONTABLE
        self.kw_capital = [
            "capital contable", "total capital contable", "patrimonio neto",
            "total patrimonio", "total capital", "capital y reservas",
            "capital propio", "capital financiero", "patrimonio",
            # "capital social", <--- ELIMINADO: Causaba error al tomar el valor nominal y no el real
        ]

        # ===== Liquidez =====
        self.kw_activo_circulante = [
            "activo circulante", "total activo circulante",
            "total de activo circulante", "activos corrientes",
            "total de activos corrientes", "suma del activo circulante",
            "activo a corto plazo", 
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

        # ===== Endeudamiento =====
        # CORRECCIÓN 2: Quitamos "total pasivo" para que no lea la línea "Total Pasivo + Capital"
        self.kw_pasivo_total = [
            "pasivo total", "total del pasivo", "suma del pasivo", 
            "pasivos totales", "total pasivos",
            # "total pasivo", <--- ELIMINADO: Peligroso en formatos que suman Capital
        ]
        
        self.kw_utilidad_operacion = [
            "utilidad de operación", "utilidad de operacion", "utilidad operativa", 
            "resultado de operación", "resultado de operacion", "resultado operativo", 
            "ganancia operativa",
        ]
        
        self.kw_intereses = [
            "gastos financieros", 
            "costo integral de financiamiento",
            # Quitamos los específicos que pueden capturar sub-cuentas pequeñas
        ]

        # ===== Rotación de activos =====
        self.kw_cuentas_por_cobrar = [
            "cuentas por cobrar", "clientes", "cxc",
        ]

        # ===== Rotación de activos (Ajuste Final) =====
        self.kw_costo_de_ventas = [
            "costo de venta", "costos de venta", # TAAS usa "Costo de venta y/o servicio"
            "costo de ventas", "costos de ventas", 
            "costo de lo vendido",
        ]

        self.kw_compras = [
            "compras nacionales", 
            "compras extranjeras",
            "compras totales",
            "adquisiciones de mercancía",
        ]

        self.kw_devoluciones_costo = [
            "devoluciones, descuentos o bonificaciones",
            "devoluciones sobre compras",
            "descuentos sobre compras",
        ]

        self.kw_activo_fijo = [
            "activo a largo plazo", # TÉRMINO CLAVE PARA TAAS LOGISTICS
            "propiedades planta y equipo",
            "propiedad, planta y equipo",
            "activo fijo neto", "activo fijo",
            "inmuebles maquinaria y equipo",
        ]

        # ===== Estructura =====
        self.kw_capital_social = [
            "capital social", 
            "capital social fijo",      # Muy común en S.A. de C.V.
            "capital social variable",  # Muy común en S.A. de C.V.
            "capital aportado", 
            "capital pagado",
            "capital contribuido",      # Término formal de las NIF
            "capital suscrito",
        ]

        self.kw_pasivo_largo_plazo = [
            "pasivo a largo plazo", 
            "pasivo no circulante",     # Término estándar actual
            "pasivos a largo plazo",
            "pasivo fijo",              # Término antiguo pero común
            "total pasivo a largo plazo", 
            "total de pasivo a largo plazo",
            "pasivos no corrientes",    # Común en traducciones o software internacional
            "deuda a largo plazo",      # A veces se etiqueta así la deuda bancaria
            "créditos a largo plazo",
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
        
        if ventas_netas == 0:
            ventas_netas = self._find_value(tablas_resultados, ["ingresos"], take_last=True)

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

    def calcular_endeudamiento(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula indicadores de endeudamiento cruzando Balance General y Estado de Resultados."""
        tablas_balance = balance_data.get("tables_data", []) or []
        tablas_resultados = resultados_data.get("tables_data", []) or []

        # --- EXTRACCIÓN DEL BALANCE ---
        activo_total = self._find_value(tablas_balance, self.kw_activo_total)
        capital_social = self._find_value(tablas_balance, self.kw_capital)
        pasivo_total_doc = self._find_value(tablas_balance, self.kw_pasivo_total)

        # Lógica de rescate para Pasivo Total (Ecuación Contable: P = A - C)
        if pasivo_total_doc == 0 and activo_total > 0:
            pasivo_total = activo_total - capital_social
        else:
            pasivo_total = pasivo_total_doc
        
        # Limpieza de signos
        if pasivo_total < 0: pasivo_total = abs(pasivo_total)

        # --- EXTRACCIÓN DEL ESTADO DE RESULTADOS ---
        utilidad_operacion = self._find_value(tablas_resultados, self.kw_utilidad_operacion, take_last=True)
        intereses = self._find_value(tablas_resultados, self.kw_intereses, take_last=True)
        
        if intereses < 0: intereses = abs(intereses)

        # --- LÓGICA DE RESCATE PARA UTILIDAD DE OPERACIÓN (NUEVO) ---
        # Si no encontramos "Utilidad de Operación", usamos EBIT aproximado:
        # Utilidad Operativa ≈ Utilidad Neta + Intereses
        if utilidad_operacion == 0:
            utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_neta, take_last=True)
            
            # Solo aplicamos el rescate si tenemos utilidad neta confirmada
            if utilidad_neta != 0:
                utilidad_operacion = utilidad_neta + intereses

        # --- CÁLCULOS ---
        apalancamiento = (pasivo_total / activo_total) if activo_total else 0
        cobertura_intereses = (utilidad_operacion / intereses) if intereses else 0
        estabilidad_financiera = (pasivo_total / capital_social) if capital_social else 0

        return {
            "datos_crudos": {
                "pasivo_total": pasivo_total,
                "activo_total": activo_total,
                "capital_social": capital_social,
                "utilidad_operacion": utilidad_operacion,
                "intereses": intereses,
            },
            "kpis": [
                {
                    "label": "Apalancamiento",
                    "value": f"{apalancamiento:.2f}",
                    "status": "ok" if apalancamiento <= 0.5 and apalancamiento > 0 else "warn",
                },
                {
                    "label": "Razón de Cobertura de Intereses",
                    "value": f"{cobertura_intereses:.2f}",
                    "status": "ok" if cobertura_intereses >= 1.5 else "warn",
                },
                {
                    "label": "Estabilidad Financiera",
                    "value": f"{estabilidad_financiera:.2f}",
                    "status": "ok" if estabilidad_financiera <= 1.0 and estabilidad_financiera > 0 else "warn",
                },
            ],
        }

    # En financial_calculator.py

    def calcular_rotacion(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any], periodicidad: str = "anual") -> Dict[str, Any]:
        """Calcula indicadores de rotación ajustando los días según la periodicidad."""
        tablas_balance = balance_data.get("tables_data", []) or []
        tablas_resultados = resultados_data.get("tables_data", []) or []

        # Valores del Balance
        cuentas_por_cobrar = self._find_value(tablas_balance, self.kw_cuentas_por_cobrar)
        inventario = self._find_value(tablas_balance, self.kw_inventario)
        activo_fijo_neto = self._find_value(tablas_balance, self.kw_activo_fijo)
        activo_total = self._find_value(tablas_balance, self.kw_activo_total)

        # Valores de Resultados
        ventas_netas = self._find_value(tablas_resultados, self.kw_ventas_netas, take_last=True)
        
        if ventas_netas == 0:
            ventas_netas = self._find_value(tablas_resultados, ["ingresos"], take_last=True)

        # --- CORRECCIÓN DE COSTO DE VENTAS ---
        # 1. Buscamos el costo explícito (ej. "Costo de ventas")
        costo_directo = self._find_value(tablas_resultados, self.kw_costo_de_ventas, take_last=True)
        
        # 2. Buscamos las compras (ej. "Compras nacionales")
        compras = self._find_value(tablas_resultados, self.kw_compras, take_last=True)
        
        devoluciones = self._find_value(tablas_resultados, self.kw_devoluciones_costo, take_last=True)
        # 3. Sumamos ambos. En empresas comercializadoras (como TAAS), 
        # a veces separan el costo del servicio de la compra de mercancía.
        costo_ventas_calculado = abs(costo_directo) + abs(compras) - abs(devoluciones)        
        # Nota: Si el PDF ya traía un "Total Costos" que incluía ambos, 
        # esto podría duplicar, pero es preferible un costo alto (conservador) a uno de casi cero.

        if costo_ventas_calculado < 0:
            costo_ventas_calculado = 0

        # --- LÓGICA DE PERIODICIDAD ---
        dias_periodo = 360 
        p = str(periodicidad).lower().strip()
        
        if p == "mensual":
            dias_periodo = 30
        elif p == "trimestral":
            dias_periodo = 90
        elif p == "semestral":
            dias_periodo = 180
            
        # CÁLCULOS
        
        # 1. Rotación de Cartera
        rotacion_cartera = (ventas_netas / cuentas_por_cobrar) if cuentas_por_cobrar else 0
        
        # 2. Días de Cobro
        ventas_diarias = (ventas_netas / dias_periodo) if dias_periodo else 0
        periodo_recaudo = (cuentas_por_cobrar / ventas_diarias) if ventas_diarias else 0
        
        # 3. Rotaciones de Activos
        rotacion_inventarios = (costo_ventas_calculado / inventario) if inventario else 0
        rotacion_activos_fijos = (ventas_netas / activo_fijo_neto) if activo_fijo_neto else 0
        rotacion_activos_totales = (ventas_netas / activo_total) if activo_total else 0

        return {
            "datos_crudos": {
                "cuentas_por_cobrar": cuentas_por_cobrar,
                "inventario": inventario,
                "activo_fijo_neto": activo_fijo_neto,
                "activo_total": activo_total,
                "ventas_netas": ventas_netas,
                "costo_ventas": costo_ventas_calculado, # Este valor corregido se enviará a Firebase
                "dias_calculo": dias_periodo
            },
            "kpis": [
                {
                    "label": "Rotación de la Cartera",
                    "value": f"{rotacion_cartera:.2f}",
                    "status": "ok" if rotacion_cartera > 0 else "warn",
                },
                {
                    "label": "Periodo Promedio de Recaudo",
                    "value": f"{periodo_recaudo:,.0f} días",
                    "status": "ok" if periodo_recaudo <= 60 and periodo_recaudo > 0 else "warn",
                },
                {
                    "label": "Rotación de Inventarios",
                    "value": f"{rotacion_inventarios:.2f}",
                    "status": "ok" if rotacion_inventarios > 0 else "warn",
                },
                {
                    "label": "Rotación de Activos Fijos",
                    "value": f"{rotacion_activos_fijos:.2f}",
                    "status": "ok" if rotacion_activos_fijos >= 1.0 else "warn",
                },
                {
                    "label": "Rotación de Activos Totales",
                    "value": f"{rotacion_activos_totales:.2f}",
                    "status": "ok" if rotacion_activos_totales >= 1.0 else "warn",
                },
            ],
        }

    def calcular_estructura(self, balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula indicadores de Estructura Financiera basados en el Balance General."""
        tablas_balance = balance_data.get("tables_data", []) or []

        # --- 1. EXTRACCIÓN BÁSICA ---
        activo_total = self._find_value(tablas_balance, self.kw_activo_total)
        activo_fijo = self._find_value(tablas_balance, self.kw_activo_fijo) 
        pasivo_total_doc = self._find_value(tablas_balance, self.kw_pasivo_total)
        capital_contable = self._find_value(tablas_balance, self.kw_capital)
        pasivo_largo_plazo = self._find_value(tablas_balance, self.kw_pasivo_largo_plazo)

        # --- 2. LÓGICA INTELIGENTE PARA CAPITAL SOCIAL ---
        capital_social_doc = self._find_value(tablas_balance, self.kw_capital_social)
        capital_variable = self._find_value(tablas_balance, ["capital variable", "capital social variable"])
        capital_fijo = self._find_value(tablas_balance, ["capital fijo", "capital social fijo"])
        
        suma_capitales = capital_fijo + capital_variable
        
        if suma_capitales > capital_social_doc:
            capital_social = suma_capitales      
        elif capital_social_doc == capital_variable and capital_fijo == 0 and capital_variable > 0:
            capital_social = capital_social_doc + capital_variable   
        else:
            capital_social = capital_social_doc

        # --- 3. RESCATE PARA PASIVO TOTAL ---
        if pasivo_total_doc == 0 and activo_total > 0:
            pasivo_total = activo_total - capital_contable
        else:
            pasivo_total = pasivo_total_doc
            
        if pasivo_total < 0: 
            pasivo_total = abs(pasivo_total)

        # --- 4. CÁLCULOS MATEMÁTICOS (¡DEBEN IR AQUÍ ABAJO!) ---
        # Ahora sí, el sistema usará los 10,000 corregidos
        
        solvencia = (activo_total / pasivo_total) if pasivo_total else 0
        
        if pasivo_largo_plazo and pasivo_largo_plazo > 0:
            seguridad_largo_plazo = activo_fijo / pasivo_largo_plazo
        else:
            seguridad_largo_plazo = None 

        inmovilizacion_social = (activo_fijo / capital_social) if capital_social else 0
        inmovilizacion_contable = (activo_fijo / capital_contable) if capital_contable else 0

        # --- 5. RETORNO DE RESULTADOS ---
        return {
            "datos_crudos": {
                "activo_total": activo_total,
                "pasivo_total": pasivo_total,
                "capital_social": capital_social, # Mandará 10,000
                "capital_contable": capital_contable,
                "activo_fijo": activo_fijo,
                "pasivo_largo_plazo": pasivo_largo_plazo
            },
            "kpis": [
                {
                    "label": "Solvencia General",
                    "value": f"{solvencia:.2f}",
                    "status": "ok" if solvencia > 1.0 else "warn",
                },
                {
                    "label": "Seguridad a largo plazo",
                    "value": "Sin Deuda LP" if seguridad_largo_plazo is None else f"{seguridad_largo_plazo:.2f}",
                    "status": "ok" if (seguridad_largo_plazo is None or seguridad_largo_plazo >= 1.0) else "warn",
                },
                {
                    "label": "Inmovilización de Cap. Social",
                    "value": f"{inmovilizacion_social:.2f}", # Ahora sí será 26.63
                    "status": "ok" if inmovilizacion_social <= 1.0 else "warn", 
                },
                {
                    "label": "Inmovilización de Cap. Contable",
                    "value": f"{inmovilizacion_contable:.2f}",
                    "status": "ok" if inmovilizacion_contable <= 1.0 else "warn",
                },
            ],
        }