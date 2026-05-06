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

        self.concept_keywords: Dict[str, List[str]] = {
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
            "ISR": [
                "isr", "impuesto sobre la renta", "impuesto a las ganancias",
            ],
            "PTU (Participación de los Trabajadores en las Utilidades)": [
                "ptu", "participación de los trabajadores en las utilidades",
            ],
            # --- BALANCE GENERAL (Reutilizando etiquetas de la clase padre) ---
            "Caja": ["caja", "efectivo en caja"],
            "Bancos": ["bancos", "efectivo y equivalentes", "efectivo en bancos"],
            "Cuentas por cobrar a clientes": self.kw_cuentas_por_cobrar,
            "Otras cuentas por cobrar (deudores diversos)": ["deudores diversos", "deudores"],
            "Inventarios": self.kw_inventario,
            "IVA acreditable": ["impuestos a favor", "iva a favor", "iva acreditable"],
            "Terrenos": ["terrenos"],
            "Edificios": ["edificios", "inmuebles", "casa oficina"],
            "Maquinaria y equipo": ["maquinaria y equipo", "maquinaria"],
            "Equipo de transporte": [
                "equipo de transporte", 
                "vehículos",
                "automóviles, autobuses, camiones",
                "automóviles",
                "camiones",
                "equipo automotriz"
            ],
            "Mobiliario y equipo de oficina": ["mobiliario y equipo de oficina", "muebles y enseres"],
            "Equipo de cómputo": ["equipo de cómputo", "equipo de comunicación", "cómputo"],
            "Depreciación acumulada": ["dep. acum.", "dep. acumulada", "depreciación acumulada", "depreciacion acumulada", "depreciacion"],
            "Impuestos y derechos": ["impuestos acreditables por pagar", "impuestos acreditables pagados", "impuestos acreditables", "impuestos y derechos", "impuesto acreditable", "isr anticipos", "isr a favor", "sub-sidio al empleo", "ISR ANTICIPOS", "ISR A FAVOR", "SUB-SIDIO AL EMPLEO"],
            "Cuentas por pagar a proveedores": ["proveedores", "cuentas por pagar a proveedores"],
            "Préstamo bancario / Deuda a corto plazo": ["documentos por pagar", "préstamos bancarios", "prestamos bancarios", "deuda a corto plazo"],
            "Acreedores diversos": ["acreedores diversos", "acreedores"],
            "Impuestos a la utilidad por pagar": ["impuestos a la utilidad por pagar", "impuestos por pagar", "impuestos retenidos"],
            "IVA por causar o trasladar": ["iva por causar o trasladar", "iva por causar", "iva trasladado no cobrado"],
            "IVA causado o trasladado": ["iva causado o trasladado", "i.v.a trasladado", "iva cobrado"],
            "Capital social": self.kw_capital_social,
            "Reserva legal": ["reserva legal"],
            "Utilidades o pérdidas de ejercicios anteriores": [
                "utilidades acumuladas",
                "resultados de ejercicios anteriores",
                "utilidades de ejercicios anteriores",
                "pérdidas acumuladas",
                "pérdida del ejercicio",  # Nomenclatura TAAS LOGISTICS (histórico acumulado)
                "utilidades y perdidas acum.",
                "utilidades y perdidas acumuladas",
                "resuls, ejercicios ant.",
                "resuls. ejercicios ant.",
                "resuls",
                "resuls.",
                "resultados"
            ],
        }

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

    def _get_exact_first(self, ocr_data: Dict[str, Any], keyword: str) -> float | None:
        """
        BYPASS: Ignora el método padre _find_value. 
        Busca nativamente en la matriz anidada de celdas la primera coincidencia 
        de la palabra y devuelve su valor adyacente numérico.
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
                    "pérdida del ejercicio", "perdida del ejercicio"
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
                                if texto_celda:  # Si la celda no está vacía
                                    val = self._clean_number(texto_celda)
                                    if val is not None: # Aceptamos el 0.00 como un valor contable real
                                        return float(val)
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
                    "pérdida del ejercicio", "perdida del ejercicio"
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

    def _get_all_matches_sum(self, ocr_data: Dict[str, Any], keywords: List[str]) -> float:
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
                    "pérdida del ejercicio", "perdida del ejercicio"
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
                        for cell in row_cells:
                            if int(cell.get("col", 0)) > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        valor_actual = abs(float(val))
                                        # REGLA ESTRICTA 4: Deduplicación jerárquica.
                                        # Si el valor es idéntico al anterior, es una subcuenta en cascada.
                                        if last_extracted_value is not None and valor_actual == last_extracted_value:
                                            seen_rows.add((t_idx, r_idx))
                                            break
                                        total_sum += float(val)
                                        last_extracted_value = valor_actual
                                        seen_rows.add((t_idx, r_idx))
                                        break
        return total_sum

    def _get_all_matches_sum_with_text(self, ocr_data: Dict[str, Any], keywords: List[str], force_abs: bool = False, exclude_dep: bool = False, sum_all: bool = False) -> tuple:
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
                    "pérdida del ejercicio", "perdida del ejercicio"
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
                        for cell in row_cells:
                            if int(cell.get("col", 0)) > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        valor_actual = abs(float(val))
                                        # REGLA ESTRICTA 4: Deduplicación jerárquica.
                                        if last_extracted_value is not None and valor_actual == last_extracted_value:
                                            seen_rows.add((t_idx, r_idx))
                                            break
                                        # REGLA ESTRICTA 3: Valor absoluto por-fila para Pasivos.
                                        total_sum += abs(float(val)) if force_abs else float(val)
                                        combined_text += " " + row_text
                                        last_extracted_value = valor_actual
                                        seen_rows.add((t_idx, r_idx))
                                        # Si sum_all=False, retornamos con la primera coincidencia (Cuenta Mayor)
                                        if not sum_all:
                                            return (total_sum, combined_text.strip())
                                        break
        return (total_sum, combined_text.strip()) if combined_text else (None, "")

    def calcular_proyeccion_edo_resultados(
        self,
        ocr_data: Dict[str, Any],
        supuestos_ingresos: List[LineaSupuesto],
        supuestos_costos: List[LineaSupuesto],
        supuestos_impuestos: List[LineaSupuesto],
        inflacion_esperada: float = 0.0  # <-- NUEVO: Recibe la inflación global
    ) -> Dict[str, Any]:
        
        self._preprocess_ocr_data(ocr_data)
        tablas_ocr = ocr_data.get("tables_data", []) or []
        
        # 1. Identificar Ventas Base (Bypass forzado a la columna mensual)
        ventas_base = self._get_exact_first(ocr_data, "ing por servicios") 
        if ventas_base is None:
            ventas_base = self._get_exact_first(ocr_data, "ingresos por servicios")
        if ventas_base is None:
            ventas_base = self._get_exact_first(ocr_data, "ingresos")
            
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
                v = self._get_exact_first(ocr_data, keyword)
                if v is not None:
                    break
            if v is None:
                v = self._find_value(tablas_ocr, kw_list, take_last=False)
            return abs(v)

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
            
            kw = self.concept_keywords.get(sup.concepto, [sup.concepto.lower()])
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
                v_admin = extract_value(["gastos de administración", "gastos de administracion"])
                v_grales = self._get_exact_first(ocr_data, "gastos generales")
                if v_grales is None: v_grales = 0.0
                
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
                v_base = extract_value(["otros gastos y pérdidas", "otros egresos"])
                if v_base == 581.90: v_base = 0.0
                    
            # Escudo C: Costo de Ventas (Reconstrucción Forzada)
            elif sup.concepto == "Costo de ventas/Costo por servicios":
                v_base = extract_value(self.kw_costo_de_ventas)
                if v_base > 0 and ventas_base > 0 and (v_base / ventas_base) < 0.10: 
                    # Extraemos la primera compra directamente del texto
                    v_compras = self._get_exact_first(ocr_data, "compras")
                    v_dev = self._get_exact_first(ocr_data, "devoluciones, descuentos o bonificaciones sobre compras")
                    
                    v_compras = v_compras if v_compras is not None else 0.0
                    v_dev = v_dev if v_dev is not None else 0.0
                    
                    if v_compras > 0:
                        v_base = v_base + v_compras - v_dev
            
            else:
                kw = self.concept_keywords.get(sup.concepto, [sup.concepto.lower()])
                v_base = extract_value(kw)
            
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

        # --- PROCESAR IMPUESTOS ---
        sup_isr = next((s for s in supuestos_impuestos if "isr" in s.concepto.lower()), None)
        val["tasa_impuestos"] = sup_isr.variacion if sup_isr else 0.0
        
        val_ptu = 0.0
        for sup in supuestos_impuestos:
            if "isr" in sup.concepto.lower(): continue
            kw = self.concept_keywords.get(sup.concepto, [sup.concepto.lower()])
            v_base = extract_value(kw)
            v_proy = solve_rubro(sup, v_base, ventas_proy, ventas_base)
            val_ptu += v_proy
            
            filas_tabla.append({
                "concepto": sup.concepto,
                "valor_base": float(v_base),
                "variacion_aplicada": ((v_proy/v_base)-1)*100 if v_base != 0 else 0,
                "valor_proyectado": float(v_proy)
            })

        # --- ARITMÉTICA DE CASCADA ---
        utilidad_bruta = val["ventas"] - val["costo_ventas"]
        utilidad_operativa = utilidad_bruta - val["gastos_operativos"] + val["otros_ingresos"] - val["otros_gastos"]
        utilidad_antes_impuestos = utilidad_operativa - val["gastos_financieros"]
        
        # NUEVO: Escudo anti-impuestos sobre pérdidas
        if utilidad_antes_impuestos > 0:
            impuestos_calculados = utilidad_antes_impuestos * (val["tasa_impuestos"] / 100)
        else:
            impuestos_calculados = 0.0
            
        impuestos_finales = impuestos_calculados + val_ptu
        
        utilidad_neta = utilidad_antes_impuestos - impuestos_finales

        return {
            "tablas_proyectadas": filas_tabla,
            "ventas": float(val["ventas"]),
            "costo_ventas": float(val["costo_ventas"]),
            "utilidad_bruta": float(utilidad_bruta),
            "gastos_operativos": float(val["gastos_operativos"]),
            "utilidad_operativa": float(utilidad_operativa),
            "gastos_financieros": float(val["gastos_financieros"]),
            "utilidad_antes_impuestos": float(utilidad_antes_impuestos),
            "impuestos": float(impuestos_finales),
            "utilidad_neta": float(utilidad_neta),
            "impuestos_totales": float(impuestos_finales)
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
        inflacion_esperada: float = 0.0
    ) -> Dict[str, Any]:
        
        self._preprocess_ocr_data(ocr_data)
        tablas_ocr = ocr_data.get("tables_data", []) or []
        filas_tabla = []
        
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
                    # Buscar y SUMAR las cuentas fiscales globales
                    kw_imp = [
                        "impuestos acreditables por pagar", "impuestos acreditables pagados", 
                        "impuestos acreditables", "impuestos y derechos", "impuesto acreditable", 
                        "impuestos por recuperar", "isr anticipos", "isr a favor", 
                        "sub-sidio al empleo", "subsidio al empleo"
                    ] # <-- Se eliminó "iva retenido" de aquí
                    v_base = self._get_all_matches_sum(ocr_data, kw_imp)
                    v_base = abs(v_base)
                    
                    # PARCHE ANTI-COLISIÓN: IVA Retenido (GCMK vs TAAS)
                    # Solo lo sumamos al Activo si el OCR lo extrajo como un valor positivo (Naturaleza deudora)
                    v_iva_ret = self._get_exact_first(ocr_data, "iva retenido")
                    if v_iva_ret is not None and v_iva_ret > 0:
                        v_base += v_iva_ret
                        
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Mobiliario y equipo de oficina":
                    v_mob = self._get_exact_first(ocr_data, "mobiliario y equipo de oficina")
                    if v_mob is None:
                        v_mob = self._get_exact_first(ocr_data, "muebles y enseres")
                    v_comunicacion = self._get_exact_first(ocr_data, "equipo de comunicación")
                    
                    v_base = (v_mob or 0.0) + (v_comunicacion or 0.0)
                    v_base = extraer_valor_con_signo(v_base, "mobiliario y comunicación", sup.concepto, key_total)
                    v_base = v_base if v_base is not None else 0.0
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Equipo de cómputo":
                    v_computo = self._get_exact_first(ocr_data, "equipo de cómputo")
                    v_base = extraer_valor_con_signo(v_computo or 0.0, "equipo de cómputo", sup.concepto, key_total)
                    v_base = v_base if v_base is not None else 0.0
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Utilidades o pérdidas de ejercicios anteriores":
                    kw = self.concept_keywords.get(sup.concepto, [sup.concepto.lower()])
                    # Usamos _get_all_matches_sum para sumar TODAS las subcuentas históricas
                    # Esto preserva el signo negativo matemático nativo sin forzar un abs()
                    v_base = self._get_all_matches_sum(ocr_data, kw)
                    
                    if v_base == 0:
                        v_base = self._find_value(tablas_ocr, kw, take_last=False) or 0.0
                        
                    v_proy = solve_balance_rubro(sup, v_base)

                else:
                    kw = self.concept_keywords.get(sup.concepto, [sup.concepto.lower()])
                    
                    # Flags contextuales dinámicos
                    _is_pasivo = "pasivo" in key_total.lower()
                    _ACTIVOS_FIJOS = ["edificio", "maquinaria", "transporte", "mobiliario", "cómputo", "computo", "herramienta"]
                    _is_fixed_asset = any(x in sup.concepto.lower() for x in _ACTIVOS_FIJOS)
                    
                    v_base, row_text_lower = self._get_all_matches_sum_with_text(
                        ocr_data, kw,
                        force_abs=_is_pasivo,
                        exclude_dep=_is_fixed_asset,
                        sum_all=any(x in sup.concepto.lower() for x in ["iva", "impuesto"])
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
        kw_dep = self.concept_keywords.get("Depreciación acumulada", ["depreciacion", "dep. acum."])
        v_dep_base = self._get_all_matches_sum(ocr_data, kw_dep)
        
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