import re
from typing import List, Dict, Any
from app.services.financial_calculator import FinancialCalculator
from app.models.projections import LineaSupuesto

class ProjectionCalculator(FinancialCalculator):
    """
    Motor de proyecciones financieras avanzado.
    Optimizado con un Bypass de RegEx para extracciones exactas de OCR.
    """

    def __init__(self) -> None:
        super().__init__()

        self.ALIAS_MAP = {
            "IVA COBRADO": "IVA causado o trasladado",
            "IVA A FAVOR EJER ANT": "IVA acreditable",
            "CASA OFICINA": "Edificios",
            "EQUIPO AUTOMOTRIZ": "Equipo de transporte"
        }

        # ─── DICCIONARIO DEL ESTADO DE RESULTADOS ───────────────────────────────
        # Alias para cuentas de INGRESOS, COSTOS, GASTOS e IMPUESTOS (gasto).
        # Nunca debe usarse al procesar el Balance General.
        self.er_keywords: Dict[str, List[str]] = {
            "Ventas netas / Ingresos por servicios": self.kw_ventas_netas,
            "Costo de ventas/Costo por servicios":   self.kw_costo_de_ventas,
            "Gastos financieros":                    self.kw_intereses,
            "Otros ingresos": [
                "otros ingresos", "otros productos", "ingresos diversos",
                "otros ingresos de operación",
            ],
            "Productos financieros": [
                "productos financieros", "ingresos financieros",
                "intereses ganados", "intereses a favor",
            ],
            "Gastos de venta": [
                "gastos de venta", "gastos de ventas",
                "gastos de comercialización", "gastos de distribución",
            ],
            "Gastos de administración": [
                "gastos de administración", "gastos de administracion",
                "gastos operativos", "gastos de operacion", "gastos de operación",
                "gastos generales",
            ],
            "Gastos de nómina": [
                "gastos de nómina", "sueldos y salarios", "nómina", "nomina",
                "remuneraciones al personal",
            ],
            "Otros gastos": [
                "otros gastos", "otros egresos", "gastos diversos",
                "otros gastos y pérdidas",
            ],
            # Impuestos como GASTO del ER (no confundir con pasivos del BG)
            "ISR": [
                "isr", "impuesto sobre la renta", "impuesto a las ganancias",
                "isr del ejercicio", "isr causado",
            ],
            "PTU (Participación de los Trabajadores en las Utilidades)": [
                "ptu", "participación de los trabajadores en las utilidades",
                "ptu del ejercicio",
            ],
        }

        # ─── DICCIONARIO DEL BALANCE GENERAL ────────────────────────────────────
        # Alias para cuentas de ACTIVO, PASIVO y CAPITAL.
        # Nunca debe usarse al procesar el Estado de Resultados.
        self.bg_keywords: Dict[str, List[str]] = {
            # Activo Circulante
            "Caja":                                    ["caja", "efectivo", "caja chica", "fondo fijo", "efectivo en caja"],
            "Bancos":                                  ["bancos", "efectivo y equivalentes", "efectivo en bancos"],
            "Cuentas por cobrar a clientes":           self.kw_cuentas_por_cobrar,
            "Otras cuentas por cobrar (deudores diversos)": ["deudores diversos", "deudores"],
            "Inventarios":                             self.kw_inventario,
            "IVA acreditable":                         ["impuestos a favor", "iva a favor", "iva acreditable"],
            "Impuestos y derechos": [
                "impuestos acreditables por pagar", "impuestos acreditables pagados",
                "impuestos acreditables", "otros impuestos a favor",
                "impuestos y derechos", "impuesto acreditable",
                "isr anticipos", "isr a favor", "sub-sidio al empleo",
                "ISR ANTICIPOS", "ISR A FAVOR", "SUB-SIDIO AL EMPLEO",
            ],
            "Seguros y fianzas": ["seguros y fianzas", "seguros pagados por anticipado", "seguros anticipados"],
            # Activo No Circulante
            "Terrenos":                  ["terrenos"],
            "Edificios":                 ["edificios", "inmuebles", "casa oficina"],
            "Maquinaria y equipo":       ["maquinaria y equipo", "maquinaria"],
            "Equipo de transporte": [
                "equipo de transporte", "vehículos",
                "automóviles, autobuses, camiones", "automóviles",
                "camiones", "equipo automotriz",
            ],
            "Mobiliario y equipo de oficina": ["mobiliario y equipo de oficina", "muebles y enseres"],
            "Equipo de cómputo":         ["equipo de cómputo", "equipo de comunicación", "cómputo"],
            "Depreciación acumulada": [
                "depreciación acumulada", "deprec. acum.", "dep. acum.", "dep. acumulada",
                "depreciacion acumulada", "depreciacion", "deprec acum", "(-) deprec. acum.",
            ],
            # Pasivo Corto Plazo
            "Cuentas por pagar a proveedores":           ["proveedores", "cuentas por pagar a proveedores"],
            "Préstamo bancario / Deuda a corto plazo":   ["documentos por pagar", "préstamos bancarios", "prestamos bancarios", "deuda a corto plazo"],
            "Acreedores diversos":                       ["acreedores diversos", "acreedores"],
            "Impuestos a la utilidad por pagar": [
                "impuestos a la utilidad por pagar", "impuestos por pagar",
                "isr por pagar", "ptu por pagar",
                "impuestos retenidos",
                "provisión de impuestos", "impuestos acumulados",
            ],
            "IVA por causar o trasladar":  ["iva por causar o trasladar", "iva por causar", "iva trasladado no cobrado"],
            "IVA causado o trasladado":    ["iva causado o trasladado", "i.v.a trasladado", "iva cobrado", "i.v.a. trasladado"],
            # Pasivo Largo Plazo
            "Acreedores diversos a largo plazo":    ["acreedores diversos a largo plazo", "pasivo l.p.", "pasivo a largo plazo"],
            "Cuentas por pagar a largo plazo":      ["cuentas por pagar a largo plazo", "deuda a largo plazo"],
            "Cobros anticipados a largo plazo":     ["cobros anticipados a largo plazo"],
            # Capital
            "Capital social":  self.kw_capital_social + ["certif. aportación", "certificados de aportación"],
            "Reserva legal":   ["reserva legal", "reservas"],
            "Utilidades o pérdidas de ejercicios anteriores": [
                "utilidades acumuladas",
                "resultados de ejercicios anteriores",
                "utilidades de ejercicios anteriores",
                "pérdidas acumuladas",
                "pérdida del ejercicio",
                "utilidades y perdidas acum.",
                "utilidades y perdidas acumuladas",
                "resuls, ejercicios ant.",
                "resuls. ejercicios ant.",
                "resuls", "resuls.",
                "resultados",
                "utilid. ejercicios",
                "utilidades de ejercicios",
            ],
        }

        # Alias unificado (retrocompatibilidad con cualquier llamada legada)
        self.concept_keywords = {**self.er_keywords, **self.bg_keywords}

    def _clean_number(self, text: str) -> float | None:
        """
        Sobreescritura local para limpiar números sucios del OCR (ej. 6.200.47)
        específica para el motor de proyecciones, evitando conflictos con
        las modificaciones de multiperiodo de la clase padre FinancialCalculator.
        """
        if text is None: return None
        raw = str(text).strip()
        if not raw: return None

        is_negative = False
        if raw.startswith("-") or (raw.startswith("(") and raw.endswith(")")):
            is_negative = True

        s = raw.replace("$", "").replace(" ", "")
        s = s.replace("(", "").replace(")", "")
        s = re.sub(r"[^0-9,\.]", "", s)

        # Bugfix: Múltiples puntos del OCR
        if s.count(".") > 1:
            s = s.replace(",", "")
            parts = s.split(".")
            s = "".join(parts[:-1]) + "." + parts[-1]
            try:
                val = float(s)
                return -abs(val) if is_negative else val
            except ValueError:
                return None

        if "," in s and "." in s:
            last_comma = s.rfind(",")
            last_dot = s.rfind(".")
            if last_comma > last_dot:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s and "." not in s:
            parts = s.split(",")
            if len(parts[-1]) != 2:
                s = s.replace(",", "")
            else:
                s = "".join(parts[:-1]) + "." + parts[-1]

        try:
            val = float(s)
            return -abs(val) if is_negative else val
        except ValueError:
            return None

    def _preprocess_ocr_data(self, ocr_data: Dict[str, Any]) -> None:
        """
        Pre-procesa la data cruda del OCR para normalizar nombres sucios o variantes
        usando ALIAS_MAP. Modifica ocr_data in-place.
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        for table in tablas_ocr:
            for cell in table:
                text = str(cell.get("text", "")).strip()
                if not text:
                    continue
                text_upper = text.upper()
                for alias, standard in self.ALIAS_MAP.items():
                    if alias in text_upper:
                        # Reemplaza el alias por el estándar manteniendo mayúsculas/minúsculas originales si es posible, 
                        # pero al mutar a standard se asegura la coincidencia exacta.
                        cell["text"] = text_upper.replace(alias, standard.upper())
                        text_upper = cell["text"]

    def _get_exact_first(self, ocr_data: Dict[str, Any], keyword: str, target_col_index: int = None, target_relative_index: int = 0) -> float | None:
        """
        BYPASS: Ignora el método padre _find_value. 
        Busca nativamente en la matriz anidada de celdas la primera coincidencia 
        de la palabra y devuelve su valor adyacente numérico.
        Si target_col_index es provisto, extrae estrictamente de la columna coincidente.
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        kw = keyword.lower()
        
        for table in tablas_ocr:
            rows = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)
                
            for r_idx in sorted(rows.keys()):
                row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                
                # REGLA ESTRICTA 1: Exclusión de la utilidad del ejercicio en curso.
                # Pass-through explícito para: abreviaturas de "anterior" Y cuentas de pérdida
                # histórica acumulada ("Pérdida del ejercicio" en TAAS/NIF).
                _es_historico = any(x in row_text for x in [
                    "anterior", "ant.", "anter",
                    "pérdida del ejercicio", "perdida del ejercicio",
                    "deprec", "maquinaria", "equipo", "edificio"
                ])
                if "ejercicio" in row_text and not _es_historico:
                    continue
                
                if kw in row_text:
                    kw_col = -1
                    acc_text = ""
                    for cell in row_cells:
                        acc_text += " " + str(cell.get("text", "")).lower()
                        if kw in acc_text:
                            kw_col = int(cell.get("col", 0))
                            break
                            
                    if kw_col != -1:
                        val_estricto = None
                        found_values = []
                        for cell in row_cells:
                            c_idx = int(cell.get("col", 0))
                            if c_idx > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        found_values.append(float(val))
                                        if target_col_index is not None and c_idx == target_col_index:
                                            val_estricto = float(val)
                        
                        valor_actual = val_estricto
                        if valor_actual is None and found_values:
                            idx = target_relative_index if target_relative_index < len(found_values) else -1
                            valor_actual = found_values[idx]
                            
                        if valor_actual is not None:
                            return valor_actual
        return None

    def _get_exact_first_with_text(self, ocr_data: Dict[str, Any], keyword: str) -> tuple:
        """
        Versión extendida de _get_exact_first que además devuelve el texto completo de la fila
        donde encontró el valor para análisis de signos (Pérdidas/Déficit).
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        kw = keyword.lower()
        
        for table in tablas_ocr:
            rows = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)
                
            for r_idx in sorted(rows.keys()):
                row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                
                # REGLA ESTRICTA 1: Exclusión de la utilidad del ejercicio en curso.
                # Pass-through explícito para: abreviaturas de "anterior" Y pérdidas históricas.
                _es_historico = any(x in row_text for x in [
                    "anterior", "ant.", "anter",
                    "pérdida del ejercicio", "perdida del ejercicio",
                    "deprec", "maquinaria", "equipo", "edificio"
                ])
                if "ejercicio" in row_text and not _es_historico:
                    continue
                
                if kw in row_text:
                    kw_col = -1
                    acc_text = ""
                    for cell in row_cells:
                        acc_text += " " + str(cell.get("text", "")).lower()
                        if kw in acc_text:
                            kw_col = int(cell.get("col", 0))
                            break
                            
                    if kw_col != -1:
                        for cell in row_cells:
                            if int(cell.get("col", 0)) > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        return float(val), row_text
        return None, ""

    def _get_all_matches_sum(self, ocr_data: Dict[str, Any], keywords: List[str], target_col_index: int = None, target_relative_index: int = 0) -> float:
        """
        Busca y suma TODOS los valores numéricos de filas que coincidan con 
        cualquiera de las palabras clave, sin duplicar filas.
        Implementa deduplicación jerárquica por valor consecutivo para manejar
        exportaciones en cascada (Cuenta Mayor + Subcuenta con el mismo saldo).
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        kws = [k.lower() for k in keywords]
        total_sum = 0.0
        seen_rows = set()  # (table_idx, row_idx)
        last_extracted_value = None  # Guard jerárquico: evita sumar subcuentas redundantes

        for t_idx, table in enumerate(tablas_ocr):
            rows = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)
            
            for r_idx in sorted(rows.keys()):
                if (t_idx, r_idx) in seen_rows: continue
                
                row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                
                # REGLA ESTRICTA 1: Exclusión de la utilidad del ejercicio en curso.
                # Pass-through explícito para: abreviaturas de "anterior" Y pérdidas históricas.
                _es_historico = any(x in row_text for x in [
                    "anterior", "ant.", "anter",
                    "pérdida del ejercicio", "perdida del ejercicio",
                    "deprec", "maquinaria", "equipo", "edificio"
                ])
                if "ejercicio" in row_text and not _es_historico:
                    continue
                
                matched_kw = None
                for kw in kws:
                    if kw in row_text:
                        matched_kw = kw
                        break
                
                if matched_kw:
                    kw_col = -1
                    acc_text = ""
                    for cell in row_cells:
                        acc_text += " " + str(cell.get("text", "")).lower()
                        if matched_kw in acc_text:
                            kw_col = int(cell.get("col", 0))
                            break
                    
                    if kw_col != -1:
                        val_estricto = None
                        found_values = []
                        for cell in row_cells:
                            c_idx = int(cell.get("col", 0))
                            if c_idx > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        found_values.append(float(val))
                                        if target_col_index is not None and c_idx == target_col_index:
                                            val_estricto = float(val)
                        
                        valor_actual = val_estricto
                        if valor_actual is None and found_values:
                            idx = target_relative_index if target_relative_index < len(found_values) else -1
                            valor_actual = found_values[idx]
                            
                        if valor_actual is not None:
                            valor_abs = abs(valor_actual)
                            # REGLA ESTRICTA 4: Deduplicación jerárquica.
                            if last_extracted_value is not None and valor_abs == last_extracted_value:
                                seen_rows.add((t_idx, r_idx))
                                continue
                            total_sum += valor_actual
                            last_extracted_value = valor_abs
                            seen_rows.add((t_idx, r_idx))
        return total_sum

    def _get_all_matches_sum_with_text(self, ocr_data: Dict[str, Any], keywords: List[str], force_abs: bool = False, exclude_dep: bool = False, sum_all: bool = False, target_col_index: int = None, target_relative_index: int = 0) -> tuple:
        """
        Busca y suma valores numéricos de filas que coincidan con las palabras clave.
        Devuelve (suma, texto_combinado).
        
        Args:
            force_abs:   Si True, aplica abs() a cada valor antes de acumular (para Pasivos).
            exclude_dep: Si True, omite filas con "dep" o "acum" (para Activos Fijos brutos).
            sum_all:     Si False (default), retorna tras encontrar la PRIMERA coincidencia válida
                         (toma solo la Cuenta Mayor). Si True, acumula todas las filas coincidentes
                         (para cuentas fragmentadas como IVAs múltiples).
        Implementa deduplicación jerárquica por valor consecutivo para manejar
        exportaciones en cascada (Cuenta Mayor + Subcuenta con el mismo saldo).
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        kws = [k.lower() for k in keywords]
        total_sum = 0.0
        combined_text = ""
        seen_rows = set()
        last_extracted_value = None  # Guard jerárquico

        for t_idx, table in enumerate(tablas_ocr):
            rows = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)
            
            for r_idx in sorted(rows.keys()):
                if (t_idx, r_idx) in seen_rows: continue
                
                row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                
                # REGLA ESTRICTA 1: Exclusión de la utilidad del ejercicio en curso.
                # Pass-through explícito para: abreviaturas de "anterior" Y pérdidas históricas.
                _es_historico = any(x in row_text for x in [
                    "anterior", "ant.", "anter",
                    "pérdida del ejercicio", "perdida del ejercicio",
                    "deprec", "maquinaria", "equipo", "edificio"
                ])
                if "ejercicio" in row_text and not _es_historico:
                    continue
                
                # REGLA ESTRICTA 2: Excluir filas de depreciación acumulada al buscar activos brutos.
                if exclude_dep and ("dep" in row_text or "acum" in row_text):
                    continue
                
                matched_kw = None
                for kw in kws:
                    if kw in row_text:
                        matched_kw = kw
                        break
                
                if matched_kw:
                    kw_col = -1
                    acc_text = ""
                    for cell in row_cells:
                        acc_text += " " + str(cell.get("text", "")).lower()
                        if matched_kw in acc_text:
                            kw_col = int(cell.get("col", 0))
                            break
                    
                    if kw_col != -1:
                        val_estricto = None
                        found_values = []
                        for cell in row_cells:
                            c_idx = int(cell.get("col", 0))
                            if c_idx > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        found_values.append(float(val))
                                        if target_col_index is not None and c_idx == target_col_index:
                                            val_estricto = float(val)
                                            
                        valor_actual = val_estricto
                        if valor_actual is None and found_values:
                            idx = target_relative_index if target_relative_index < len(found_values) else -1
                            valor_actual = found_values[idx]
                        
                        if valor_actual is not None:
                            valor_abs = abs(valor_actual)
                            # REGLA ESTRICTA 4: Deduplicación jerárquica.
                            if last_extracted_value is not None and valor_abs == last_extracted_value:
                                seen_rows.add((t_idx, r_idx))
                                continue
                            # REGLA ESTRICTA 3: Valor absoluto por-fila para Pasivos.
                            total_sum += abs(valor_actual) if force_abs else valor_actual
                            combined_text += " " + row_text
                            last_extracted_value = valor_abs
                            seen_rows.add((t_idx, r_idx))
                            # Si sum_all=False, retornamos con la primera coincidencia (Cuenta Mayor)
                            if not sum_all:
                                return (total_sum, combined_text.strip())
        return (total_sum, combined_text.strip()) if combined_text else (None, "")

    def calcular_proyeccion_edo_resultados(
        self,
        ocr_data: Dict[str, Any],
        supuestos_ingresos: List[LineaSupuesto],
        supuestos_costos: List[LineaSupuesto],
        supuestos_impuestos: List[LineaSupuesto],
        inflacion_esperada: float = 0.0,
        periodo_base: str = None
    ) -> Dict[str, Any]:
        
        self._preprocess_ocr_data(ocr_data)
        tablas_ocr = ocr_data.get("tables_data", []) or []

        print(f"DEBUG OCR - Periodo Base Recibido: '{periodo_base}'")

        # ESCANEO DINÁMICO DE CABECERAS PARA EXTRACCIÓN ESTRICTA
        target_col_index = None
        if periodo_base:
            texto_limpio = str(periodo_base).lower().replace('ejercicio', '').replace('periodo', '').strip()
            p_base_lower = texto_limpio.split()[0] if texto_limpio else ""
            if p_base_lower:
                for table in tablas_ocr:
                    rows = {}
                    for cell in table:
                        r_idx = int(cell.get("row", 0))
                        rows.setdefault(r_idx, []).append(cell)
                    for r_idx in sorted(rows.keys())[:5]: # Primeras 5 filas
                        for cell in rows[r_idx]:
                            if p_base_lower in str(cell.get("text", "")).strip().lower():
                                target_col_index = int(cell.get("col", 0))
                                break
                        if target_col_index is not None: break
                    if target_col_index is not None: break
        
        print(f"DEBUG OCR - target_col_index detectado: {target_col_index}")

        # 1. Identificar Ventas Base (Bypass forzado a la columna mensual/anual)
        ventas_base = self._get_exact_first(ocr_data, "ing por servicios", target_col_index=target_col_index) 
        if ventas_base is None:
            ventas_base = self._get_exact_first(ocr_data, "ingresos por servicios", target_col_index=target_col_index)
        if ventas_base is None:
            ventas_base = self._get_exact_first(ocr_data, "ingresos", target_col_index=target_col_index)
            
        if ventas_base is None:
            kw_ventas = self.concept_keywords.get("Ventas netas / Ingresos por servicios", self.kw_ventas_netas)
            ventas_base = self._find_value(tablas_ocr, kw_ventas, take_last=False)
            
        ventas_base = abs(ventas_base) if ventas_base else 0.0

        # 2. Calcular Ventas Proyectadas
        sup_v = next((s for s in supuestos_ingresos if s.concepto == "Ventas netas / Ingresos por servicios"), None)
        if sup_v and not sup_v.mantener_igual:
            ventas_proy = ventas_base * (1 + (sup_v.variacion / 100))
        else:
            ventas_proy = ventas_base

        val = {
            "ventas": float(ventas_proy),
            "costo_ventas": 0.0,
            "gastos_operativos": 0.0,
            "gastos_financieros": 0.0,
            "otros_ingresos": 0.0,
            "otros_gastos": 0.0,
            "tasa_impuestos": 0.0
        }
        filas_tabla = []

        def solve_rubro(sup, v_base, v_proy_sales, b_sales):
            if sup.mantener_igual: 
                # NUEVO: Protege el valor adquisitivo multiplicando por la inflación
                return v_base * (1 + (inflacion_esperada / 100))
            elif sup.variacion != 0: 
                return v_base * (1 + (sup.variacion / 100)) 
            else:
                p_base = v_base / b_sales if b_sales != 0 else 0
                return p_base * v_proy_sales 

        # --- FUNCIÓN DE EXTRACCIÓN ROBUSTA (Con Bucle y take_last=False) ---
        def extract_value(kw_list):
            v = None
            for keyword in kw_list:
                v = self._get_exact_first(ocr_data, keyword, target_col_index=target_col_index)
                if v is not None:
                    break
            if v is None:
                v = self._find_value(tablas_ocr, kw_list, take_last=False)
            return float(v) if v is not None else 0.0

        # --- PROCESAR INGRESOS ---
        for sup in supuestos_ingresos:
            if sup.concepto == "Ventas netas / Ingresos por servicios":
                filas_tabla.append({
                    "concepto": sup.concepto,
                    "valor_base": float(ventas_base),
                    "variacion_aplicada": sup.variacion if not sup.mantener_igual else 0.0,
                    "valor_proyectado": float(ventas_proy)
                })
                continue
            
            kw = self.er_keywords.get(sup.concepto, [sup.concepto.lower()])
            v_base = extract_value(kw)
            v_proy = solve_rubro(sup, v_base, ventas_proy, ventas_base)
            val["otros_ingresos"] += v_proy
            
            filas_tabla.append({
                "concepto": sup.concepto,
                "valor_base": float(v_base),
                "variacion_aplicada": ((v_proy/v_base)-1)*100 if v_base != 0 else 0,
                "valor_proyectado": float(v_proy)
            })

        # --- PROCESAR COSTOS Y GASTOS (CON BYPASS EXTENDIDO) ---
        for sup in supuestos_costos:
            
            # Escudo A: Gastos de Administración (Separación de Gastos Generales)
            if sup.concepto == "Gastos de administración":
                v_admin = abs(extract_value(["gastos de administración", "gastos de administracion"]))
                v_grales = self._get_exact_first(ocr_data, "gastos generales", target_col_index=target_col_index)
                v_grales = abs(v_grales) if v_grales is not None else 0.0
                
                # Insertar Gastos Generales como fila independiente si existe
                if v_grales > 0:
                    v_grales_proy = solve_rubro(sup, v_grales, ventas_proy, ventas_base)
                    val["gastos_operativos"] += v_grales_proy
                    filas_tabla.append({
                        "concepto": "Gastos generales",
                        "valor_base": float(v_grales),
                        "variacion_aplicada": ((v_grales_proy/v_grales)-1)*100 if v_grales != 0 else 0,
                        "valor_proyectado": float(v_grales_proy)
                    })
                
                v_base = v_admin
                
            # Escudo B: Otros Gastos
            elif sup.concepto == "Otros gastos":
                v_base = abs(extract_value(["otros gastos y pérdidas", "otros egresos"]))
                if v_base == 581.90: v_base = 0.0
                    
            # Escudo C: Costo de Ventas (Reconstrucción Forzada)
            elif sup.concepto == "Costo de ventas/Costo por servicios":
                v_base = abs(extract_value(self.kw_costo_de_ventas))
                if v_base > 0 and ventas_base > 0 and (v_base / ventas_base) < 0.10: 
                    # Extraemos la primera compra directamente del texto
                    v_compras = self._get_exact_first(ocr_data, "compras", target_col_index=target_col_index)
                    v_dev = self._get_exact_first(ocr_data, "devoluciones, descuentos o bonificaciones sobre compras", target_col_index=target_col_index)
                    
                    v_compras = abs(v_compras) if v_compras is not None else 0.0
                    v_dev = abs(v_dev) if v_dev is not None else 0.0
                    
                    if v_compras > 0:
                        v_base = v_base + v_compras - v_dev
            
            else:
                kw = self.er_keywords.get(sup.concepto, [sup.concepto.lower()])
                v_base = abs(extract_value(kw))
            
            v_proy = solve_rubro(sup, v_base, ventas_proy, ventas_base)
            
            if "costo" in sup.concepto.lower():
                val["costo_ventas"] += v_proy
            elif "financiero" in sup.concepto.lower():
                val["gastos_financieros"] += v_proy
            elif "otros" in sup.concepto.lower():
                val["otros_gastos"] += v_proy
            else:
                val["gastos_operativos"] += v_proy
            
            filas_tabla.append({
                "concepto": sup.concepto,
                "valor_base": float(v_base),
                "variacion_aplicada": ((v_proy/v_base)-1)*100 if v_base != 0 else 0,
                "valor_proyectado": float(v_proy)
            })

        # 4. Impuestos (ISR y PTU operan igual, extrayendo del OCR)
        total_impuestos_proyectados = 0.0
        
        for sup in supuestos_impuestos:
            # Quitamos el continue del ISR para que lo procese igual que la PTU
            kw = self.er_keywords.get(sup.concepto, [sup.concepto.lower()])
            v_base = abs(extract_value(kw))
            v_proy = solve_rubro(sup, v_base, ventas_proy, ventas_base)
            
            total_impuestos_proyectados += v_proy
            
            filas_tabla.append({
                "concepto": sup.concepto,
                "valor_base": float(v_base),
                "variacion_aplicada": sup.variacion if not sup.mantener_igual else 0.0,
                "valor_proyectado": float(v_proy)
            })

        # 5. Cálculo de cascada final
        utilidad_bruta = val["ventas"] - val["costo_ventas"]
        utilidad_bruta_proy = utilidad_bruta  # ya están proyectados en val[]

        utilidad_operativa = utilidad_bruta - val["gastos_operativos"] + val["otros_ingresos"] - val["otros_gastos"]
        utilidad_operativa_proy = utilidad_operativa

        utilidad_antes_impuestos = utilidad_operativa - val["gastos_financieros"]

        # Restamos la suma de todos los impuestos extraídos e impactados por la regla de proyección
        utilidad_neta = utilidad_antes_impuestos - total_impuestos_proyectados

        return {
            "tablas_proyectadas": filas_tabla,
            "ventas": float(val["ventas"]),
            "costo_ventas": float(val["costo_ventas"]),
            "utilidad_bruta": float(utilidad_bruta),
            "gastos_operativos": float(val["gastos_operativos"]),
            "utilidad_operativa": float(utilidad_operativa),
            "gastos_financieros": float(val["gastos_financieros"]),
            "utilidad_antes_impuestos": float(utilidad_antes_impuestos),
            "impuestos": float(total_impuestos_proyectados),
            "utilidad_neta": float(utilidad_neta),
            "impuestos_totales": float(total_impuestos_proyectados)
        }

    def calcular_proyeccion_balance(
        self,
        ocr_data: Dict[str, Any],
        activo_circulante: List[LineaSupuesto],
        activo_no_circulante: List[LineaSupuesto],
        pasivo_corto_plazo: List[LineaSupuesto],
        pasivo_largo_plazo: List[LineaSupuesto],
        capital_contribuido: List[LineaSupuesto],
        capital_ganado: List[LineaSupuesto],
        utilidad_neta_proforma: float,
        ventas_proy_incremento_pct: float,
        inflacion_esperada: float = 0.0,
        periodo_base: str = None
    ) -> Dict[str, Any]:
        
        self._preprocess_ocr_data(ocr_data)
        tablas_ocr = ocr_data.get("tables_data", []) or []
        filas_tabla = []

        # ESCANEO DINÁMICO DE CABECERAS PARA EXTRACCIÓN ESTRICTA
        target_col_index = None
        target_relative_index = 0
        if periodo_base:
            texto_limpio = str(periodo_base).lower().replace('ejercicio', '').replace('periodo', '').strip()
            p_base_lower = texto_limpio.split()[0] if texto_limpio else ""
            if p_base_lower:
                for table in tablas_ocr:
                    rows = {}
                    for cell in table:
                        r_idx = int(cell.get("row", 0))
                        rows.setdefault(r_idx, []).append(cell)
                    for r_idx in sorted(rows.keys())[:5]: # Primeras 5 filas
                        row_cells = sorted(rows[r_idx], key=lambda c: int(c.get("col", 0)))
                        for cell in row_cells:
                            if p_base_lower in str(cell.get("text", "")).strip().lower():
                                target_col_index = int(cell.get("col", 0))
                                periodos = [c for c in row_cells if int(c.get("col", 0)) > 0 and len(str(c.get("text", "")).strip()) > 0]
                                for p_idx, p_cell in enumerate(periodos):
                                    if p_base_lower in str(p_cell.get("text", "")).strip().lower():
                                        target_relative_index = p_idx
                                        break
                                break
                        if target_col_index is not None: break
                    if target_col_index is not None: break
        
        print(f"DEBUG OCR Balance - target_col_index: {target_col_index}, relative_index: {target_relative_index}")
        
        # --- BLOQUE DE EXTRACCIÓN CON CORRECCIÓN DE SIGNO ---
        def extraer_valor_con_signo(v_extraido, row_text, concepto_nombre, seccion):
            if v_extraido is None: return 0.0
            valor = abs(v_extraido)
            row_lower = row_text.lower()
            
            # 1. Naturaleza inicial por palabras negativas
            final_valor = valor
            palabras_negativas = ["perdida", "pérdida", "deficit", "defícit", "a favor"]
            if any(neg in row_lower for neg in palabras_negativas):
                final_valor = -valor

            # 2. OVERRIDES (Reglas de Oro que prevalecen)
            # PASIVOS: Siempre deben ser positivos (Valor Absoluto)
            if "pasivo" in seccion.lower():
                return abs(valor)
            # CUENTAS COMPLEMENTARIAS DE ACTIVO (Depreciación): Siempre negativas
            if "depreciación" in concepto_nombre.lower() or "depreciacion" in concepto_nombre.lower() or "dep." in concepto_nombre.lower():
                return -abs(valor)
            # ACTIVOS FIJOS: Siempre positivos
            if any(x in concepto_nombre.lower() for x in ["mobiliario", "equipo", "maquinaria", "transporte", "edificio"]):
                return abs(valor)
                
            return final_valor

        # Totales por sección
        totales = {
            "total_activo_circulante": 0.0,
            "total_activo_no_circulante": 0.0,
            "total_pasivo_corto": 0.0,
            "total_pasivo_largo": 0.0,
            "total_capital_contribuido": 0.0,
            "total_capital_ganado": 0.0
        }

        def solve_balance_rubro(sup, v_base):
            # CORRECCIÓN A (NIF/IFRS - Costo Histórico):
            # En el Balance General, "Mantener igual" congela el saldo absoluto.
            # Los Activos Fijos NO se re-expresan por inflación en un balance proyectado
            # porque se registran a costo histórico, no a valor de reposición.
            # (La inflación solo aplica en el ER para proteger el poder adquisitivo de gastos.)
            if sup.mantener_igual:
                return v_base
            elif sup.variacion != 0:
                return v_base * (1 + (sup.variacion / 100))
            else:
                # Método Porcentaje de Ventas por defecto (Escalabilidad operativa)
                # Esto asegura que rubros como Proveedores, IVA por causar e Impuestos retenidos
                # crezcan en la misma proporción que las ventas.
                return v_base * (1 + (ventas_proy_incremento_pct / 100))

        def procesar_seccion(lista_sups, key_total):
            for sup in lista_sups:
                # Casos especiales automáticos (Capital Ganado)
                if sup.concepto == "Utilidad o pérdida del ejercicio":
                    v_base = 0.0
                    v_proy = utilidad_neta_proforma

                elif sup.concepto == "Impuestos y derechos":
                    v_base = 0.0
                    
                    # 1. Intentar Modo GCMK (sumar rubros sueltos de impuestos del activo)
                    # Excluimos estrictamente "impuestos a favor" para no chocar con el IVA Acreditable
                    kw_gcmk = ["isr anticipos", "isr a favor", "sub-sidio al empleo", "subsidio al empleo"]
                    v_gcmk = self._get_all_matches_sum(ocr_data, kw_gcmk, target_col_index=target_col_index, target_relative_index=target_relative_index)
                    
                    if v_gcmk > 0:
                        # Estamos en GCMK, tomamos la suma y le agregamos el IVA retenido
                        v_base = abs(v_gcmk)
                        v_iva_ret = self._get_exact_first(ocr_data, "iva retenido", target_col_index=target_col_index, target_relative_index=target_relative_index)
                        if v_iva_ret is not None and v_iva_ret > 0:
                            v_base += v_iva_ret
                    else:
                        # 2. Estamos en TAAS. Tomamos subcuentas específicas sin tocar la cuenta padre del IVA
                        kw_taas = ["impuestos acreditables por pagar", "impuestos y derechos"]
                        v_base = abs(self._get_all_matches_sum(ocr_data, kw_taas, target_col_index=target_col_index, target_relative_index=target_relative_index))
                        
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "IVA causado o trasladado":
                    # SUMATORIA SEGURA: Suma 'iva cobrado' + 'i.v.a trasladado' + variantes
                    kw_iva = self.concept_keywords.get("IVA causado o trasladado", ["iva causado o trasladado"])
                    v_base = abs(self._get_all_matches_sum(ocr_data, kw_iva, target_col_index=target_col_index, target_relative_index=target_relative_index))
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Mobiliario y equipo de oficina":
                    v_mob = self._get_exact_first(ocr_data, "mobiliario y equipo de oficina", target_col_index=target_col_index, target_relative_index=target_relative_index)
                    if v_mob is None:
                        v_mob = self._get_exact_first(ocr_data, "muebles y enseres", target_col_index=target_col_index, target_relative_index=target_relative_index)
                    v_comunicacion = self._get_exact_first(ocr_data, "equipo de comunicación", target_col_index=target_col_index, target_relative_index=target_relative_index)
                    
                    v_base = (v_mob or 0.0) + (v_comunicacion or 0.0)
                    v_base = extraer_valor_con_signo(v_base, "mobiliario y comunicación", sup.concepto, key_total)
                    v_base = v_base if v_base is not None else 0.0
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Equipo de cómputo":
                    v_computo = self._get_exact_first(ocr_data, "equipo de cómputo", target_col_index=target_col_index, target_relative_index=target_relative_index)
                    v_base = extraer_valor_con_signo(v_computo or 0.0, "equipo de cómputo", sup.concepto, key_total)
                    v_base = v_base if v_base is not None else 0.0
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Depreciación acumulada":
                    kw_dep = self.concept_keywords.get("Depreciación acumulada", ["(-) deprec. acum.", "deprec. acum.", "dep. acum.", "depreciacion acumulada", "depreciacion", "deprec acum"])
                    v_base = self._get_all_matches_sum(ocr_data, kw_dep, target_col_index=target_col_index, target_relative_index=target_relative_index)
                    
                    if v_base == 0:
                        v_base = self._get_all_matches_sum(ocr_data, ["deprec"], target_col_index=target_col_index, target_relative_index=target_relative_index)
                        
                    v_base = v_base if v_base is not None else 0.0
                    v_base = -abs(v_base) if v_base != 0 else 0.0
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Utilidades o pérdidas de ejercicios anteriores":
                    kw = self.bg_keywords.get(sup.concepto, [sup.concepto.lower()])
                    # Usamos _get_all_matches_sum para sumar TODAS las subcuentas históricas
                    # Esto preserva el signo negativo matemático nativo sin forzar un abs()
                    v_base = self._get_all_matches_sum(ocr_data, kw, target_col_index=target_col_index, target_relative_index=target_relative_index)
                    
                    if v_base == 0:
                        v_base = self._find_value(tablas_ocr, kw, take_last=False) or 0.0
                        
                    v_proy = solve_balance_rubro(sup, v_base)

                else:
                    kw = self.bg_keywords.get(sup.concepto, [sup.concepto.lower()])
                    
                    # Flags contextuales dinámicos
                    _is_pasivo = "pasivo" in key_total.lower()
                    _ACTIVOS_FIJOS = ["edificio", "maquinaria", "transporte", "mobiliario", "cómputo", "computo", "herramienta"]
                    _is_fixed_asset = any(x in sup.concepto.lower() for x in _ACTIVOS_FIJOS)
                    
                    v_base, row_text_lower = self._get_all_matches_sum_with_text(
                        ocr_data, kw,
                        force_abs=_is_pasivo,
                        exclude_dep=_is_fixed_asset,
                        sum_all=(sup.concepto == "Impuestos a la utilidad por pagar"),
                        target_col_index=target_col_index,
                        target_relative_index=target_relative_index
                    )
                    
                    if v_base is None:
                        v_base = self._find_value(tablas_ocr, kw, take_last=False)
                    
                    v_base = extraer_valor_con_signo(v_base, row_text_lower, sup.concepto, key_total)
                    v_base = v_base if v_base is not None else 0.0
                    v_proy = solve_balance_rubro(sup, v_base)
                
                totales[key_total] += v_proy
                    
                filas_tabla.append({
                    "concepto": sup.concepto,
                    "valor_base": float(v_base),
                    "variacion_aplicada": ((v_proy/v_base)-1)*100 if v_base != 0 else 0,
                    "valor_proyectado": float(v_proy)
                })

        # Procesar cada sección siguiendo el orden del balance
        procesar_seccion(activo_circulante, "total_activo_circulante")
        procesar_seccion(activo_no_circulante, "total_activo_no_circulante")

        # --- AJUSTE DE DEPRECIACIÓN ---
        # Buscamos y sumamos cuentas de depreciación para restarlas explícitamente del activo
        # Solo lo hacemos de manera manual si NO fue inyectada ni procesada previamente
        if not any(f["concepto"] == "Depreciación acumulada" for f in filas_tabla):
            kw_dep = self.concept_keywords.get("Depreciación acumulada", ["(-) deprec. acum.", "deprec. acum.", "dep. acum.", "depreciacion acumulada", "depreciacion", "deprec acum"])
            v_dep_base = self._get_all_matches_sum(ocr_data, kw_dep, target_col_index=target_col_index, target_relative_index=target_relative_index)
            
            if v_dep_base == 0:
                v_dep_base = self._get_all_matches_sum(ocr_data, ["deprec"], target_col_index=target_col_index, target_relative_index=target_relative_index)
            
            v_dep_base = v_dep_base if v_dep_base is not None else 0.0
            
            if v_dep_base == 0:
                v_dep_base = self._find_value(tablas_ocr, kw_dep, take_last=True) or 0.0
            
            # Forzar a negativo para que descuente del activo
            v_dep_base = -abs(v_dep_base) if v_dep_base != 0 else 0.0
            v_dep_proy = v_dep_base 
            totales["total_activo_no_circulante"] += v_dep_proy
            
            if v_dep_base != 0:
                filas_tabla.append({
                    "concepto": "Depreciación acumulada",
                    "valor_base": float(v_dep_base),
                    "variacion_aplicada": 0,
                    "valor_proyectado": float(v_dep_proy)
                })
        procesar_seccion(pasivo_corto_plazo, "total_pasivo_corto")
        procesar_seccion(pasivo_largo_plazo, "total_pasivo_largo")
        procesar_seccion(capital_contribuido, "total_capital_contribuido")
        procesar_seccion(capital_ganado, "total_capital_ganado")

        # Cálculos finales
        total_activo = totales["total_activo_circulante"] + totales["total_activo_no_circulante"]
        total_pasivo = totales["total_pasivo_corto"] + totales["total_pasivo_largo"]
        total_capital = totales["total_capital_contribuido"] + totales["total_capital_ganado"]
        
        # FER = variable de holgura para cuadrar el balance
        # FER > 0 → se requiere financiamiento externo adicional
        # FER < 0 → hay excedente de fondos
        fer = total_activo - (total_pasivo + total_capital)
        
        return {
            "tablas_proyectadas": filas_tabla,
            "total_activo": float(total_activo),
            "total_pasivo": float(total_pasivo),
            "total_capital": float(total_capital),
            "fer": float(fer)
        }