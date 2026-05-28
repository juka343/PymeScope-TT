import re
from decimal import Decimal, ROUND_HALF_UP
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
            # ── Aliases originales (GCMK) ─────────────────────────────────────────
            "IVA COBRADO":              "IVA causado o trasladado",
            "IVA A FAVOR EJER ANT":     "IVA acreditable",
            "CASA OFICINA":             "Edificios",
            "EQUIPO AUTOMOTRIZ":        "Equipo de transporte",

            # ── Activo Fijo — variantes sin acento o sin preposición (NIF C-6) ────
            # Despegue Digital y PDFs informales usan estos formatos
            "EQUIPO COMPUTO":           "Equipo de cómputo",
            "EQUIPO DE COMPUTO":        "Equipo de cómputo",
            "EQUIPOS DE COMPUTO":       "Equipo de cómputo",
            "EQUIPOS DE CÓMPUTO":       "Equipo de cómputo",
            "MUEBLES Y ENSERES":        "Mobiliario y equipo de oficina",
            "EQUIPO DE OFICINA":        "Mobiliario y equipo de oficina",
            "FLOTILLA":                 "Equipo de transporte",
            "FLOTILLA VEHICULAR":       "Equipo de transporte",
            "UNIDADES DE REPARTO":      "Equipo de transporte",
            "VEHICULOS":                "Equipo de transporte",
            "VEHÍCULOS":                "Equipo de transporte",
            "CONSTRUCCIONES":           "Edificios",
            "INMUEBLES":                "Edificios",
            "PREDIOS":                  "Terrenos",
            "MARCAS Y PATENTES":        "Patentes",

            # ── Pagos anticipados — variantes comunes (NIF B-6) ───────────────────
            "RENTAS ANTICIPADAS":       "Rentas pagadas por anticipado",
            "SEGUROS ANTICIPADOS":      "Seguros y fianzas",
            "PRIMAS DE SEGURO":         "Seguros y fianzas",
            "ANTICIPOS A PROVEEDORES":  "Anticipo a proveedores",

            # ── Capital — variantes comunes (NIF B-6, LGSM) ───────────────────────
            "CERTIF. APORTACION":       "Capital social",
            "CERTIF APORTACION":        "Capital social",
            "CERTIF. APORTACIÓN":       "Capital social",
            "APORTACIONES DE SOCIOS":   "Capital social",
            "CAP. SOCIAL":              "Capital social",           # ← NUEVO: CASO 5 BG
            "CAPITAL SOCIAL":           "Capital social",           # ← NUEVO: variante explícita
            "UTILID. EJERCICIOS":       "Utilidades o pérdidas de ejercicios anteriores",
            "UTILID. EJERC. ANT.":      "Utilidades o pérdidas de ejercicios anteriores",
            "UTILIDADES RETENIDAS":     "Utilidades o pérdidas de ejercicios anteriores",
            "SUPERAVIT ACUMULADO":      "Utilidades o pérdidas de ejercicios anteriores",
            "UTILIDADES":               "Utilidades o pérdidas de ejercicios anteriores", # ← NUEVO: CASO 5 BG

            # ── Empresas públicas — Activo Fijo consolidado (NIF C-6) ─────────────
            "PROPIEDAD, PLANTA Y EQUIPO":        "Maquinaria y equipo",
            "PROPIEDAD PLANTA Y EQUIPO":         "Maquinaria y equipo",
            "PROPIEDADES, PLANTA Y EQUIPO":      "Maquinaria y equipo",
            "PROPIEDAD DE INVERSION":            "Edificios",

            # ── Empresas públicas — Capital consolidado (NIF B-8 / NIIF 10) ───────
            "CAPITAL CONTABLE MAYORITARIO":      "Capital social",
            "CAPITAL CONTABLE MINORITARIO":      "Participación no controladora",
            "CAPITAL CONTABLE CONTROLADORA":     "Capital social",
            "PARTICIPACION CONTROLADORA":        "Capital social",
            "PARTICIPACION NO CONTROLADORA":     "Participación no controladora",

            # ── Activo Fijo — abreviaciones con punto (NIF C-6) ───────────────────
            "EQ. TRANSPORTE":           "Equipo de transporte",    # ← NUEVO: CASO 5 BG
            "EQ. CÓMPUTO":              "Equipo de cómputo",       # ← NUEVO: CASO 5 BG
            "EQ. COMPUTO":              "Equipo de cómputo",       # ← NUEVO: CASO 5 BG
            "EQ DE TRANSPORTE":         "Equipo de transporte",    # ← NUEVO: variante sin punto
            "EQ DE COMPUTO":            "Equipo de cómputo",       # ← NUEVO: variante sin punto

            # ── Intangibles y otros activos (NIF C-8) ─────────────────────────────
            "GASTOS INSTALACIÓN":       "Gastos de instalación",   # ← NUEVO: CASO 5 BG
            "GASTOS INSTALACION":       "Gastos de instalación",   # ← NUEVO: sin acento
            "GASTOS DE INSTALACION":    "Gastos de instalación",   # ← NUEVO: variante larga
            "GASTOS DE INSTALACIÓN":    "Gastos de instalación",   # ← NUEVO: variante larga con acento

            # ── ER — variantes de gastos operativos (NIF B-3) ─────────────────────
            "GASTOS DE OPERACION":       "Gastos de venta",        # existente
            "GASTOS DE OPERACIÓN":       "Gastos de venta",        # existente
            "GASTOS DE ADMINISTRACION":  "Gastos de administración", # ← NUEVO: GCMK sin acento
        }

        # ─── DICCIONARIO DEL ESTADO DE RESULTADOS ───────────────────────────────
        # Alias para cuentas de INGRESOS, COSTOS, GASTOS e IMPUESTOS (gasto).
        # Nunca debe usarse al procesar el Balance General.
        self.er_keywords: Dict[str, List[str]] = {
            "Ventas netas / Ingresos por servicios": [
                "ventas netas",         # ← NUEVO: formato más común en PDFs mexicanos
                "ventas netas anuales", # ← NUEVO: variante anual
                *self.kw_ventas_netas,  # mantiene todos los keywords existentes
            ],
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
            "Caja":                                    ["caja", "efectivo", "caja chica", "fondo fijo", "efectivo en caja", "efectivo y equivalentes"],
            "Bancos":                                  ["bancos", "efectivo en bancos"],
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
            "Rentas pagadas por anticipado":           ["rentas pagadas por anticipado", "rentas anticipadas"],
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
            "Equipo de cómputo":         ["equipo de cómputo", "cómputo", "equipo cómputo"],
            "Marcas":                    ["marcas"],
            "Patentes":                  ["patentes", "marcas y patentes"],
            "Licencias de software": [
                "licencias de software",
                "licencias",
                "software",
                # ── NUEVO: intangibles y cargos diferidos (NIF C-8) ───────────────
                # Los gastos de instalación son activos intangibles amortizables
                # sin sustancia física — se agrupan aquí al no tener cuenta propia.
                "gastos de instalación",      # ← CASO 5 BG — post-ALIAS_MAP
                "gastos de instalacion",      # ← sin acento
                "gastos preoperativos",       # ← variante común en PyMEs
                "cargos diferidos",           # ← término SAT y planes de cuentas MX
                "mejoras a locales",          # ← mejoras a locales arrendados
                "gastos de organización",     # ← gastos preoperativos de inicio
                "gastos de organizacion",     # ← sin acento
            ],
            "Depreciación acumulada": [
                "depreciación acumulada", "deprec. acum.", "dep. acum.", "dep. acumulada",
                "depreciacion acumulada", "depreciacion", "deprec acum", "(-) deprec. acum.",
            ],
            # ── Activos por Derechos de Uso — NIIF 16 / NIF D-5 ──────────────────
            # Empresas públicas y grandes empresas presentan esta cuenta separada
            # del activo fijo. Se congela bajo juicio crítico.
            "Activos por derechos de uso": [
                "activos por derechos de uso",
                "activos por derecho de uso",      # ← singular
                "derecho de uso",
                "derechos de uso",
                "activos por arrendamiento",
                "activo por arrendamiento",
                "propiedad de arrendamiento",      # ← variante NIIF
                "activo de arrendamiento",         # ← variante
                "right of use",
                "rou assets",                      # ← IFRS inglés abreviado
            ],
            # Pasivo Corto Plazo
            "Cuentas por pagar a proveedores":           ["proveedores", "cuentas por pagar a proveedores"],
            "Préstamo bancario / Deuda a corto plazo":   ["documentos por pagar", "préstamos bancarios", "prestamos bancarios", "deuda a corto plazo", "préstamos bancario", "prestamos bancario"],
            "Acreedores diversos":                       ["acreedores diversos", "acreedores"],
            "Impuestos a la utilidad por pagar": [
                "impuestos a la utilidad por pagar", "impuestos por pagar",
                "isr por pagar", "ptu por pagar",
                "provisión de impuestos", "impuestos acumulados",
            ],
            "IVA por causar o trasladar":  ["iva por causar o trasladar", "iva por causar", "iva trasladado no cobrado"],
            "IVA causado o trasladado":    ["iva causado o trasladado", "i.v.a trasladado", "iva cobrado", "i.v.a. trasladado"],
            "Impuestos retenidos por enterar": [
                "impuestos retenidos",
                "iva retenido pendiente",
                "iva retenido acreditable",
                "isr retenido acreditable",
                "retenciones por enterar",
                "impuestos retenidos por enterar",
            ],
            # ── Pasivo por Arrendamiento Corto Plazo — NIIF 16 / NIF D-5 ─────────
            "Pasivo por arrendamiento a corto plazo": [
                "pasivo por arrendamiento a corto plazo",
                "pasivos por arrendamiento a corto plazo",  # ← plural
                "vencimientos de arrendamientos de l.p. en c.p.",
                "vencimientos de arrendamientos",
                "arrendamiento corto plazo",
                "arrendamiento c.p.",
                "porcion circulante arrendamiento",         # ← variante
                "porción circulante arrendamiento",         # ← con acento
                "lease liability current",
            ],
            # Pasivo Largo Plazo
            "Acreedores diversos a largo plazo":    ["acreedores diversos a largo plazo", "pasivo l.p.", "pasivo a largo plazo"],
            "Cuentas por pagar a largo plazo":      ["cuentas por pagar a largo plazo", "deuda a largo plazo"],
            "Cobros anticipados a largo plazo":     ["cobros anticipados a largo plazo"],
            # ── Pasivo por Arrendamiento Largo Plazo — NIIF 16 / NIF D-5 ─────────
            "Pasivo por arrendamiento a largo plazo": [
                "pasivo por arrendamiento a largo plazo",
                "pasivos por arrendamiento a largo plazo",  # ← plural
                "arrendamientos l.p.",
                "arrendamiento largo plazo",
                "arrendamiento l.p.",
                "arrendamientos a largo plazo",             # ← variante
                "pasivo arrendamiento largo plazo",         # ← sin preposición
                "lease liability non current",
                "lease liability long term",                # ← IFRS variante
            ],
            # ── Obligaciones Laborales Largo Plazo — NIF D-3 ─────────────────────
            "Obligaciones laborales": [
                "obligaciones laborales",
                "beneficios a empleados",
                "pensiones y jubilaciones",
                "plan de pensiones",
                "retiro y jubilación",
                "retiro y jubilacion",
            ],
            # Capital
            "Capital social":  self.kw_capital_social + ["certif. aportación", "certificados de aportación"],
            "Reserva legal":   ["reserva legal", "reservas"],
            "Otros resultados integrales": [
                "otros resultados integrales",
                "resultado integral",
                # ── NUEVO: Contalink — resultado acumulado del ejercicio en curso ──────
                # Contalink presenta la utilidad acumulada del año en una cuenta separada
                # llamada "Resultado del ejercicio en curso" dentro del Capital Ganado.
                # Al no tener cuenta propia en el formulario, se mapea a "Otros resultados
                # integrales" que:
                #   1. Está en Capital Ganado (NIF B-6 párr. 68) — sección correcta
                #   2. No tiene handler especial — se congela bajo juicio crítico
                #   3. No interfiere con "Utilidad o pérdida del ejercicio" (handler automático)
                #   4. No interfiere con "Utilidades de ejercicios anteriores" (lógica anual)
                "resultado del ejercicio en curso",
                "resultado en curso",
                "utilidad en curso",
                "pérdida en curso",
                "perdida en curso",
                "resultado acumulado en curso",
            ],
            "Utilidades o pérdidas de ejercicios anteriores": [
                # GCMK — abreviaciones específicas
                "resuls. ejercicios ant.",
                "resuls, ejercicios ant.",
                "resul. ejercicios ant.",
                "resuls.",
                "resuls",
                # Formatos genéricos seguros
                "resultado de ejercicios anteriores",
                "resultados de ejercicios anteriores",
                "utilidades de ejercicios anteriores",
                "utilidades acumuladas",
                "pérdidas acumuladas",
                "perdidas acumuladas",
                "utilid. ejercicios",
                "resuls. ejercicios",
                # ── NUEVO ──────────────────────────────────────────────────────────
                # El ALIAS_MAP convierte "UTILIDADES" y "UTILID. EJERCICIOS" en la
                # cadena completa "UTILIDADES O PÉRDIDAS DE EJERCICIOS ANTERIORES".
                # Ningún keyword anterior la capturaba como substring — por eso el
                # motor extraía $0 y proyectaba solo la utilidad neta base del ER.
                "utilidades o pérdidas de ejercicios anteriores",
                "utilidades o perdidas de ejercicios anteriores",
                # Contalink — se procesa con lógica de row mínimo
                "resultado del ejercicio",
            ],
            # ── Participación No Controladora — NIF B-8 / NIIF 10 ────────────────
            # En estados consolidados forma parte del capital contable total.
            # Se congela bajo juicio crítico — no tiene handler especial.
            "Participación no controladora": [
                "participación no controladora",
                "participacion no controladora",
                "capital contable minoritario",
                "interés minoritario",
                "intereses minoritarios",
                "participación minoritaria",
                "non-controlling interest",
            ],
        }

        # Alias unificado (retrocompatibilidad con cualquier llamada legada)
        self.concept_keywords = {**self.er_keywords, **self.bg_keywords}

    def _clean_number(self, text: str) -> Decimal | None:
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
                val = Decimal(s)
                return -abs(val) if is_negative else val
            except Exception:
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
            val = Decimal(s)
            return -abs(val) if is_negative else val
        except Exception:
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
                # Normalizar saltos de línea antes de buscar aliases.
                # Azure OCR puede partir celdas con \n
                # Ej: "Seguros\nAnticipados" → "Seguros Anticipados"
                # Ej: "Certif.\nAportación"  → "Certif. Aportación"
                # Ej: "Deprec.\nAcum."       → "Deprec. Acum."
                text_upper = text.upper().replace("\n", " ").replace("  ", " ").strip()
                for alias, standard in self.ALIAS_MAP.items():
                    if alias in text_upper:
                        # Reemplaza el alias por el estándar manteniendo mayúsculas/minúsculas originales si es posible, 
                        # pero al mutar a standard se asegura la coincidencia exacta.
                        cell["text"] = text_upper.replace(alias, standard.upper())
                        text_upper = cell["text"]

    def _get_exact_first(self, ocr_data: Dict[str, Any], keyword: str, target_col_index: int = None, target_relative_index: int = 0, consumed_set: set = None) -> Decimal | None:
        """
        BYPASS: Ignora el método padre _find_value. 
        Busca nativamente en la matriz anidada de celdas la primera coincidencia 
        de la palabra y devuelve su valor adyacente numérico.
        Si target_col_index es provisto, extrae estrictamente de la columna coincidente.
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        kw = keyword.lower()
        consumed = consumed_set if consumed_set is not None else ocr_data.setdefault("used_rows", set())
        
        for t_idx, table in enumerate(tablas_ocr):
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
                # REGLA ESTRICTA 1: Excluir filas con "ejercicio" que no sean históricas.
                # Solo se permite pasar si la fila claramente se refiere a ejercicios
                # anteriores o a cuentas de pérdida/depreciación históricas.
                # Se eliminaron "maquinaria", "equipo", "edificio" como señales —
                # son demasiado genéricas y pueden aparecer en contextos no históricos.
                _es_historico = any(x in row_text for x in [
                    "anterior", "ant.", "anter",
                    "pérdida del ejercicio", "perdida del ejercicio",
                    "deprec",
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
                        if (t_idx, r_idx, kw_col) in consumed:
                            continue
                        val_estricto = None
                        found_values = []
                        for cell in row_cells:
                            c_idx = int(cell.get("col", 0))
                            if c_idx > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        found_values.append(Decimal(str(val)))
                                        if target_col_index is not None and c_idx == target_col_index:
                                            val_estricto = Decimal(str(val))
                        
                        valor_actual = val_estricto
                        if valor_actual is None and found_values:
                            idx = target_relative_index if target_relative_index < len(found_values) else -1
                            valor_actual = found_values[idx]
                            
                        if valor_actual is not None:
                            consumed.add((t_idx, r_idx, kw_col))
                            return valor_actual
        return None

    def _get_first_row_match(
        self,
        ocr_data: Dict[str, Any],
        keyword: str,
        target_col_index: int = None,
        target_relative_index: int = 0,
        consumed_set: set = None
    ) -> float | None:
        """
        Busca el keyword y retorna el valor de la fila con el row más bajo.
        Esto resuelve el problema de Contalink donde padre y subcuentas
        tienen el mismo texto base pero diferente número de fila.
        El padre siempre tiene el row más bajo.
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        keyword_lower = keyword.lower().strip()
        
        mejor_row = None
        mejor_valor = None
        
        for table in tablas_ocr:
            rows = {}
            for cell in table:
                rows.setdefault(int(cell.get("row", 0)), []).append(cell)
            
            for r_idx, row_cells in rows.items():
                row_cells_sorted = sorted(row_cells, key=lambda c: int(c.get("col", 0)))
                
                # Buscar el keyword en las celdas de texto de esta fila
                texto_fila = " ".join([
                    str(c.get("text", "")).lower().strip() 
                    for c in row_cells_sorted
                ])
                
                if keyword_lower not in texto_fila:
                    continue
                
                # Verificar que la celda no esté consumida
                celda_key = f"{r_idx}_{target_col_index or 0}"
                if consumed_set and celda_key in consumed_set:
                    continue
                
                # Encontrar en qué columna está el keyword
                col_keyword = None
                for cell in row_cells_sorted:
                    cell_text = str(cell.get("text", "")).lower().strip()
                    if keyword_lower in cell_text:
                        col_keyword = int(cell.get("col", 0))
                        break

                if col_keyword is None:
                    continue

                # Tomar el valor numérico de la columna más cercana a la DERECHA del keyword
                # Esto evita tomar valores de activos que están a la IZQUIERDA del keyword
                cols_con_valor = [
                    c for c in row_cells_sorted
                    if int(c.get("col", 0)) > col_keyword  # solo columnas a la derecha del keyword
                    and self._clean_number(str(c.get("text", ""))) is not None
                ]

                # Si no hay valores a la derecha, buscar en target_col_index específico
                if not cols_con_valor:
                    if target_col_index is not None:
                        cols_con_valor = [
                            c for c in row_cells_sorted
                            if int(c.get("col", 0)) == target_col_index
                            and self._clean_number(str(c.get("text", ""))) is not None
                        ]
                    if not cols_con_valor:
                        continue

                # Tomar la primera columna a la derecha del keyword
                if target_col_index is not None:
                    col_target = next(
                        (c for c in cols_con_valor if int(c.get("col", 0)) == target_col_index),
                        cols_con_valor[0]  # fallback: primera a la derecha
                    )
                else:
                    col_target = cols_con_valor[0]  # primera columna a la derecha del keyword

                if col_target is None:
                    continue

                valor = self._clean_number(str(col_target.get("text", "")))
                if valor is None:
                    continue

                # Guardar si es el row más bajo encontrado hasta ahora
                if mejor_row is None or r_idx < mejor_row:
                    mejor_row = r_idx
                    mejor_valor = valor
                    if consumed_set is not None:
                        celda_key = f"{r_idx}_{int(col_target.get('col', 0))}"
                        consumed_set.add(celda_key)
        
        return mejor_valor

    def _get_exact_first_with_text(self, ocr_data: Dict[str, Any], keyword: str, consumed_set: set = None) -> tuple:
        """
        Versión extendida de _get_exact_first que además devuelve el texto completo de la fila
        donde encontró el valor para análisis de signos (Pérdidas/Déficit).
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        kw = keyword.lower()
        consumed = consumed_set if consumed_set is not None else ocr_data.setdefault("used_rows", set())
        
        for t_idx, table in enumerate(tablas_ocr):
            rows = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)
                
            for r_idx in sorted(rows.keys()):
                row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                
                # REGLA ESTRICTA 1: Exclusión de la utilidad del ejercicio en curso.
                # Pass-through explícito para: abreviaturas de "anterior" Y pérdidas históricas.
                # REGLA ESTRICTA 1: Excluir filas con "ejercicio" que no sean históricas.
                # Solo se permite pasar si la fila claramente se refiere a ejercicios
                # anteriores o a cuentas de pérdida/depreciación históricas.
                # Se eliminaron "maquinaria", "equipo", "edificio" como señales —
                # son demasiado genéricas y pueden aparecer en contextos no históricos.
                _es_historico = any(x in row_text for x in [
                    "anterior", "ant.", "anter",
                    "pérdida del ejercicio", "perdida del ejercicio",
                    "deprec",
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
                        if (t_idx, r_idx, kw_col) in consumed:
                            continue
                        for cell in row_cells:
                            if int(cell.get("col", 0)) > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        consumed.add((t_idx, r_idx, kw_col))
                                        return Decimal(str(val)), row_text
        return None, ""

    def _get_all_matches_sum(self, ocr_data: Dict[str, Any], keywords: List[str], target_col_index: int = None, target_relative_index: int = 0, consumed_set: set = None) -> Decimal:
        """
        Busca y suma TODOS los valores numéricos de filas que coincidan con 
        cualquiera de las palabras clave, sin duplicar filas.
        Implementa deduplicación jerárquica por valor consecutivo para manejar
        exportaciones en cascada (Cuenta Mayor + Subcuenta con el mismo saldo).
        """
        tablas_ocr = ocr_data.get("tables_data", []) or []
        kws = [k.lower() for k in keywords]
        total_sum = Decimal("0.00")
        consumed = consumed_set if consumed_set is not None else ocr_data.setdefault("used_rows", set())
        last_extracted_value = None  # Guard jerárquico: evita sumar subcuentas redundantes

        for t_idx, table in enumerate(tablas_ocr):
            rows = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)
            
            for r_idx in sorted(rows.keys()):
                row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                
                # REGLA ESTRICTA 1: Exclusión de la utilidad del ejercicio en curso.
                # Pass-through explícito para: abreviaturas de "anterior" Y pérdidas históricas.
                # REGLA ESTRICTA 1: Excluir filas con "ejercicio" que no sean históricas.
                # Solo se permite pasar si la fila claramente se refiere a ejercicios
                # anteriores o a cuentas de pérdida/depreciación históricas.
                # Se eliminaron "maquinaria", "equipo", "edificio" como señales —
                # son demasiado genéricas y pueden aparecer en contextos no históricos.
                _es_historico = any(x in row_text for x in [
                    "anterior", "ant.", "anter",
                    "pérdida del ejercicio", "perdida del ejercicio",
                    "deprec",
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
                        if (t_idx, r_idx, kw_col) in consumed:
                            continue
                        val_estricto = None
                        found_values = []
                        for cell in row_cells:
                            c_idx = int(cell.get("col", 0))
                            if c_idx > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        found_values.append(Decimal(str(val)))
                                        if target_col_index is not None and c_idx == target_col_index:
                                            val_estricto = Decimal(str(val))
                        
                        valor_actual = val_estricto
                        if valor_actual is None and found_values:
                            idx = target_relative_index if target_relative_index < len(found_values) else -1
                            valor_actual = found_values[idx]
                            
                        if valor_actual is not None:
                            valor_abs = abs(valor_actual)
                            # REGLA ESTRICTA 4: Deduplicación jerárquica.
                            if last_extracted_value is not None and valor_abs == last_extracted_value:
                                consumed.add((t_idx, r_idx, kw_col))
                                continue
                            total_sum += valor_actual
                            last_extracted_value = valor_abs
                            consumed.add((t_idx, r_idx, kw_col))
        return total_sum

    def _get_all_matches_sum_with_text(self, ocr_data: Dict[str, Any], keywords: List[str], force_abs: bool = False, exclude_dep: bool = False, sum_all: bool = False, target_col_index: int = None, target_relative_index: int = 0, consumed_set: set = None) -> tuple:
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
        total_sum = Decimal("0.00")
        combined_text = ""
        consumed = consumed_set if consumed_set is not None else ocr_data.setdefault("used_rows", set())
        last_extracted_value = None  # Guard jerárquico

        for t_idx, table in enumerate(tablas_ocr):
            rows = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)
            
            for r_idx in sorted(rows.keys()):
                row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                
                # REGLA ESTRICTA 1: Exclusión de la utilidad del ejercicio en curso.
                # Pass-through explícito para: abreviaturas de "anterior" Y pérdidas históricas.
                # REGLA ESTRICTA 1: Excluir filas con "ejercicio" que no sean históricas.
                # Solo se permite pasar si la fila claramente se refiere a ejercicios
                # anteriores o a cuentas de pérdida/depreciación históricas.
                # Se eliminaron "maquinaria", "equipo", "edificio" como señales —
                # son demasiado genéricas y pueden aparecer en contextos no históricos.
                _es_historico = any(x in row_text for x in [
                    "anterior", "ant.", "anter",
                    "pérdida del ejercicio", "perdida del ejercicio",
                    "deprec",
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
                        if (t_idx, r_idx, kw_col) in consumed:
                            continue
                        val_estricto = None
                        found_values = []
                        for cell in row_cells:
                            c_idx = int(cell.get("col", 0))
                            if c_idx > kw_col:
                                texto_celda = str(cell.get("text", "")).strip()
                                if texto_celda:
                                    val = self._clean_number(texto_celda)
                                    if val is not None:
                                        found_values.append(Decimal(str(val)))
                                        if target_col_index is not None and c_idx == target_col_index:
                                            val_estricto = Decimal(str(val))
                                            
                        valor_actual = val_estricto
                        if valor_actual is None and found_values:
                            idx = target_relative_index if target_relative_index < len(found_values) else -1
                            valor_actual = found_values[idx]
                        
                        if valor_actual is not None:
                            valor_abs = abs(valor_actual)
                            # REGLA ESTRICTA 4: Deduplicación jerárquica.
                            if last_extracted_value is not None and valor_abs == last_extracted_value:
                                consumed.add((t_idx, r_idx, kw_col))
                                continue
                            # REGLA ESTRICTA 3: Valor absoluto por-fila para Pasivos.
                            total_sum += abs(valor_actual) if force_abs else valor_actual
                            combined_text += " " + row_text
                            last_extracted_value = valor_abs
                            consumed.add((t_idx, r_idx, kw_col))
                            # Si sum_all=False, retornamos con la primera coincidencia (Cuenta Mayor)
                            if not sum_all:
                                return (total_sum, combined_text.strip())
        return (total_sum, combined_text.strip()) if combined_text else (None, "")

    def _detectar_tipo_periodo(self, periodo_base: str) -> str:
        """
        Detecta si el periodo base es anual, trimestral o mensual.
        Retorna: "anual", "trimestral" o "mensual"
        """
        if not periodo_base:
            return "anual"  # fallback conservador

        texto = periodo_base.lower().strip()

        meses = ["enero","febrero","marzo","abril","mayo","junio",
                 "julio","agosto","septiembre","octubre","noviembre","diciembre"]

        # Anual: contiene "ejercicio" o año completo (enero a diciembre)
        if "ejercicio" in texto:
            return "anual"

        meses_encontrados = [m for m in meses if m in texto]

        if len(meses_encontrados) >= 2:
            if "enero" in meses_encontrados and "diciembre" in meses_encontrados:
                return "anual"
            return "trimestral"

        if len(meses_encontrados) == 1:
            return "mensual"

        # Solo tiene año (ej. "2025") → anual
        if any(w.isdigit() and len(w) == 4 for w in texto.split()):
            return "anual"

        return "anual"  # fallback conservador

    def _extraer_señales_periodo(self, texto: str) -> dict:
        """
        Extrae del texto las señales de periodo relevantes: mes, año, trimestre.
        Ignora palabras no informativas como PERIODO, Ejercicio, Al, de, ($), etc.

        Ejemplos:
        "Febrero 2026 ($)"                   → { mes: "febrero", año: "2026", trimestre: None }
        "PERIODO Febrero 2026"               → { mes: "febrero", año: "2026", trimestre: None }
        "Al 28 de Febrero de 2026"           → { mes: "febrero", año: "2026", trimestre: None }
        "Ejercicio 2025"                     → { mes: None,      año: "2025", trimestre: None }
        "2025 ($)"                           → { mes: None,      año: "2025", trimestre: None }
        "Q1 2026"                            → { mes: None,      año: "2026", trimestre: "q1" }
        "Ene-Mar 2026 ($)"                   → { mes: None,      año: "2026", trimestre: "q1" }
        "1er Trimestre 2026"                 → { mes: None,      año: "2026", trimestre: "q1" }
        """
        texto_lower = str(texto).lower().strip()

        meses = {
            "enero": "01", "febrero": "02", "marzo": "03",
            "abril": "04", "mayo": "05", "junio": "06",
            "julio": "07", "agosto": "08", "septiembre": "09",
            "octubre": "10", "noviembre": "11", "diciembre": "12",
            # Abreviaciones comunes en PDFs mexicanos
            "ene": "01", "feb": "02", "mar": "03",
            "abr": "04", "may": "05", "jun": "06",
            "jul": "07", "ago": "08", "sep": "09",
            "oct": "10", "nov": "11", "dic": "12",
        }

        trimestres = {
            "q1": "q1", "q2": "q2", "q3": "q3", "q4": "q4",
            "t1": "q1", "t2": "q2", "t3": "q3", "t4": "q4",
            "1er trimestre": "q1", "2do trimestre": "q2",
            "3er trimestre": "q3", "4to trimestre": "q4",
            "primer trimestre": "q1", "segundo trimestre": "q2",
            "tercer trimestre": "q3", "cuarto trimestre": "q4",
            "ene-mar": "q1", "abr-jun": "q2",
            "jul-sep": "q3", "oct-dic": "q4",
            "enero-marzo": "q1", "abril-junio": "q2",
            "julio-septiembre": "q3", "octubre-diciembre": "q4",
        }

        señales = { "mes": None, "año": None, "trimestre": None }

        # ── Caso especial: formato bursátil mexicano "1T25", "2T24", etc. ─────
        # Debe procesarse ANTES del regex de año y del loop de trimestres
        # para evitar falsos positivos:
        #   "1t25" contiene "t2" como substring → sin este fix detectaría Q2
        #   "25" es año de 2 dígitos → el regex \b(20\d{2})\b no lo captura
        # Regex: \b([1-4])[tT](\d{2})\b
        #   [1-4]   → número de trimestre (1, 2, 3 o 4)
        #   [tT]    → letra T mayúscula o minúscula
        #   (\d{2}) → año de 2 dígitos (25, 24, 26...)
        # Ejemplos: "1T25"→Q1/2025, "2T24"→Q2/2024, "3T26"→Q3/2026
        # Verificado: no afecta ningún formato anterior (mensual, anual, Q1 2026, T1 2026)
        match_bursatil = re.search(r'\b([1-4])[tT](\d{2})\b', texto_lower)
        if match_bursatil:
            señales["trimestre"] = f"q{match_bursatil.group(1)}"
            señales["año"] = "20" + match_bursatil.group(2)
            return señales  # retorno temprano — formato identificado sin ambigüedad
        # ─────────────────────────────────────────────────────────────────────

        # Extraer año — 4 dígitos entre 2000 y 2099
        match_año = re.search(r'\b(20\d{2})\b', texto_lower)
        if match_año:
            señales["año"] = match_año.group(1)

        # Extraer trimestre — antes que mes para evitar que "marzo" de "ene-mar" matchee como mes
        for kw, valor in trimestres.items():
            if kw in texto_lower:
                señales["trimestre"] = valor
                break

        # Extraer mes — solo si no encontró trimestre
        if not señales["trimestre"]:
            for nombre in meses:
                if nombre in texto_lower:
                    señales["mes"] = nombre
                    break

        return señales

    def _señales_coinciden(self, señales_base: dict, señales_header: dict) -> bool:
        """
        Verifica si las señales del periodo_base del usuario coinciden
        con las señales extraídas del header del PDF.
        Solo compara lo que es relevante para el tipo de periodo.

        Reglas:
        - El año siempre debe coincidir si ambos lo tienen
        - Periodo mensual  → el mes debe coincidir
        - Periodo trimestral → el trimestre debe coincidir
        - Periodo anual    → solo el año importa
        """
        # Si alguno no tiene señales útiles — no coincide
        if not any(señales_header.values()):
            return False

        # El año debe coincidir si ambos lo tienen
        if señales_base["año"] and señales_header["año"]:
            if señales_base["año"] != señales_header["año"]:
                return False

        # Periodo mensual — el mes debe coincidir
        if señales_base["mes"]:
            return señales_base["mes"] == señales_header["mes"]

        # Periodo trimestral — el trimestre debe coincidir
        if señales_base["trimestre"]:
            return señales_base["trimestre"] == señales_header["trimestre"]

        # Periodo anual — solo el año importa
        if señales_base["año"]:
            return señales_header["año"] == señales_base["año"]

        return False

    def _detectar_columna_periodo(self, tablas_ocr, periodo_base):
        """
        Detecta la columna correcta del periodo base comparando señales extraídas.

        Estrategia principal: extrae mes/año/trimestre del periodo_base del usuario
        y busca en los headers del PDF la celda cuyas señales coincidan.
        Ignora palabras no informativas como PERIODO, Ejercicio, ($), Al, de, etc.

        Funciona con cualquier combinación de:
        - Periodicidad mensual:    "Febrero 2026" vs "PERIODO Febrero 2026 ($)"
        - Periodicidad trimestral: "Q1 2026"      vs "Ene-Mar 2026 ($)"
        - Periodicidad anual:      "Ejercicio 2025" vs "2025 ($)"

        Fallback (Estrategia 4): si ningún header coincide, toma la última
        columna numérica — el periodo más reciente va a la derecha (NIF B-3 párr. 16).
        """
        if not periodo_base:
            return None

        # Extraer las señales del periodo que el usuario seleccionó
        señales_base = self._extraer_señales_periodo(periodo_base)

        # ESTRATEGIAS 1-3 unificadas:
        # Recorrer los primeros 5 headers de cada tabla y comparar señales
        for table in tablas_ocr:
            rows = {}
            for cell in table:
                rows.setdefault(int(cell.get("row", 0)), []).append(cell)
            for r_idx in sorted(rows.keys())[:5]:
                for cell in rows[r_idx]:
                    señales_header = self._extraer_señales_periodo(
                        cell.get("text", "")
                    )
                    if self._señales_coinciden(señales_base, señales_header):
                        return int(cell.get("col", 0))

        # ESTRATEGIA 4: Fallback — columna numérica más reciente
        # Para PDFs sin headers claros o con formato no estándar.
        # NIF B-3 párrafo 16: el periodo actual siempre va a la derecha
        # en presentaciones comparativas.
        for table in tablas_ocr:
            rows = {}
            for cell in table:
                rows.setdefault(int(cell.get("row", 0)), []).append(cell)
            for r_idx in sorted(rows.keys()):
                row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                cols_numericas = []
                for cell in row_cells:
                    val = self._clean_number(str(cell.get("text", "")))
                    if val is not None and abs(val) > 100:
                        cols_numericas.append(int(cell.get("col", 0)))
                if len(cols_numericas) >= 2:
                    return cols_numericas[-1]
                elif len(cols_numericas) == 1:
                    return cols_numericas[0]

        return None

    def _redondear(self, valor: Decimal) -> Decimal:
        """Redondeo matemático tradicional (0.5 siempre sube). Evita redondeo bancario de Python."""
        return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calcular_proyeccion_edo_resultados(
        self,
        ocr_data: Dict[str, Any],
        supuestos_ingresos: List[LineaSupuesto],
        supuestos_costos: List[LineaSupuesto],
        supuestos_impuestos: List[LineaSupuesto],
        inflacion_esperada: float = 0.0,
        periodo_base: str = None
    ) -> Dict[str, Any]:
        # ── LOG TEMPORAL: ver estructura OCR raw ──────────────────────────────
        # Eliminar después de diagnosticar el PDF de GCMK
        import json
        tablas_debug = ocr_data.get("tables_data", [])
        print(f"  [OCR DEBUG] Tablas encontradas: {len(tablas_debug)}")
        for t_idx, table in enumerate(tablas_debug):
            print(f"  [OCR DEBUG] Tabla {t_idx+1}: {len(table)} celdas")
            for cell in table[:20]:  # primeras 20 celdas
                print(f"    row={cell.get('row')} col={cell.get('col')} text='{cell.get('text','')}'")
        # ─────────────────────────────────────────────────────────────────────

        self._preprocess_ocr_data(ocr_data)
        tablas_ocr = ocr_data.get("tables_data", []) or []


        def _get_sup_texto(s):
            if s is None:
                return "-"
            if getattr(s, 'mantener_igual', False):
                return "Mantener igual"
            if getattr(s, 'monto', None) is not None:
                return f"${s.monto:,.2f}"
            if getattr(s, 'variacion', None) is not None:
                return f"{s.variacion:+.2f}%"
            return "-"

        target_col_index = self._detectar_columna_periodo(tablas_ocr, periodo_base)

        # ── Rescate semántico por sección NIF ─────────────────────────────────────
        # Activa el embedding SOLO cuando keyword search falla (Nivel 3).
        # Nunca interfiere con _get_exact_first ni _get_all_matches_sum (Nivel 1).
        SECTION_CONCEPT_MAP_ER = {
            "ingresos":   "ventas_netas",            # NIF B-3 Ventas o Ingresos netos
            "costos":     "costo_de_ventas",         # NIF B-3 Costo de ventas
            "gastos":     "utilidad_operacion",      # NIF B-3 Gastos de operación (proxy)
            "financiero": "gastos_financieros",      # NIF B-3 RIF
            "impuestos":  "impuestos",               # NIF D-3, D-4
        }

        # 1. Identificar Ventas Base (Bypass forzado a la columna mensual/anual)
        # Secuencia de búsqueda por keywords directos — de más específico a más general
        ventas_base = self._get_exact_first(ocr_data, "ventas netas", target_col_index=target_col_index)
        if ventas_base is None:
            ventas_base = self._get_exact_first(ocr_data, "ing por servicios", target_col_index=target_col_index)
        if ventas_base is None:
            ventas_base = self._get_exact_first(ocr_data, "ingresos por servicios", target_col_index=target_col_index)
        if ventas_base is None:
            ventas_base = self._get_exact_first(ocr_data, "ingresos totales", target_col_index=target_col_index)
        if ventas_base is None:
            ventas_base = self._get_exact_first(ocr_data, "ingresos", target_col_index=target_col_index)
            
        if ventas_base is None:
            kw_ventas = self.concept_keywords.get("Ventas netas / Ingresos por servicios", self.kw_ventas_netas)
            ventas_base = self._find_value(
                tablas_ocr, kw_ventas,
                take_last=False,
                concept_key="ventas_netas"  # NIF B-3 rescate semántico
            )
            if ventas_base:
                print(f"  [RESCATE ER] ventas_base via embedding: {float(ventas_base):,.2f}")
            
        ventas_base = abs(Decimal(str(ventas_base))) if ventas_base else Decimal("0.00")

        # 2. Calcular Ventas Proyectadas (Combinando crecimiento real + inflación)
        sup_v = next((s for s in supuestos_ingresos if s.concepto == "Ventas netas / Ingresos por servicios"), None)
        
        if sup_v and not sup_v.mantener_igual:
            ventas_proy = Decimal(str(ventas_base)) * (Decimal("1") + (Decimal(str(sup_v.variacion)) / Decimal("100"))) * (Decimal("1") + (Decimal(str(inflacion_esperada)) / Decimal("100")))
        else:
            ventas_proy = Decimal(str(ventas_base)) * (Decimal("1") + (Decimal(str(inflacion_esperada)) / Decimal("100")))

        val = {
            "ventas": ventas_proy,
            "costo_ventas": Decimal("0.00"),
            "gastos_operativos": Decimal("0.00"),
            "gastos_financieros": Decimal("0.00"),
            "otros_ingresos": Decimal("0.00"),
            "otros_gastos": Decimal("0.00"),
            "productos_financieros": Decimal("0.00"),
            "tasa_impuestos": Decimal("0.00")
        }
        filas_tabla = []
        filas_consumidas = set()

        def solve_rubro(sup, v_base, v_proy_sales, b_sales):
            v_b = Decimal(str(v_base))
            v_p_s = Decimal(str(v_proy_sales))
            b_s = Decimal(str(b_sales))
            infl_esp = Decimal(str(inflacion_esperada))
            
            if sup.mantener_igual or sup.variacion == 0.0 or sup.variacion == 0:
                # Fijo: solo crece con inflación — SIN redondear (acumulación exacta)
                return v_b * (Decimal("1") + (infl_esp / Decimal("100")))
            
            elif sup.variacion is None:
                # Variable: proporción exacta sobre ventas proyectadas
                if b_s > Decimal("0"):
                    proporcion = v_b / b_s  # máxima precisión Decimal
                    return proporcion * v_p_s
                else:
                    return v_b
            
            else:
                # Manual: % del usuario + inflación — SIN redondear
                var_usr = Decimal(str(sup.variacion))
                return v_b * (Decimal("1") + (var_usr / Decimal("100"))) * (Decimal("1") + (infl_esp / Decimal("100")))

        def extract_value(kw_list, seccion=None):
            v = None
            for keyword in kw_list:
                v = self._get_exact_first(
                    ocr_data, keyword,
                    target_col_index=target_col_index,
                    consumed_set=filas_consumidas
                )
                if v is not None:
                    break
            if v is None:
                # Rescate semántico — Nivel 3, solo si keyword falla
                concept_key = SECTION_CONCEPT_MAP_ER.get(seccion) if seccion else None
                v = self._find_value(
                    tablas_ocr, kw_list,
                    take_last=False,
                    concept_key=concept_key
                )
                if v and concept_key:
                    print(f"  [RESCATE ER] seccion='{seccion}' "
                          f"concept_key='{concept_key}' valor={float(v):,.2f}")
            if v is not None:
                return Decimal(str(v))
            return Decimal("0.00")

        # --- PROCESAR INGRESOS ---
        for sup in supuestos_ingresos:
            if sup.concepto == "Ventas netas / Ingresos por servicios":
                filas_tabla.append({
                    "concepto": sup.concepto,
                    "valor_base": float(ventas_base),
                    "variacion_aplicada": sup.variacion if not sup.mantener_igual else 0.0,
                    "valor_proyectado": float(ventas_proy)
                , "supuesto_texto": _get_sup_texto(sup)
                })
                continue
            
            kw = self.er_keywords.get(sup.concepto, [sup.concepto.lower()])
            v_base = extract_value(kw, seccion="ingresos")
            v_proy = solve_rubro(sup, v_base, ventas_proy, ventas_base)
            
            # Separar productos financieros de otros ingresos operativos
            if sup.concepto == "Productos financieros":
                val["productos_financieros"] += v_proy  # ← va al resultado financiero
            else:
                val["otros_ingresos"] += v_proy          # ← va a ingresos operativos
            
            filas_tabla.append({
                "concepto": sup.concepto,
                "valor_base": float(v_base),
                "variacion_aplicada": ((float(v_proy) / float(v_base)) - 1) * 100 if v_base != Decimal("0.00") and v_base != Decimal("0") else 0.0,
                "valor_proyectado": float(self._redondear(v_proy)),
                "supuesto_texto": _get_sup_texto(sup)
            })

        # --- PROCESAR COSTOS Y GASTOS (CON BYPASS EXTENDIDO) ---
        for sup in supuestos_costos:
            
            # Escudo A: Gastos de Administración (Separación de Gastos Generales)
            if sup.concepto == "Gastos de administración":
                v_admin = abs(extract_value(["gastos de administración", "gastos de administracion"], seccion="gastos"))
                v_grales = self._get_exact_first(ocr_data, "gastos generales", target_col_index=target_col_index, consumed_set=filas_consumidas)
                v_grales = abs(Decimal(str(v_grales))) if v_grales is not None else Decimal("0.00")
                
                # Insertar Gastos Generales como fila independiente si existe
                if v_grales > 0:
                    v_grales_proy = solve_rubro(sup, v_grales, ventas_proy, ventas_base)
                    val["gastos_operativos"] += v_grales_proy
                    filas_tabla.append({
                        "concepto": "Gastos generales",
                        "valor_base": float(v_grales),
                        "variacion_aplicada": ((float(v_grales_proy) / float(v_grales)) - 1) * 100 if v_grales != Decimal("0.00") and v_grales != Decimal("0") else 0.0,
                        "valor_proyectado": float(self._redondear(v_grales_proy))
                    })
                
                v_base = v_admin
                
            # Escudo B: Otros Gastos
            elif sup.concepto == "Otros gastos":
                v_base = abs(extract_value(["otros gastos y pérdidas", "otros egresos"], seccion="gastos"))
                    
            # Escudo C: Costo de Ventas (Reconstrucción Forzada)
            elif sup.concepto == "Costo de ventas/Costo por servicios":
                v_base = abs(extract_value(self.kw_costo_de_ventas, seccion="costos"))
                
                if v_base > Decimal("0") and ventas_base > Decimal("0") and (v_base / ventas_base) < Decimal("0.10"): 
                    # Extraemos la primera compra directamente del texto
                    v_compras = self._get_exact_first(ocr_data, "compras", target_col_index=target_col_index, consumed_set=filas_consumidas)
                    v_dev = self._get_exact_first(ocr_data, "devoluciones, descuentos o bonificaciones sobre compras", target_col_index=target_col_index, consumed_set=filas_consumidas)
                    
                    v_compras = abs(Decimal(str(v_compras))) if v_compras is not None else Decimal("0.00")
                    v_dev = abs(Decimal(str(v_dev))) if v_dev is not None else Decimal("0.00")
                    
                    if v_compras > Decimal("0"):
                        v_base = v_base + v_compras - v_dev
            
            else:
                kw = self.er_keywords.get(sup.concepto, [sup.concepto.lower()])
                # Gastos financieros usan su propia sección NIF B-3 RIF
                # para que el embedding compare contra "gastos_financieros"
                # y no contra "utilidad_operacion" (proxy de gastos operativos)
                if "financiero" in sup.concepto.lower():
                    v_base = abs(extract_value(kw, seccion="financiero"))
                else:
                    v_base = abs(extract_value(kw, seccion="gastos"))
            
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
                "variacion_aplicada": ((float(v_proy) / float(v_base)) - 1) * 100 if v_base != Decimal("0.00") and v_base != Decimal("0") else 0.0,
                "valor_proyectado": float(self._redondear(v_proy)),
                "supuesto_texto": _get_sup_texto(sup)
            })

        # 4. Cálculo de cascada parcial (Utilidad Antes de Impuestos)
        # Cascada exacta — SIN _redondear() en pasos intermedios
        # Los acumuladores val[] ya contienen Decimals de precisión máxima
        utilidad_bruta = val["ventas"] - val["costo_ventas"]
        utilidad_operativa = (
            utilidad_bruta
            - val["gastos_operativos"]
            + val["otros_ingresos"]
            - val["otros_gastos"]
        )
        resultado_financiero = val["gastos_financieros"] - val["productos_financieros"]
        utilidad_antes_impuestos = utilidad_operativa - resultado_financiero

        uai_proy = utilidad_antes_impuestos

        # ── LÓGICA DE IMPUESTOS CORREGIDA ──────────────────────────────────────
        uai_proy = utilidad_antes_impuestos

        # --- CÁLCULO DE PTU ---
        sup_ptu = next((s for s in supuestos_impuestos 
                        if s.concepto == "PTU (Participación de los Trabajadores en las Utilidades)"), None)

        # Búsqueda estricta en cascada — excluye filas que contengan "utilidad" o "impuesto"
        EXCLUIR_PTU = ["utilidad", "impuesto", "antes de"]

        v_ptu_base = None

        # Intento 1: búsqueda por frases largas y específicas
        for kw in ["participación de los trabajadores en las utilidades", 
                   "ptu (participación", 
                   "ptu del ejercicio"]:
            resultado = self._get_exact_first(ocr_data, kw, target_col_index=target_col_index, consumed_set=filas_consumidas)
            if resultado is not None:
                v_ptu_base = resultado
                break

        # Intento 2: buscar "(-) ptu" o "- ptu" (formato con signo negativo)
        if v_ptu_base is None:
            for kw in ["(-) ptu", "- ptu", "menos ptu"]:
                resultado = self._get_exact_first(ocr_data, kw, target_col_index=target_col_index, consumed_set=filas_consumidas)
                if resultado is not None:
                    v_ptu_base = resultado
                    break

        # Intento 3: buscar "ptu" pero validando que la fila NO contenga palabras de utilidad
        if v_ptu_base is None:
            tablas_ocr_local = ocr_data.get("tables_data", []) or []
            for table in tablas_ocr_local:
                rows = {}
                for cell in table:
                    rows.setdefault(int(cell.get("row", 0)), []).append(cell)
                for r_idx in sorted(rows.keys()):
                    row_cells = sorted(rows[r_idx], key=lambda x: int(x.get("col", 0)))
                    row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                    # Solo procesar si contiene "ptu" Y no contiene palabras de exclusión
                    if "ptu" in row_text and not any(ex in row_text for ex in EXCLUIR_PTU):
                        for cell in row_cells:
                            if int(cell.get("col", 0)) > 0:
                                val = self._clean_number(str(cell.get("text", "")))
                                if val is not None and val != Decimal("0"):
                                    v_ptu_base = abs(val)
                                    break
                    if v_ptu_base is not None:
                        break
                if v_ptu_base is not None:
                    break

        v_ptu_base = abs(v_ptu_base) if v_ptu_base else Decimal("0.00")

        # --- CÁLCULO DE PTU ---
        ptu_viene_del_doc = v_ptu_base > Decimal("0")
        ptu_activado_por_usuario = (
            sup_ptu is not None
            and sup_ptu.variacion is not None
            and sup_ptu.variacion > 0
        )

        # Inicializar siempre — evita UnboundLocalError si ninguna rama aplica
        ptu_proy = Decimal("0.00")
        tasa_ptu_aplicada = 0.0

        if uai_proy > Decimal("0") and (ptu_viene_del_doc or ptu_activado_por_usuario):

            if ptu_activado_por_usuario:
                # Usuario definió tasa → aplicar sobre UAI
                tasa_ptu = Decimal(str(sup_ptu.variacion)) / Decimal("100")
                ptu_proy = self._redondear(uai_proy * tasa_ptu)
                tasa_ptu_aplicada = float(sup_ptu.variacion)
                filas_tabla.append({
                    "concepto": "PTU (Participación de los Trabajadores en las Utilidades)",
                    "valor_base": float(v_ptu_base),
                    "variacion_aplicada": tasa_ptu_aplicada,
                    "valor_proyectado": float(ptu_proy)
                , "supuesto_texto": _get_sup_texto(sup_ptu)
                })

            elif ptu_viene_del_doc:
                # PDF tiene PTU histórico pero usuario no activó tasa
                # → conservar histórico, no proyectar nuevo valor
                ptu_proy = Decimal("0.00")
                tasa_ptu_aplicada = 0.0
                filas_tabla.append({
                    "concepto": "PTU (Participación de los Trabajadores en las Utilidades)",
                    "valor_base": float(v_ptu_base),
                    "variacion_aplicada": 0.0,
                    "valor_proyectado": 0.0
                , "supuesto_texto": "-"
                })

        else:
            # UAI <= 0 o no hay PTU → $0
            ptu_proy = Decimal("0.00")
            tasa_ptu_aplicada = 0.0
            filas_tabla.append({
                "concepto": "PTU (Participación de los Trabajadores en las Utilidades)",
                "valor_base": float(v_ptu_base),
                "variacion_aplicada": 0.0,
                "valor_proyectado": 0.0
            , "supuesto_texto": "-"
                })

        # --- CÁLCULO DE ISR ---
        sup_isr = next((s for s in supuestos_impuestos if s.concepto == "ISR"), None)
        kw_isr = self.er_keywords.get("ISR", ["isr"])
        v_isr_base = abs(extract_value(kw_isr, seccion="impuestos"))

        isr_viene_del_doc = v_isr_base > Decimal("0")
        isr_activado_por_usuario = sup_isr is not None and sup_isr.variacion is not None and sup_isr.variacion > 0

        if uai_proy > Decimal("0") and (isr_viene_del_doc or isr_activado_por_usuario):
            if sup_isr and sup_isr.variacion is not None and sup_isr.variacion > 0:
                base_isr = uai_proy - ptu_proy
                tasa_isr = Decimal(str(sup_isr.variacion)) / Decimal("100")
                isr_proy = self._redondear(base_isr * tasa_isr)
                tasa_isr_aplicada = float(tasa_isr * Decimal("100"))
            else:
                isr_proy = Decimal("0.00")
                tasa_isr_aplicada = 0.0
        else:
            isr_proy = Decimal("0.00")
            tasa_isr_aplicada = 0.0

        filas_tabla.append({
            "concepto": "ISR",
            "valor_base": float(v_isr_base),
            "variacion_aplicada": tasa_isr_aplicada,
            "valor_proyectado": float(isr_proy)
        , "supuesto_texto": _get_sup_texto(sup_isr)
        })

        total_impuestos_proyectados = ptu_proy + isr_proy
        utilidad_neta = utilidad_antes_impuestos - total_impuestos_proyectados

        # Calcular utilidad neta base del documento OCR
        # Buscamos directamente el valor de utilidad neta/total del documento base
        # Es más preciso que reconstruirlo desde las filas

        # Intento 1: buscar "utilidad neta" o "utilidad total" directamente del OCR
        kw_utilidad_base = [
            "utilidad neta", "utilidad total", "utilidad del ejercicio",
            "utilidad (pérdida) neta", "utilidad (perdida) neta",
            "resultado del ejercicio", "resultado neto"
        ]

        utilidad_neta_base_ocr = None
        for kw in kw_utilidad_base:
            val_encontrado = self._get_exact_first(
                ocr_data, kw,
                target_col_index=target_col_index,
                consumed_set=None  # ← No consumir — solo leer
            )
            if val_encontrado is not None:
                utilidad_neta_base_ocr = val_encontrado
                break

        # Intento 2: si no encontró, reconstruir desde filas (incluyendo impuestos)
        if utilidad_neta_base_ocr is None:
            utilidad_reconstruida = Decimal(str(ventas_base))
            for f in filas_tabla:
                if f["concepto"] == "Ventas netas / Ingresos por servicios":
                    continue
                v_f = Decimal(str(f["valor_base"]))
                if v_f > Decimal("0"):
                    if f["concepto"] in ["Otros ingresos", "Productos financieros"]:
                        utilidad_reconstruida += v_f
                    else:
                        utilidad_reconstruida -= v_f
            utilidad_neta_base_ocr = self._redondear(utilidad_reconstruida)

        utilidad_neta_base_ocr = self._redondear(Decimal(str(utilidad_neta_base_ocr)))

        return {
            "tablas_proyectadas": filas_tabla,
            "ventas": float(self._redondear(val["ventas"])),
            "costo_ventas": float(self._redondear(val["costo_ventas"])),
            "utilidad_bruta": float(self._redondear(utilidad_bruta)),
            "gastos_operativos": float(self._redondear(val["gastos_operativos"])),
            "utilidad_operativa": float(self._redondear(utilidad_operativa)),
            "gastos_financieros": float(self._redondear(val["gastos_financieros"])),
            "productos_financieros": float(self._redondear(val.get("productos_financieros", Decimal("0.00")))),
            "resultado_financiero_neto": float(self._redondear(resultado_financiero)),
            "utilidad_antes_impuestos": float(self._redondear(utilidad_antes_impuestos)),
            "impuestos": float(self._redondear(total_impuestos_proyectados)),
            "utilidad_neta": float(self._redondear(utilidad_neta)),
            "impuestos_totales": float(self._redondear(total_impuestos_proyectados)),
            "utilidad_neta_base": float(self._redondear(Decimal(str(utilidad_neta_base_ocr)))),  # ← nuevo campo
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
        periodo_base: str = None,
        total_impuestos_proforma: float = 0.0,
        gasto_depreciacion_proforma: float = 0.0,
        utilidad_neta_base: float = 0.0,
        periodicidad: str = "mensual",
    ) -> Dict[str, Any]:
        
        self._preprocess_ocr_data(ocr_data)
        tablas_ocr = ocr_data.get("tables_data", []) or []

        # ── LOG TEMPORAL: diagnóstico cuentas NIIF 16 y capital minoritario ───
        # Eliminar después de diagnosticar Bimbo
        # Primero identificar las filas de interés
        filas_interes = set()
        palabras_buscar = ["derecho", "arrendamiento", "minoritario", "planta", "capital contable"]
        for t_idx, table in enumerate(tablas_ocr):
            for cell in table:
                texto = str(cell.get("text", "")).lower()
                if any(p in texto for p in palabras_buscar):
                    filas_interes.add((t_idx, int(cell.get("row", 0))))

        # Luego mostrar TODAS las celdas de esas filas
        for t_idx, table in enumerate(tablas_ocr):
            for cell in table:
                if (t_idx, int(cell.get("row", 0))) in filas_interes:
                    print(f"  [BG DEBUG] row={cell.get('row')} col={cell.get('col')} text='{cell.get('text','')}'")
        # ─────────────────────────────────────────────────────────────────────

        filas_tabla = []

        # DETECCIÓN DE COLUMNA — usa el detector en cascada del ER

        def _get_sup_texto(s):
            if s is None:
                return "-"
            if getattr(s, 'mantener_igual', False):
                return "Mantener igual"
            if getattr(s, 'monto', None) is not None:
                return f"${s.monto:,.2f}"
            if getattr(s, 'variacion', None) is not None:
                return f"{s.variacion:+.2f}%"
            return "-"

        target_col_index = self._detectar_columna_periodo(tablas_ocr, periodo_base)

        # ── Detectar columna dual para BG de doble bloque horizontal ──────────
        # NIF B-6 permite dos formatos de presentación:
        #
        # Formato reporte (vertical) — una sola columna de cuentas:
        #   col 0=Concepto  col 1=2025  col 2=2024
        #   → target_col_index_pasivo = None (flujo normal sin cambios)
        #
        # Formato cuenta (horizontal) — Activo y Pasivo lado a lado:
        #   col 0=ACTIVO  col 1=2025  col 2=2024  col 3=PASIVO  col 4=2025  col 5=2024
        #   → Hay DOS columnas con el mismo periodo
        #   → target_col_index        = cols_coincidentes[0]   (bloque izquierdo — Activo)
        #   → target_col_index_pasivo = cols_coincidentes[-1]  (bloque derecho — Pasivo+Capital)
        #
        # Se usa [0] y [-1] (primero y último) para cubrir también el caso de
        # formato cuenta con 3 periodos comparativos (NIF B-3 párr. 16):
        #   col 0=ACTIVO  col 1=2025  col 2=2024  col 3=2023  col 4=PASIVO  col 5=2025 ...
        #   → cols_coincidentes para 2025 = [col 1, col 5] → [0]=col 1, [-1]=col 5 ✅

        target_col_index_pasivo = None
        señales_base = self._extraer_señales_periodo(periodo_base or "")
        cols_coincidentes = []

        for table in tablas_ocr:
            rows = {}
            for cell in table:
                rows.setdefault(int(cell.get("row", 0)), []).append(cell)
            for r_idx in sorted(rows.keys())[:5]:
                row_cells = sorted(rows[r_idx], key=lambda c: int(c.get("col", 0)))
                cols_coincidentes = [
                    int(c.get("col", 0))
                    for c in row_cells
                    if self._señales_coinciden(
                        señales_base,
                        self._extraer_señales_periodo(str(c.get("text", "")))
                    )
                ]
                # Dos o más columnas con el mismo periodo = formato cuenta (doble bloque)
                if len(cols_coincidentes) >= 2:
                    target_col_index = cols_coincidentes[0]    # Activo — bloque izquierdo
                    target_col_index_pasivo = cols_coincidentes[-1]  # Pasivo+Capital — bloque derecho
                    break
            if target_col_index_pasivo:
                break
        
        # ── Rescate semántico por sección NIF ─────────────────────────────────────
        SECTION_CONCEPT_MAP_BG = {
            "total_activo_circulante":    "activo_circulante",    # NIF B-6, C-1, C-3, C-4
            "total_activo_no_circulante": "activo_fijo_detalle",  # NIF C-6, C-8
            "total_pasivo_corto":         "pasivo_circulante",    # NIF C-9, C-18
            "total_pasivo_largo":         "pasivo_largo_plazo",   # NIF C-18
            "total_capital_contribuido":  "capital_social",       # NIF B-6, C-11
            "total_capital_ganado":       "capital_contable",     # NIF B-6, LGSM
        }

        # Mapa especial para cuentas individuales del activo circulante
        # que necesitan un concept_key más específico que "activo_circulante"
        CUENTA_CONCEPT_MAP_BG = {
            "Caja":                    "caja_bancos",
            "Bancos":                  "caja_bancos",
            "Inversiones temporales":  "inversiones_temporales",
            "IVA acreditable":         "pagos_anticipados",
            "Impuestos y derechos":    "pagos_anticipados",
            "Seguros y fianzas":       "pagos_anticipados",
            "Rentas pagadas por anticipado": "pagos_anticipados",
        }
        
        # Detectar tipo de periodo para cuentas especiales anuales
        es_anual = periodicidad == "anual"
        
        target_relative_index = 0
        target_relative_index_pasivo = 0

        # Calcular target_relative_index para el bloque Activo (izquierda)
        if target_col_index is not None:
            for table in tablas_ocr:
                rows = {}
                for cell in table:
                    rows.setdefault(int(cell.get("row", 0)), []).append(cell)
                for r_idx in sorted(rows.keys())[:5]:
                    row_cells = sorted(rows[r_idx], key=lambda c: int(c.get("col", 0)))
                    cols_numericas = [c for c in row_cells if int(c.get("col", 0)) > 0
                                    and str(c.get("text", "")).strip()]
                    for p_idx, p_cell in enumerate(cols_numericas):
                        if int(p_cell.get("col", 0)) == target_col_index:
                            target_relative_index = p_idx
                            break
                    if target_relative_index > 0:
                        break
                if target_relative_index > 0:
                    break

        # Calcular target_relative_index para el bloque Pasivo+Capital (derecha)
        # Solo aplica cuando se detectó formato cuenta (doble bloque horizontal)
        if target_col_index_pasivo is not None:
            for table in tablas_ocr:
                rows = {}
                for cell in table:
                    rows.setdefault(int(cell.get("row", 0)), []).append(cell)
                for r_idx in sorted(rows.keys())[:5]:
                    row_cells = sorted(rows[r_idx], key=lambda c: int(c.get("col", 0)))
                    cols_numericas = [c for c in row_cells if int(c.get("col", 0)) > 0
                                    and str(c.get("text", "")).strip()]
                    for p_idx, p_cell in enumerate(cols_numericas):
                        if int(p_cell.get("col", 0)) == target_col_index_pasivo:
                            target_relative_index_pasivo = p_idx
                            break
                    if target_relative_index_pasivo > 0:
                        break
                if target_relative_index_pasivo > 0:
                    break
        

        # --- BLOQUE DE EXTRACCIÓN CON CORRECCIÓN DE SIGNO ---
        def extraer_valor_con_signo(v_extraido, row_text, concepto_nombre, seccion):
            if v_extraido is None: return Decimal("0.00")
            valor = abs(Decimal(str(v_extraido)))
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
            if any(x in concepto_nombre.lower() for x in [
                "mobiliario", "equipo", "maquinaria", "transporte", "edificio",
                "licencias", "patentes", "marcas", "franquicias",
                "crédito mercantil", "credito mercantil",
                "depósitos", "depositos", "terrenos",
                "gastos de instalación", "gastos de instalacion",
                "gastos preoperativos", "cargos diferidos",
            ]):
                return abs(valor)
                
            return final_valor

        # Totales por sección
        totales = {
            "total_activo_circulante": Decimal("0.00"),
            "total_activo_no_circulante": Decimal("0.00"),
            "total_pasivo_corto": Decimal("0.00"),
            "total_pasivo_largo": Decimal("0.00"),
            "total_capital_contribuido": Decimal("0.00"),
            "total_capital_ganado": Decimal("0.00")
        }
        
        filas_consumidas = set()

        # Cuentas con CÁLCULO ESPECIAL — se manejan en procesar_seccion
        CUENTAS_ESPECIALES = {
            "Reserva legal",
            "Utilidades o pérdidas de ejercicios anteriores",
            "Utilidad o pérdida del ejercicio",
            "Impuestos a la utilidad por pagar",
        }

        def solve_balance_rubro(sup, v_base):
            v_b = Decimal(str(v_base))
            # PRIORIDAD 1: Usuario marcó "mantener igual" -> congela siempre
            if sup.mantener_igual:
                return self._redondear(v_b)
            
            # PRIORIDAD 2: Usuario definió % manual (Su Juicio Crítico) -> aplica ese %
            if sup.variacion is not None and sup.variacion != 0:
                # Variación manual pura
                var_usr = Decimal(str(sup.variacion))
                return self._redondear(v_b * (Decimal("1") + (var_usr / Decimal("100"))))

            # PRIORIDAD 3: Automático si variacion==0 -> Se congela
            return self._redondear(v_b)

        def procesar_seccion(lista_sups, key_total):
            for sup in lista_sups:
                # Casos especiales automáticos (Capital Ganado)
                if sup.concepto == "Utilidad o pérdida del ejercicio":
                    v_base = Decimal("0.00")
                    v_proy = Decimal(str(utilidad_neta_proforma))

                elif sup.concepto == "Impuestos a la utilidad por pagar":
                    # Juicio crítico: esta cuenta = ISR + PTU del ER proforma
                    kw = self.bg_keywords.get(sup.concepto, [sup.concepto.lower()])
                    v_base_ocr, row_text_lower = self._get_all_matches_sum_with_text(
                        ocr_data, kw,
                        force_abs=True,
                        sum_all=True,
                        target_col_index=target_col_index,
                        target_relative_index=target_relative_index,
                        consumed_set=filas_consumidas
                    )
                    v_base = abs(Decimal(str(v_base_ocr))) if v_base_ocr else Decimal("0.00")
                    
                    if sup.mantener_igual:
                        v_proy = self._redondear(v_base)
                    elif sup.variacion != 0:
                        v_proy = self._redondear(v_base * (Decimal("1") + (Decimal(str(sup.variacion)) / Decimal("100"))))
                    else:
                        if total_impuestos_proforma > 0:
                            # Hay ISR+PTU proyectados del ER → usar ese valor exacto
                            v_proy = self._redondear(Decimal(str(total_impuestos_proforma)))
                        elif utilidad_neta_proforma < 0:
                            # Hay pérdida → definitivamente no hay impuestos que pagar
                            v_proy = Decimal("0.00")
                        else:
                            # Hay utilidad pero el usuario no activó ISR/PTU → conservar valor histórico
                            v_proy = self._redondear(v_base)

                elif sup.concepto == "Reserva legal":
                    kw = self.bg_keywords.get(sup.concepto, ["reserva legal"])
                    v_b_val = self._get_all_matches_sum(
                        ocr_data, kw,
                        target_col_index=target_col_index,
                        target_relative_index=target_relative_index,
                        consumed_set=filas_consumidas
                    )
                    v_base = abs(Decimal(str(v_b_val))) if v_b_val else Decimal("0.00")
                    
                    if sup.mantener_igual:
                        v_proy = self._redondear(v_base)
                    elif sup.variacion != 0:
                        v_proy = self._redondear(v_base * (Decimal("1") + (Decimal(str(sup.variacion)) / Decimal("100"))))
                    else:
                        # Art. 20 LGSM: solo aplica cálculo automático para ER anual
                        if es_anual and utilidad_neta_proforma > 0:
                            incremento_reserva = self._redondear(Decimal(str(utilidad_neta_proforma)) * Decimal("0.05"))
                            capital_social_proy = Decimal(str(next(
                                (f["valor_proyectado"] for f in filas_tabla if f["concepto"] == "Capital social"),
                                0.0
                            )))
                            limite_reserva = self._redondear(capital_social_proy * Decimal("0.20"))
                            
                            if v_base + incremento_reserva <= limite_reserva:
                                v_proy = v_base + incremento_reserva
                            elif v_base < limite_reserva:
                                v_proy = limite_reserva
                            else:
                                v_proy = v_base
                        else:
                            # Mensual o sin utilidad -> se congela la reserva legal
                            v_proy = self._redondear(v_base)

                elif sup.concepto == "Impuestos y derechos":
                    v_base = Decimal("0.00")
                    
                    # 1. Intentar Modo GCMK (sumar rubros sueltos de impuestos del activo)
                    # Excluimos estrictamente "impuestos a favor" para no chocar con el IVA Acreditable
                    kw_gcmk = ["isr anticipos", "isr a favor", "sub-sidio al empleo", "subsidio al empleo"]
                    v_gcmk = self._get_all_matches_sum(ocr_data, kw_gcmk, target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas)
                    
                    if v_gcmk > 0:
                        # Estamos en GCMK, tomamos la suma y le agregamos el IVA retenido
                        v_base = abs(Decimal(str(v_gcmk)))
                        v_iva_ret = self._get_exact_first(ocr_data, "iva retenido", target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas)
                        if v_iva_ret is not None and v_iva_ret > 0:
                            v_base += Decimal(str(v_iva_ret))
                    else:
                        # 2. Estamos en TAAS. Tomamos subcuentas específicas sin tocar la cuenta padre del IVA
                        kw_taas = ["impuestos acreditables por pagar", "impuestos y derechos"]
                        v_base = abs(Decimal(str(self._get_all_matches_sum(ocr_data, kw_taas, target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas))))
                        
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "IVA causado o trasladado":
                    # SUMATORIA SEGURA: Suma 'iva cobrado' + 'i.v.a trasladado' + variantes
                    kw_iva = self.concept_keywords.get("IVA causado o trasladado", ["iva causado o trasladado"])
                    v_base = abs(Decimal(str(self._get_all_matches_sum(ocr_data, kw_iva, target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas))))
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Mobiliario y equipo de oficina":
                    kw_mob = self.bg_keywords.get("Mobiliario y equipo de oficina", ["mobiliario", "muebles y enseres"])
                    v_mob = self._get_all_matches_sum(ocr_data, kw_mob, target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas)
                    if v_mob == Decimal("0"):
                        v_mob = self._get_exact_first(ocr_data, "muebles y enseres", target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas)
                    v_comunicacion = self._get_exact_first(ocr_data, "equipo de comunicación", target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas)
                    
                    v_base_raw = (v_mob or Decimal("0.00")) + (v_comunicacion or Decimal("0.00"))
                    v_base_extraido = extraer_valor_con_signo(v_base_raw, "mobiliario y comunicación", sup.concepto, key_total)
                    v_base = Decimal(str(v_base_extraido)) if v_base_extraido is not None else Decimal("0.00")
                    
                    # Si el keyword no encontró nada, intentar rescate semántico
                    if v_base == Decimal("0.00"):
                        texto_ocr_completo = " ".join([
                            str(cell.get("text", "")).lower()
                            for table in tablas_ocr
                            for cell in table
                        ])
                        kw_mob = self.bg_keywords.get("Mobiliario y equipo de oficina", ["mobiliario"])
                        if any(k.lower() in texto_ocr_completo for k in kw_mob):
                            v_fallback = self._find_value(
                                tablas_ocr, kw_mob,
                                take_last=False,
                                concept_key="activo_fijo_detalle"  # NIF C-6
                            )
                            if v_fallback:
                                v_base = abs(Decimal(str(v_fallback)))
                                print(f"  [RESCATE BG] 'Mobiliario y equipo de oficina' "
                                      f"concept_key='activo_fijo_detalle' valor={float(v_base):,.2f}")
                                      
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Equipo de cómputo":
                    kw_comp = self.bg_keywords.get("Equipo de cómputo", ["equipo de cómputo"])
                    v_computo = self._get_all_matches_sum(ocr_data, kw_comp, target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas)
                    v_base_extraido = extraer_valor_con_signo(v_computo or Decimal("0.00"), "equipo de cómputo", sup.concepto, key_total)
                    v_base = Decimal(str(v_base_extraido)) if v_base_extraido is not None else Decimal("0.00")
                    
                    # Si el keyword no encontró nada, intentar rescate semántico
                    if v_base == Decimal("0.00"):
                        # Verificar si algún keyword existe en el texto del OCR
                        texto_ocr_completo = " ".join([
                            str(cell.get("text", "")).lower()
                            for table in tablas_ocr
                            for cell in table
                        ])
                        kw_computo = self.bg_keywords.get("Equipo de cómputo", ["equipo de cómputo"])
                        if any(k.lower() in texto_ocr_completo for k in kw_computo):
                            v_fallback = self._find_value(
                                tablas_ocr, kw_computo,
                                take_last=False,
                                concept_key="activo_fijo_detalle"  # NIF C-6
                            )
                            if v_fallback:
                                v_base = abs(Decimal(str(v_fallback)))
                                print(f"  [RESCATE BG] 'Equipo de cómputo' "
                                      f"concept_key='activo_fijo_detalle' valor={float(v_base):,.2f}")
                                      
                    v_proy = solve_balance_rubro(sup, v_base)

                elif sup.concepto == "Depreciación acumulada":
                    kw_dep = self.concept_keywords.get("Depreciación acumulada", ["(-) deprec. acum.", "deprec. acum.", "dep. acum.", "depreciacion acumulada", "depreciacion", "deprec acum"])
                    v_base_val = self._get_all_matches_sum(ocr_data, kw_dep, target_col_index=target_col_index, target_relative_index=target_relative_index, consumed_set=filas_consumidas)
                    
                    if v_base_val == Decimal("0"):
                        # Usar keywords completos en lugar de "deprec" solo para evitar
                        # sumar subcuentas individuales (deprec. edificios + deprec. maquinaria + total)
                        kw_dep_especificos = [
                            "depreciación acumulada", "depreciacion acumulada",
                            "deprec. acum.", "dep. acum.", "(-) deprec. acum.",
                            "deprec acum", "dep. acumulada"
                        ]
                        v_base_val = self._get_all_matches_sum(
                            ocr_data, kw_dep_especificos,
                            target_col_index=target_col_index,
                            target_relative_index=target_relative_index,
                            consumed_set=filas_consumidas
                        )
                        
                    v_base = Decimal(str(v_base_val)) if v_base_val is not None else Decimal("0.00")
                    v_base = -abs(v_base) if v_base != Decimal("0") else Decimal("0.00")
                    
                    # JUICIO CRÍTICO: Base histórica (-) Nuevo Gasto del ER
                    # Ambos son negativos contablemente, la resta aumenta el saldo negativo
                    v_proy = self._redondear(v_base - abs(Decimal(str(gasto_depreciacion_proforma))))


                elif sup.concepto == "Utilidades o pérdidas de ejercicios anteriores":
                    kw = self.bg_keywords.get(sup.concepto, [])
                    v_base = None

                    # Estrategia 1: keywords específicos sin problema de subcuentas
                    kw_seguros = [k for k in kw if k != "resultado del ejercicio"]
                    for keyword in kw_seguros:
                        v_b = self._get_exact_first(
                            ocr_data, keyword,
                            target_col_index=target_col_index,
                            target_relative_index=target_relative_index,
                            consumed_set=filas_consumidas
                        )
                        if v_b is not None:
                            v_base = Decimal(str(v_b))
                            break

                    # Estrategia 2: "resultado del ejercicio" con row mínimo (Contalink)
                    if v_base is None:
                        v_b = self._get_first_row_match(
                            ocr_data, "resultado del ejercicio",
                            target_col_index=target_col_index,
                            target_relative_index=target_relative_index,
                            consumed_set=filas_consumidas
                        )
                        if v_b is not None:
                            v_base = Decimal(str(v_b))

                    if v_base is None:
                        v_base = Decimal("0.00")

                    # Juicio crítico: acumular utilidad del ejercicio base
                    if sup.mantener_igual:
                        v_proy = self._redondear(v_base)
                    elif sup.variacion != 0:
                        v_proy = self._redondear(v_base * (Decimal("1") + (Decimal(str(sup.variacion)) / Decimal("100"))))
                    else:
                        # Solo acumula utilidad base para ER anual
                        # Para mensual/trimestral el año no cerró → conservar histórico
                        if es_anual and utilidad_neta_base != 0:
                            v_proy = self._redondear(v_base + Decimal(str(utilidad_neta_base)))
                        else:
                            # Mensual/trimestral → valor histórico conservador
                            # La utilidad del periodo no "pasó" aún a utilidades acumuladas
                            v_proy = self._redondear(v_base)

                else:
                    kw = self.bg_keywords.get(sup.concepto, [sup.concepto.lower()])
                    
                    # Flags contextuales dinámicos
                    _is_pasivo = "pasivo" in key_total.lower()
                    _ACTIVOS_FIJOS = [
                        "edificio", "maquinaria", "transporte", "mobiliario",
                        "cómputo", "computo", "herramienta",
                        "licencias", "patentes", "marcas", "franquicias",
                        "crédito mercantil", "credito mercantil",
                        "depósitos", "depositos", "terrenos",
                        "gastos de instalación", "gastos de instalacion",
                        "gastos preoperativos", "cargos diferidos",
                    ]
                    _is_fixed_asset = any(x in sup.concepto.lower() for x in _ACTIVOS_FIJOS)
                    
                    v_base_ocr, row_text_lower = self._get_all_matches_sum_with_text(
                        ocr_data, kw,
                        force_abs=_is_pasivo,
                        exclude_dep=_is_fixed_asset,
                        sum_all=(sup.concepto == "Impuestos a la utilidad por pagar"),
                        target_col_index=target_col_index,
                        target_relative_index=target_relative_index,
                        consumed_set=filas_consumidas
                    )
                    v_base_val = v_base_ocr
                    
                    if v_base_val is None:
                        if sup.concepto not in ["Marcas", "Patentes"]:
                            # El rescate semántico solo tiene sentido cuando el keyword
                            # encontró texto en el PDF pero no pudo leer el valor numérico.
                            # Si _get_all_matches_sum_with_text retorna (None, "") significa
                            # que la cuenta no existe en el PDF → $0 es correcto, no activar.
                            #
                            # Para activar el rescate semántico de forma segura, primero
                            # verificamos si algún keyword del concepto aparece en el texto
                            # del OCR. Si no aparece ninguno → la cuenta no existe → no rescatar.
                            
                            texto_ocr_completo = " ".join([
                                str(cell.get("text", "")).lower()
                                for table in tablas_ocr
                                for cell in table
                            ])
                            
                            # ¿Algún keyword del concepto aparece en el texto del PDF?
                            keyword_encontrado_en_texto = any(
                                k.lower() in texto_ocr_completo
                                for k in kw
                            )
                            
                            if not keyword_encontrado_en_texto:
                                # El PDF no tiene esta cuenta → $0 legítimo, no rescatar
                                v_base_val = None  # se convertirá en Decimal("0.00") abajo
                            else:
                                # El keyword SÍ existe en el texto pero el motor no lo leyó bien
                                # → activar rescate semántico
                                concept_key = (
                                    CUENTA_CONCEPT_MAP_BG.get(sup.concepto)
                                    or SECTION_CONCEPT_MAP_BG.get(key_total)
                                )
                                v_base_val = self._find_value(
                                    tablas_ocr, kw,
                                    take_last=False,
                                    concept_key=concept_key
                                )
                                if v_base_val and concept_key:
                                    print(f"  [RESCATE BG] '{sup.concepto}' "
                                          f"concept_key='{concept_key}' "
                                          f"valor={float(v_base_val):,.2f}")
                    
                    v_base_extraido = extraer_valor_con_signo(v_base_val, row_text_lower, sup.concepto, key_total)
                    v_base = Decimal(str(v_base_extraido)) if v_base_extraido is not None else Decimal("0.00")
                    v_proy = solve_balance_rubro(sup, v_base)
                
                totales[key_total] += v_proy
                    
                filas_tabla.append({
                    "concepto": sup.concepto,
                    "valor_base": float(v_base),
                    "variacion_aplicada": ((float(v_proy) / float(v_base)) - 1) * 100 if v_base != Decimal("0.00") and v_base != Decimal("0") else 0.0,
                    "valor_proyectado": float(v_proy)
                , "supuesto_texto": _get_sup_texto(sup)
                })

        # Procesar cada sección siguiendo el orden del balance
        procesar_seccion(activo_circulante, "total_activo_circulante")

        # ── RESCATE: Activo Circulante Consolidado ────────────────────────────
        # Algunos PDFs presentan el activo circulante como un total único
        # sin subcuentas desglosadas (ej. "Circulante 800,000").
        # En ese caso todas las subcuentas retornan $0 y el total queda en $0.
        #
        # Flujo del rescate:
        # 1. Detecta que total_activo_circulante == $0
        # 2. Busca "circulante" o variantes en el OCR
        # 3. Si encuentra un total → crea una fila consolidada
        # 4. Si el usuario ingresó un monto en modo $ en alguna subcuenta
        #    → usa ese monto como proyección
        # 5. Si no hay monto del usuario → congela el histórico
        #
        # No requiere cambios en el formulario porque el OCR corre
        # después de que el usuario llena los supuestos.

        if totales["total_activo_circulante"] == Decimal("0.00"):
            # Paso 1: Buscar el total de circulante en el OCR
            kw_circulante = [
                "circulante",
                "activo circulante",
                "total circulante",
                "activo corriente",
                "total activo circulante",
                "total activo corriente",
            ]
            v_circ_ocr = None
            for kw in kw_circulante:
                v_circ_ocr = self._get_exact_first(
                    ocr_data, kw,
                    target_col_index=target_col_index,
                    consumed_set=None
                )
                if v_circ_ocr is not None:
                    break

            if v_circ_ocr is not None and abs(v_circ_ocr) > Decimal("0"):
                v_base_circ = abs(Decimal(str(v_circ_ocr)))

                # Paso 2: Verificar si el usuario ingresó un monto explícito
                # en modo $ en alguna subcuenta del activo circulante
                monto_usuario = next(
                    (
                        Decimal(str(s.monto))
                        for s in activo_circulante
                        if getattr(s, "monto", None) is not None
                        and Decimal(str(s.monto)) > Decimal("0")
                    ),
                    None
                )

                if monto_usuario:
                    # Usuario indicó monto explícito → usarlo como proyección
                    v_proy_circ = self._redondear(monto_usuario)
                else:
                    # Sin indicación del usuario → congelar el histórico
                    v_proy_circ = self._redondear(v_base_circ)

                # Paso 3: Calcular variación aplicada para la fila
                variacion_aplicada = float(
                    ((v_proy_circ / v_base_circ) - Decimal("1")) * Decimal("100")
                ) if v_base_circ > Decimal("0") else 0.0

                # Paso 4: Registrar la fila consolidada y actualizar el total de sección
                filas_tabla.append({
                    "concepto": "Activo circulante (consolidado)",
                    "valor_base": float(v_base_circ),
                    "variacion_aplicada": variacion_aplicada,
                    "valor_proyectado": float(v_proy_circ),
                    "supuesto_texto": f"${float(monto_usuario):,.2f}" if monto_usuario else "Consolidado — mantener igual"
                })
                totales["total_activo_circulante"] = v_proy_circ

                print(
                    f"  [RESCATE BG] Activo circulante consolidado: "
                    f"base={float(v_base_circ):,.2f} → "
                    f"proyectado={float(v_proy_circ):,.2f}"
                    + (" (monto usuario)" if monto_usuario else " (congelado)")
                )

        procesar_seccion(activo_no_circulante, "total_activo_no_circulante")

        # --- AJUSTE DE DEPRECIACIÓN ---
        # Buscamos y sumamos cuentas de depreciación para restarlas explícitamente del activo
        # Solo lo hacemos de manera manual si NO fue inyectada ni procesada previamente
        if not any(f["concepto"] == "Depreciación acumulada" for f in filas_tabla):
            kw_dep = self.concept_keywords.get("Depreciación acumulada", ["(-) deprec. acum.", "deprec. acum.", "dep. acum.", "depreciacion acumulada", "depreciacion", "deprec acum"])
            v_dep_base_val = self._get_all_matches_sum(ocr_data, kw_dep, target_col_index=target_col_index, target_relative_index=target_relative_index)
            
            if v_dep_base_val == Decimal("0"):
                kw_dep_especificos = [
                    "depreciación acumulada", "depreciacion acumulada",
                    "deprec. acum.", "dep. acum.", "(-) deprec. acum.",
                    "deprec acum", "dep. acumulada"
                ]
                v_dep_base_val = self._get_all_matches_sum(
                    ocr_data, kw_dep_especificos,
                    target_col_index=target_col_index,
                    target_relative_index=target_relative_index
                )
            
            v_dep_base = Decimal(str(v_dep_base_val)) if v_dep_base_val is not None else Decimal("0.00")
            
            if v_dep_base == Decimal("0"):
                texto_ocr_completo = " ".join([
                    str(cell.get("text", "")).lower()
                    for table in tablas_ocr
                    for cell in table
                ])
                if any(k.lower() in texto_ocr_completo for k in kw_dep):
                    v_dep_val = self._find_value(
                        tablas_ocr, kw_dep,
                        take_last=True,
                        concept_key="activo_fijo_detalle"  # NIF C-6
                    )
                else:
                    v_dep_val = None
                v_dep_base = Decimal(str(v_dep_val)) if v_dep_val is not None else Decimal("0.00")
            
            # Forzar a negativo para que descuente del activo
            v_dep_base = -abs(v_dep_base) if v_dep_base != Decimal("0") else Decimal("0.00")
            v_dep_proy = v_dep_base 
            totales["total_activo_no_circulante"] += v_dep_proy
            
            if v_dep_base != Decimal("0"):
                filas_tabla.append({
                    "concepto": "Depreciación acumulada",
                    "valor_base": float(v_dep_base),
                    "variacion_aplicada": 0,
                    "valor_proyectado": float(v_dep_proy)
                , "supuesto_texto": "-"
                })
        # Si se detectó formato cuenta (doble bloque horizontal), cambiar al índice
        # del bloque derecho para que Pasivo y Capital lean de la columna correcta.
        # Para formato reporte (vertical), target_col_index_pasivo es None
        # y este bloque no se ejecuta — flujo normal sin cambios.
        if target_col_index_pasivo is not None:
            target_col_index = target_col_index_pasivo
            target_relative_index = target_relative_index_pasivo

        procesar_seccion(pasivo_corto_plazo, "total_pasivo_corto")

        # ── RESCATE: Pasivo Corto Plazo Consolidado ───────────────────────────
        # Algunos PDFs presentan el pasivo circulante como un total único
        # sin subcuentas desglosadas (ej. "Pasivo C.P. 900,000").
        # En ese caso todas las subcuentas retornan $0 y el total queda en $0.
        #
        # Es el mismo patrón que el Activo Circulante Consolidado (Fix 6).
        # El rescate corre automáticamente sin cambios en el formulario.
        #
        # Nota: Solo activa el rescate si el total del pasivo CP es $0
        # Y se encontró un total de sección en el OCR.
        # El bloque de Impuestos a la utilidad por pagar se suma por separado
        # después del rescate para no interferir con la lógica automática.

        # El total puede ser > 0 si "Impuestos a la utilidad por pagar" se inyectó
        # automáticamente del ER proforma — pero eso no significa que haya subcuentas
        # reales extraídas del OCR. El rescate debe activarse cuando ninguna subcuenta
        # real (Proveedores, Préstamos, Acreedores) fue extraída del PDF.
        # Verificamos si hay alguna fila de pasivo CP con valor_base > 0 en filas_tabla
        # excluyendo "Impuestos a la utilidad por pagar" que es automático.
        subcuentas_pasivo_cp_reales = [
            f for f in filas_tabla
            if f.get("concepto") in [
                "Cuentas por pagar a proveedores",
                "Préstamo bancario / Deuda a corto plazo",
                "Acreedores diversos",
                "IVA por causar o trasladar",
                "IVA causado o trasladado",
                "Anticipo de clientes",
                "Rentas cobradas por anticipado",
                "Intereses cobrados por anticipado",
            ]
            and f.get("valor_base", 0) > 0
        ]

        if not subcuentas_pasivo_cp_reales:
            # Paso 1: Buscar el total de pasivo circulante en el OCR
            kw_pasivo_cp = [
                "pasivo c.p.",
                "pasivo circulante",
                "pasivo a corto plazo",
                "pasivo corriente",
                "total pasivo circulante",
                "total pasivo corto plazo",
                "total pasivo c.p.",
            ]
            v_pasivo_cp_ocr = None
            for kw in kw_pasivo_cp:
                v_pasivo_cp_ocr = self._get_exact_first(
                    ocr_data, kw,
                    target_col_index=target_col_index,
                    consumed_set=None
                )
                if v_pasivo_cp_ocr is not None:
                    break

            if v_pasivo_cp_ocr is not None and abs(v_pasivo_cp_ocr) > Decimal("0"):
                v_base_pasivo_cp = abs(Decimal(str(v_pasivo_cp_ocr)))

                # Paso 2: Verificar si el usuario ingresó un monto explícito
                # en modo $ en alguna subcuenta del pasivo corto plazo
                monto_usuario_pasivo = next(
                    (
                        Decimal(str(s.monto))
                        for s in pasivo_corto_plazo
                        if getattr(s, "monto", None) is not None
                        and Decimal(str(s.monto)) > Decimal("0")
                    ),
                    None
                )

                if monto_usuario_pasivo:
                    # Usuario indicó monto explícito → usarlo como proyección
                    v_proy_pasivo_cp = self._redondear(monto_usuario_pasivo)
                else:
                    # Sin indicación del usuario → congelar el histórico
                    v_proy_pasivo_cp = self._redondear(v_base_pasivo_cp)

                # Paso 3: Calcular variación aplicada para la fila
                variacion_aplicada_pasivo = float(
                    ((v_proy_pasivo_cp / v_base_pasivo_cp) - Decimal("1")) * Decimal("100")
                ) if v_base_pasivo_cp > Decimal("0") else 0.0

                # Paso 4: Registrar la fila consolidada y actualizar el total de sección
                filas_tabla.append({
                    "concepto": "Pasivo circulante (consolidado)",
                    "valor_base": float(v_base_pasivo_cp),
                    "variacion_aplicada": variacion_aplicada_pasivo,
                    "valor_proyectado": float(v_proy_pasivo_cp),
                    "supuesto_texto": f"${float(monto_usuario_pasivo):,.2f}" if monto_usuario_pasivo else "Consolidado — mantener igual"
                })
                # Sumar al total existente — no sobreescribir.
                # "Impuestos a la utilidad por pagar" ya fue sumado por procesar_seccion
                # antes del rescate — este consolidado se agrega encima.
                totales["total_pasivo_corto"] += v_proy_pasivo_cp

                print(
                    f"  [RESCATE BG] Pasivo circulante consolidado: "
                    f"base={float(v_base_pasivo_cp):,.2f} → "
                    f"proyectado={float(v_proy_pasivo_cp):,.2f}"
                    + (" (monto usuario)" if monto_usuario_pasivo else " (congelado)")
                )

        # --- AJUSTE AUTOMÁTICO: IMPUESTOS RETENIDOS ---
        # Captura retenciones fiscales usando _get_exact_first para tomar
        # solo el renglón padre — evita doble suma de subcuentas.
        v_ret_val = None
        for kw_ret in ["impuestos retenidos", "retenciones por enterar"]:
            v_ret_val = self._get_exact_first(
                ocr_data, kw_ret,
                target_col_index=target_col_index,
                target_relative_index=target_relative_index,
                consumed_set=filas_consumidas
            )
            if v_ret_val is not None:
                break

        v_ret = abs(Decimal(str(v_ret_val))) if v_ret_val else Decimal("0.00")

        if v_ret > Decimal("0"):
            totales["total_pasivo_corto"] += v_ret
            filas_tabla.append({
                "concepto": "Impuestos retenidos por enterar",
                "valor_base": float(v_ret),
                "variacion_aplicada": 0.0,
                "valor_proyectado": float(v_ret)
            , "supuesto_texto": "-"
            })

        procesar_seccion(pasivo_largo_plazo, "total_pasivo_largo")
        procesar_seccion(capital_contribuido, "total_capital_contribuido")
        procesar_seccion(capital_ganado, "total_capital_ganado")

        # Restaurar el índice del Activo para los cálculos finales de totales y FER.
        # FER = Total Activo - (Total Pasivo + Total Capital)
        # El Total Activo viene de la columna izquierda — necesita el índice original.
        if target_col_index_pasivo is not None:
            target_col_index = cols_coincidentes[0]
            target_relative_index = 0

        # Cálculos finales
        total_activo = self._redondear(totales["total_activo_circulante"] + totales["total_activo_no_circulante"])
        total_pasivo = self._redondear(totales["total_pasivo_corto"] + totales["total_pasivo_largo"])
        total_capital = self._redondear(totales["total_capital_contribuido"] + totales["total_capital_ganado"])
        
        # FER = variable de holgura para cuadrar el balance
        # FER > 0 → se requiere financiamiento externo adicional
        # FER < 0 → hay excedente de fondos
        fer = self._redondear(total_activo - (total_pasivo + total_capital))
        
        return {
            "tablas_proyectadas": filas_tabla,
            "total_activo": float(total_activo),
            "total_pasivo": float(total_pasivo),
            "total_capital": float(total_capital),
            "fer": float(fer)
        }