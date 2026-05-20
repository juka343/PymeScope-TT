import re
from typing import List, Dict, Any, Optional


class FinancialCalculator:
    """
    Motor universal para extraer cuentas de estados financieros a partir de tablas OCR.
    Espera: balance_data/resultados_data con clave 'tables_data' que contiene:
      tables_data: List[table]
      table: List[cell]
      cell: Dict con al menos 'row', 'col', 'text'
    
    Incluye un fallback semántico basado en embeddings (Gemini API) que se activa
    automáticamente cuando el diccionario de keywords no encuentra un concepto.
    """

    def __init__(self) -> None:
        # ===== Servicio de Embeddings (fallback semántico) =====
        self._embedding_service = None
        try:
            from app.core.config import settings
            from app.services.embedding_service import EmbeddingService
            if settings.GEMINI_API_KEY:
                self._embedding_service = EmbeddingService(
                    api_key=settings.GEMINI_API_KEY,
                    model=getattr(settings, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
                )
        except Exception as e:
            print(f"⚠️ FinancialCalculator: Embedding service no disponible: {e}")
            self._embedding_service = None

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
            "utilidad total", "remanente (utilidad) neta", "remanente neto", 
            "remanente del ejercicio"
        ]

        self.kw_utilidad_antes_impuestos = [
            "utilidad antes de impuestos", "resultado antes de impuestos",
            "resultado antes del impuesto", "utilidad antes del impuesto",
        ]

        self.kw_impuestos = [
            "isr", "impuestos a la utilidad", "impuesto sobre la renta", 
            "provisión para isr", "ptu", "impuestos y ptu",
            # Entidades gubernamentales: "Provisión de I.S.R."
            "provisión de i.s.r",
        ]

        self.kw_ventas_netas = [
            "ventas netas", "ventas totales", "ingresos netos",
            "ingresos totales", "total de ingresos", "ingresos por servicios",
            "ingresos operativos", "facturación total", "total ventas",
            "importe de ventas", "productos y servicios",
            "ingresos por venta", "venta de inmuebles",
            "ingresos por arrendamiento", "ingresos por rentas",
            "ingresos por donativos/servicios", "ingresos por donativos",
            # Entidades gubernamentales (PRONABIVE)
            "ingresos propios",
            # "ingresos", <--- ELIMINADO PARA EVITAR FALSOS POSITIVOS CON "OTROS INGRESOS"
        ]

        self.kw_activo_total = [
            "total de activos", "activo total", "suma del activo",
            "activos totales", "total del activo", "activo general",
            "activo circulante y fijo", "activo corriente y no corriente",
            "total activos:", "total activos", "total activo",
        ]

        # CORRECCIÓN 1: Quitamos "capital social" para obligar a buscar el CONTABLE
        self.kw_capital = [
            "capital contable", "total capital contable", "patrimonio neto",
            "total patrimonio", "total capital", "capital y reservas",
            "capital propio", "capital financiero", "patrimonio",
            # Entidades gubernamentales: "Hacienda Pública" = equivalente de Capital Contable
            "hacienda pública", "hacienda publica",
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
            "pasivo a corto plazo", "total pasivo corto plazo", "pasivo corto plazo", 
            "pasivo c.p.", "pasivo a c.p.", "pasivo circulante a c.p."
        ]

        self.kw_inventario = [
            "inventario", "inventarios", "almacén",
            "almacen", "mercancías", "mercancias",
        ]

        # ===== Endeudamiento =====
        # CORRECCIÓN 2: Quitamos "total pasivo" para que no lea la línea "Total Pasivo + Capital"
        self.kw_pasivo_total = [
            "pasivo total", "total del pasivo", "suma del pasivo", 
            "pasivos totales", "total pasivos", "total pasivo",
            # "total pasivo", <--- ELIMINADO: Peligroso en formatos que suman Capital
        ]
        
        self.kw_utilidad_operacion = [
            "utilidad de operación", "utilidad de operacion", "utilidad operativa", 
            "resultado de operación", "resultado de operacion", "resultado operativo", 
            "ganancia operativa",
            # Formatos corporativos BMV (ej. Bimbo: "UTILIDAD (PÉRDIDA) DE OPERACIÓN")
            # IMPORTANTE: Solo variantes con acento en "operación" (ó) para evitar
            # colisión con "UTILIDAD (PÉRDIDA) DE OPERACIONES CONTINUAS"
            "utilidad (pérdida) de operación", "utilidad (perdida) de operación",
        ]
        
        self.kw_intereses = [
            "gastos financieros", "gasto financiero",  # plural + singular (ej. FEMSA)
            "costo integral de financiamiento",
            # Formatos corporativos BMV (ej. Bimbo: "Resultado Integral de Financiamiento")
            "resultado integral de financiamiento",
            # FEMSA: "Gastos de Financiamiento, neto"
            "gastos de financiamiento",
        ]

        # ===== Rotación de activos =====
        self.kw_cuentas_por_cobrar = [
            "cuentas por cobrar", "clientes", "cxc",
        ]

        # ===== Rotación de activos (Ajuste Final) =====
        self.kw_costo_de_ventas = [
            "costo de venta", "costos de venta", # TAAS usa "Costo de venta y/o servicio"
            "costo de ventas", "costos de ventas", 
            "costo de lo vendido", "costo de los servicios", 
            "costo de servicios"
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
            "inmuebles maquinaria y equipo", "total activo no circulante", "activo no circulante"
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
            "certif. aportación", 
            "certif aportacion",        
            "certif. aportacion", "certificados de aportacion",
            "aportaciones de socios", "cap. social", "cap social",
            "patrimonio inicial"
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
            "pasivos l.p.", "pasivo l.p.",
            "pasivo lp",                 # <- Sin puntos
            "pasivo l. p.",              # <- Con espacio entre letras
            "pasivos lp"
        ]

    # -------------------------------------------------------------------------
    # Helpers internos
    # -------------------------------------------------------------------------
    def _parse_periodicidad(self, periodicidad: str) -> tuple:
        """Retorna (usar_acumulado, dias_periodo) según la periodicidad indicada."""
        p = str(periodicidad).lower().strip()
        usar_acumulado = p in ("anual", "acumulado")
        dias_map = {"mensual": 30, "trimestral": 90, "semestral": 180}
        return usar_acumulado, dias_map.get(p, 360)

    @staticmethod
    def _get_tables(data: Dict[str, Any]) -> List:
        """Extrae tables_data de un documento de forma segura."""
        return data.get("tables_data", []) or []

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
    # Búsqueda de valores en tablas OCR (Proximidad Inteligente + Columnas)
    # -------------------------------------------------------------------------
    def _find_value(self, tables_data: List[List[Dict[str, Any]]], keywords: List[str], take_last: bool = False, col_index: int = 0, skip_if_row_contains: List[str] = None, concept_key: str = None) -> float:
        """Busca un valor en las tablas OCR. Primero por keywords, luego por similitud semántica."""
        # --- Paso 1: Búsqueda por keywords (rápida, determinística, gratis) ---
        result = self._keyword_search(tables_data, keywords, take_last, col_index, skip_if_row_contains)
        if result != 0.0:
            return result
        
        # --- Paso 2: Fallback semántico con embeddings (solo si el diccionario falló) ---
        if concept_key and self._embedding_service and self._embedding_service.is_available():
            semantic_result = self._semantic_search(tables_data, concept_key, take_last, col_index, skip_if_row_contains)
            if semantic_result != 0.0:
                print(f"  🧠 Embedding fallback: '{concept_key}' encontrado por similitud semántica → {semantic_result}")
                return semantic_result
        
        return 0.0

    def _keyword_search(self, tables_data: List[List[Dict[str, Any]]], keywords: List[str], take_last: bool = False, col_index: int = 0, skip_if_row_contains: List[str] = None) -> float:
        """Búsqueda original por substring de keywords en las filas OCR."""
        for table in reversed(tables_data):
            rows: Dict[int, List[Dict[str, Any]]] = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)

            for r_idx in sorted(rows.keys(), reverse=True):
                row_cells = rows[r_idx]
                row_cells.sort(key=lambda x: int(x.get("col", 0)))
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])

                # Saltar filas que contienen palabras "veneno" (ej. "TOTAL PASIVO Y CAPITAL CONTABLE")
                if skip_if_row_contains and any(poison in row_text for poison in skip_if_row_contains):
                    continue

                for kw in keywords:
                    if kw in row_text:
                        kw_col_index = -1
                        for cell in row_cells:
                            if kw in str(cell.get("text", "")).lower():
                                kw_col_index = int(cell.get("col", 0))
                                break

                        found_values = []
                        for cell in row_cells:
                            col_idx = int(cell.get("col", 0))
                            if col_idx > kw_col_index:
                                cell_text = str(cell.get("text", "")).strip()
                                val = self._clean_number(cell_text)
                                if val is not None:
                                    found_values.append(float(val))
                                elif cell_text and val is None:
                                    # Celda de texto no-numérico después del keyword = concepto diferente
                                    # (ej. balance lado-a-lado: "Inventarios | 900,000 | ISR por Pagar | 96,000")
                                    # Detenemos la recolección para evitar cruzar al otro lado del balance.
                                    break

                        if found_values:
                            # --- FILTRO ANTI-PORCENTAJES (Nivel Experto) ---
                            max_magnitude = max(abs(v) for v in found_values)
                            
                            val_monetarios = [v for v in found_values if abs(v) > 100 or abs(v) == max_magnitude or v == 0]
                            
                            # Determinamos la lista a usar
                            lista_final = val_monetarios if val_monetarios else found_values
                            
                            # Lógica de extracción de columna
                            if take_last:
                                return lista_final[-1]
                            
                            # Usamos el col_index para elegir la columna deseada (0=Año actual, 1=Año anterior)
                            # Si el índice pedido es mayor a los números que hay, nos protegemos tomando el último
                            if col_index < len(lista_final):
                                return lista_final[col_index]
                            else:
                                return lista_final[-1]
                            
                        # Fallback si texto y número están pegados en la misma celda
                        for cell in row_cells:
                            if kw in str(cell.get("text", "")).lower():
                                val = self._clean_number(cell.get("text", ""))
                                if val is not None:
                                    return float(val)
        return 0.0

    def _semantic_search(self, tables_data: List[List[Dict[str, Any]]], concept_key: str, take_last: bool = False, col_index: int = 0, skip_if_row_contains: List[str] = None) -> float:
        """Búsqueda semántica: compara cada fila de texto contra el concepto canónico usando embeddings."""
        THRESHOLD = 0.85
        best_score = 0.0
        best_values = []
        
        for table in reversed(tables_data):
            rows: Dict[int, List[Dict[str, Any]]] = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)

            for r_idx in sorted(rows.keys(), reverse=True):
                row_cells = rows[r_idx]
                row_cells.sort(key=lambda x: int(x.get("col", 0)))
                
                # Extraer solo las celdas de texto (no numéricas) para el embedding
                text_cells = []
                for c in row_cells:
                    txt = str(c.get("text", "")).strip()
                    if txt and self._clean_number(txt) is None:
                        text_cells.append(txt)
                
                row_label = " ".join(text_cells).strip()
                if not row_label or len(row_label) < 3:
                    continue
                
                row_text = " ".join([str(c.get("text", "")).lower() for c in row_cells])
                
                # Saltar filas veneno
                if skip_if_row_contains and any(poison in row_text for poison in skip_if_row_contains):
                    continue
                
                # Calcular similitud semántica
                score = self._embedding_service.find_match_for_concept(row_label, concept_key, threshold=THRESHOLD)
                
                if score > best_score:
                    best_score = score
                    # Extraer valores numéricos de la fila
                    # Encontrar la última celda de texto para usarla como referencia de columna
                    text_col_max = -1
                    for c in row_cells:
                        txt = str(c.get("text", "")).strip()
                        if txt and self._clean_number(txt) is None:
                            text_col_max = max(text_col_max, int(c.get("col", 0)))
                    
                    found_values = []
                    for cell in row_cells:
                        c_idx = int(cell.get("col", 0))
                        if c_idx > text_col_max:
                            cell_text = str(cell.get("text", "")).strip()
                            val = self._clean_number(cell_text)
                            if val is not None:
                                found_values.append(float(val))
                            elif cell_text and val is None:
                                break
                    
                    if found_values:
                        max_magnitude = max(abs(v) for v in found_values)
                        val_monetarios = [v for v in found_values if abs(v) > 100 or abs(v) == max_magnitude or v == 0]
                        best_values = val_monetarios if val_monetarios else found_values
        
        if best_values and best_score >= THRESHOLD:
            lista_final = best_values
            if take_last:
                return lista_final[-1]
            if col_index < len(lista_final):
                return lista_final[col_index]
            return lista_final[-1]
        
        return 0.0


    # -------------------------------------------------------------------------
    # KPIs
    # -------------------------------------------------------------------------
    def calcular_rentabilidad(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0) -> Dict[str, Any]:
        """Calcula indicadores de rentabilidad cruzando Balance y Estado de Resultados."""
        tablas_resultados = self._get_tables(resultados_data)
        tablas_balance = self._get_tables(balance_data)
        usar_acumulado, dias_periodo = self._parse_periodicidad(periodicidad)
        ventas_netas = self._find_value(tablas_resultados, self.kw_ventas_netas, take_last=usar_acumulado, col_index=col_index, concept_key="ventas_netas")
        if ventas_netas == 0:
            ventas_netas = self._find_value(tablas_resultados, ["ingresos"], take_last=usar_acumulado, col_index=col_index)

        utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_neta, take_last=usar_acumulado, col_index=col_index, concept_key="utilidad_neta")
        
        # Fallback 1: buscar utilidad antes de impuestos en el Estado de Resultados
        if utilidad_neta == 0:
            utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_antes_impuestos, take_last=usar_acumulado, col_index=col_index, concept_key="utilidad_antes_impuestos")

        # Fallback 2: buscar utilidad neta en el Balance General
        if utilidad_neta == 0:
            utilidad_neta = self._find_value(tablas_balance, self.kw_utilidad_neta, take_last=usar_acumulado, col_index=0)
            
        if utilidad_neta == 0:
                utilidad_neta = self._find_value(tablas_balance, self.kw_utilidad_antes_impuestos, take_last=usar_acumulado, col_index=0)

        # 3) Balance
        activo_total = self._find_value(tablas_balance, self.kw_activo_total, take_last=usar_acumulado, col_index=0, concept_key="activo_total")
        capital_contable = self._find_value(tablas_balance, self.kw_capital, take_last=usar_acumulado, col_index=0, skip_if_row_contains=["pasivo y capital", "pasivo + capital", "pasivo y hacienda"], concept_key="capital_contable")

        # 4) Cálculos
        margen_utilidad = (utilidad_neta / ventas_netas) if ventas_netas else 0
        roa = (utilidad_neta / activo_total) if activo_total else 0
        roe = (utilidad_neta / capital_contable) if capital_contable else 0

        # 5) Factor de ajuste para umbrales flujo÷stock
        # ROA y ROE comparan un flujo del periodo (utilidad) contra un stock (activos/capital),
        # por lo que en periodos más cortos el flujo es proporcionalmente menor.
        # El margen (utilidad/ventas) es flujo÷flujo, así que NO se ajusta.
        factor = dias_periodo / 365  # 1.0 anual, ~0.25 trimestral, ~0.08 mensual
        roa_ok = 0.05 * factor
        roe_ok = 0.10 * factor

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
                    "status": "ok" if margen_utilidad >= 0.10 else ("warn" if margen_utilidad >= 0 else "danger"),
                },
                {
                    "label": "Rendimiento sobre Activos Totales (RAT)",
                    "value": f"{roa * 100:.2f}%",
                    "status": "ok" if roa >= roa_ok else ("warn" if roa >= 0 else "danger"),
                },
                {
                    "label": "Rendimiento sobre el Patrimonio",
                    "value": f"{roe * 100:.2f}%",
                    "status": "ok" if roe >= roe_ok else ("warn" if roe >= 0 else "danger"),
                },
            ],
        }

    def calcular_liquidez(self, balance_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0) -> Dict[str, Any]:
        """Calcula indicadores de liquidez basados en el Balance General."""
        tablas_balance = self._get_tables(balance_data)
        usar_acumulado, _ = self._parse_periodicidad(periodicidad)

        activo_circulante = self._find_value(tablas_balance, self.kw_activo_circulante, take_last=usar_acumulado, col_index=0, concept_key="activo_circulante")
        pasivo_circulante = self._find_value(tablas_balance, self.kw_pasivo_circulante, take_last=usar_acumulado, col_index=0, concept_key="pasivo_circulante")
        inventario = self._find_value(tablas_balance, self.kw_inventario, take_last=usar_acumulado, col_index=0, concept_key="inventario")

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
                    "status": "ok" if razon_liquidez >= 1.0 else ("warn" if razon_liquidez >= 0.8 else "danger"),
                },
                {
                    "label": "Prueba del Ácido",
                    "value": f"{prueba_acido:.2f}",
                    "status": "ok" if prueba_acido >= 0.8 else ("warn" if prueba_acido >= 0.5 else "danger"),
                },
                {
                    "label": "Capital de Trabajo",
                    "value": f"${capital_trabajo:,.2f}",
                    "status": "ok" if capital_trabajo > 0 else ("warn" if capital_trabajo == 0 else "danger"),
                },
            ],
        }

    def calcular_endeudamiento(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0) -> Dict[str, Any]:
        """Calcula indicadores de endeudamiento cruzando Balance y Estado de Resultados."""
        tablas_balance = self._get_tables(balance_data)
        tablas_resultados = self._get_tables(resultados_data)
        usar_acumulado, _ = self._parse_periodicidad(periodicidad)

        # --- EXTRACCIÓN DEL BALANCE ---
        activo_total = self._find_value(tablas_balance, self.kw_activo_total, take_last=usar_acumulado, col_index=0, concept_key="activo_total")
        
        # Renombramos a capital_contable para evitar confusiones y asegurar la fórmula
        capital_contable = self._find_value(tablas_balance, self.kw_capital, take_last=usar_acumulado, col_index=0, skip_if_row_contains=["pasivo y capital", "pasivo + capital", "pasivo y hacienda"], concept_key="capital_contable")
        pasivo_total_doc = self._find_value(tablas_balance, self.kw_pasivo_total, take_last=usar_acumulado, col_index=0, skip_if_row_contains=["capital contable", "y capital", "+ capital", "y hacienda"], concept_key="pasivo_total")

        # Lógica de rescate para Pasivo Total (Ecuación Contable: P = A - C)
        # Si no lo encuentra (0) o si captura la fila "Total Pasivo + Capital" (>= activo_total)
        if (pasivo_total_doc == 0 or pasivo_total_doc >= activo_total) and activo_total > 0:
            pasivo_total = activo_total - capital_contable
        else:
            pasivo_total = pasivo_total_doc
        
        # Limpieza de signos
        if pasivo_total < 0: pasivo_total = abs(pasivo_total)



        # --- EXTRACCIÓN DEL ESTADO DE RESULTADOS ---
        utilidad_operacion = self._find_value(tablas_resultados, self.kw_utilidad_operacion, take_last=usar_acumulado, col_index=col_index, concept_key="utilidad_operacion")
        intereses = self._find_value(tablas_resultados, self.kw_intereses, take_last=usar_acumulado, col_index=col_index, concept_key="gastos_financieros")
        utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_neta, take_last=usar_acumulado, col_index=col_index, concept_key="utilidad_neta")
        impuestos = self._find_value(tablas_resultados, self.kw_impuestos, take_last=usar_acumulado, col_index=col_index, concept_key="impuestos")
        
        if intereses < 0: intereses = abs(intereses)
        if impuestos < 0: impuestos = abs(impuestos)

        # --- LÓGICA DE RESCATE (100% UNIVERSAL Y MATEMÁTICA) ---
        if utilidad_operacion == 0 or utilidad_operacion == intereses:
            # Rescate Nivel 1: EBT + Intereses
            util_antes_imp = self._find_value(tablas_resultados, self.kw_utilidad_antes_impuestos, take_last=usar_acumulado, col_index=col_index, concept_key="utilidad_antes_impuestos")
            
            if util_antes_imp != 0:
                utilidad_operacion = util_antes_imp + intereses
            elif utilidad_neta != 0:
                # Rescate Nivel 2: Utilidad Neta + Impuestos Reales Extraídos + Intereses
                utilidad_operacion = utilidad_neta + impuestos + intereses

        # --- CÁLCULOS ---
        apalancamiento = (pasivo_total / activo_total) if activo_total else 0
        cobertura_intereses = (utilidad_operacion / intereses) if intereses else 0
        estabilidad_financiera = (pasivo_total / capital_contable) if capital_contable else 0

        return {
            "datos_crudos": {
                "pasivo_total": pasivo_total,
                "activo_total": activo_total,
                "capital_social": capital_contable,  # Nota: el campo se llama capital_social por compatibilidad con el frontend, pero el valor es capital_contable
                "utilidad_operacion": utilidad_operacion,
                "intereses": intereses,
            },
            "kpis": [
                {
                    "label": "Apalancamiento",
                    "value": f"{apalancamiento:.2f}",
                    "status": "ok" if 0 < apalancamiento <= 0.5 else ("warn" if 0.5 < apalancamiento <= 0.7 else "danger"),
                },
                {
                    "label": "Razón de Cobertura de Intereses",
                    "value": f"{cobertura_intereses:.2f}",
                    "status": "ok" if cobertura_intereses >= 1.5 else ("warn" if cobertura_intereses >= 1.0 else "danger"),
                },
                {
                    "label": "Estabilidad Financiera",
                    "value": f"{estabilidad_financiera:.2f}",
                    "status": "ok" if 0 < estabilidad_financiera <= 1.0 else ("warn" if 1.0 < estabilidad_financiera <= 1.5 else "danger"),
                },
            ],
        }

    def calcular_rotacion(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0) -> Dict[str, Any]:
        """Calcula indicadores de rotación adaptándose dinámicamente al tipo de periodo."""
        tablas_balance = self._get_tables(balance_data)
        tablas_resultados = self._get_tables(resultados_data)
        usar_acumulado, dias_periodo = self._parse_periodicidad(periodicidad)

        # --- EXTRACCIÓN BÁSICA ---
        cuentas_por_cobrar = self._find_value(tablas_balance, self.kw_cuentas_por_cobrar, take_last=usar_acumulado, col_index=0, concept_key="cuentas_por_cobrar")
        inventario = self._find_value(tablas_balance, self.kw_inventario, take_last=usar_acumulado, col_index=0, concept_key="inventario")
        activo_fijo_neto = self._find_value(tablas_balance, self.kw_activo_fijo, take_last=usar_acumulado, col_index=0, concept_key="activo_fijo")
        activo_total = self._find_value(tablas_balance, self.kw_activo_total, take_last=usar_acumulado, col_index=0, concept_key="activo_total")

        # Usamos nuestra variable dinámica 'usar_acumulado' en lugar del True hardcodeado
        ventas_netas = self._find_value(tablas_resultados, self.kw_ventas_netas, take_last=usar_acumulado, col_index=col_index, concept_key="ventas_netas")
        
        if ventas_netas == 0:
            ventas_netas = self._find_value(tablas_resultados, ["ingresos"], take_last=usar_acumulado, col_index=col_index)

        costo_directo = self._find_value(tablas_resultados, self.kw_costo_de_ventas, take_last=usar_acumulado, col_index=col_index, concept_key="costo_de_ventas")
        compras = self._find_value(tablas_resultados, self.kw_compras, take_last=usar_acumulado, col_index=col_index)
        devoluciones = self._find_value(tablas_resultados, self.kw_devoluciones_costo, take_last=usar_acumulado, col_index=col_index)
        
        costo_ventas_calculado = abs(costo_directo) + abs(compras) - abs(devoluciones)        
        if costo_ventas_calculado < 0: costo_ventas_calculado = 0
        
        # 1. Rotación de Cartera
        rotacion_cartera = (ventas_netas / cuentas_por_cobrar) if cuentas_por_cobrar else 0
        
        # 2. Días de Cobro
        ventas_diarias = (ventas_netas / dias_periodo) if dias_periodo else 0
        periodo_recaudo = (cuentas_por_cobrar / ventas_diarias) if ventas_diarias else 0
        
        # 3. Rotaciones de Activos
        rotacion_inventarios = (costo_ventas_calculado / inventario) if inventario else 0
        rotacion_activos_fijos = (ventas_netas / activo_fijo_neto) if activo_fijo_neto else 0
        rotacion_activos_totales = (ventas_netas / activo_total) if activo_total else 0

        # 4. Factor de ajuste para umbrales flujo÷stock
        # Las rotaciones comparan un flujo del periodo (ventas, costo) contra un stock (activos),
        # por lo que en periodos más cortos el flujo es proporcionalmente menor.
        # El Periodo Promedio de Recaudo ya se ajusta vía dias_periodo, así que NO cambia.
        factor = dias_periodo / 365  # 1.0 anual, ~0.25 trimestral, ~0.08 mensual
        rot_cartera_ok = 4.0 * factor
        rot_af_ok = 1.0 * factor
        rot_af_warn = 0.5 * factor
        rot_at_ok = 1.0 * factor
        rot_at_warn = 0.5 * factor

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
                    "status": "ok" if rotacion_cartera >= rot_cartera_ok else ("warn" if rotacion_cartera > 0 else "danger"),
                },
                {
                    "label": "Periodo Promedio de Recaudo",
                    "value": f"{periodo_recaudo:,.0f} días",
                    "status": "ok" if 0 < periodo_recaudo <= 60 else ("warn" if 60 < periodo_recaudo <= 90 else "danger"),
                },
                {
                    "label": "Rotación de Inventarios",
                    "value": "N/A" if inventario == 0 else f"{rotacion_inventarios:.2f}",
                    # Si el inventario es 0, es una empresa de servicios y el estatus es OK
                    "status": "ok" if (rotacion_inventarios > 0 or inventario == 0) else "danger",
                },
                {
                    "label": "Rotación de Activos Fijos",
                    "value": f"{rotacion_activos_fijos:.2f}",
                    "status": "ok" if rotacion_activos_fijos >= rot_af_ok else ("warn" if rotacion_activos_fijos >= rot_af_warn else "danger"),
                },
                {
                    "label": "Rotación de Activos Totales",
                    "value": f"{rotacion_activos_totales:.2f}",
                    "status": "ok" if rotacion_activos_totales >= rot_at_ok else ("warn" if rotacion_activos_totales >= rot_at_warn else "danger"),
                },
            ],
        }

    def calcular_estructura(self, balance_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0) -> Dict[str, Any]:
        """Calcula indicadores de Estructura Financiera basados en el Balance General."""
        tablas_balance = self._get_tables(balance_data)
        usar_acumulado, _ = self._parse_periodicidad(periodicidad)

        # --- 1. EXTRACCIÓN BÁSICA ---
        activo_total = self._find_value(tablas_balance, self.kw_activo_total, take_last=usar_acumulado, col_index=0, concept_key="activo_total")
        activo_fijo = self._find_value(tablas_balance, self.kw_activo_fijo, take_last=usar_acumulado, col_index=0, concept_key="activo_fijo") 
        pasivo_total_doc = self._find_value(tablas_balance, self.kw_pasivo_total, take_last=usar_acumulado, col_index=0, skip_if_row_contains=["capital contable", "y capital", "y hacienda"], concept_key="pasivo_total")
        capital_contable = self._find_value(tablas_balance, self.kw_capital, take_last=usar_acumulado, col_index=0, skip_if_row_contains=["pasivo y capital", "pasivo + capital", "pasivo y hacienda"], concept_key="capital_contable")
        pasivo_largo_plazo = self._find_value(tablas_balance, self.kw_pasivo_largo_plazo, take_last=usar_acumulado, col_index=0, concept_key="pasivo_largo_plazo")

        # --- 2. LÓGICA INTELIGENTE PARA CAPITAL SOCIAL ---
        capital_social_doc = self._find_value(tablas_balance, self.kw_capital_social, take_last=usar_acumulado, col_index=0, skip_if_row_contains=["pasivo y capital", "pasivo + capital", "pasivo y hacienda"], concept_key="capital_social")
        capital_variable = self._find_value(tablas_balance, ["capital variable", "capital social variable"], take_last=usar_acumulado, col_index=0)
        capital_fijo = self._find_value(tablas_balance, ["capital fijo", "capital social fijo"], take_last=usar_acumulado, col_index=0)
        
        suma_capitales = capital_fijo + capital_variable
        
        if suma_capitales > capital_social_doc:
            capital_social = suma_capitales      
        elif capital_social_doc == capital_variable and capital_fijo == 0 and capital_variable > 0:
            capital_social = capital_social_doc + capital_variable   
        else:
            capital_social = capital_social_doc

        # --- 3. RESCATE PARA PASIVO TOTAL ---
        # Si lee 0, o si se confunde con "Suma de Pasivo y Capital" (dando un valor >= al activo)
        if (pasivo_total_doc == 0 or pasivo_total_doc >= activo_total) and activo_total > 0:
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
                "capital_social": capital_social,
                "capital_contable": capital_contable,
                "activo_fijo": activo_fijo,
                "pasivo_largo_plazo": pasivo_largo_plazo
            },
            "kpis": [
                {
                    "label": "Solvencia General",
                    "value": f"{solvencia:.2f}",
                    "status": "ok" if solvencia > 1.0 else ("warn" if solvencia >= 0.8 else "danger"),
                },
                {
                    "label": "Seguridad a largo plazo",
                    "value": "N/A" if seguridad_largo_plazo is None else f"{seguridad_largo_plazo:.2f}",
                    # Sin deuda a largo plazo es una posición de seguridad (OK)
                    "status": "ok" if (seguridad_largo_plazo is None or seguridad_largo_plazo >= 1.0) else ("warn" if seguridad_largo_plazo >= 0.5 else "danger"),
                },
                {
                    "label": "Inmovilización de Cap. Social",
                    "value": f"{inmovilizacion_social:.2f}",
                    "status": "ok" if inmovilizacion_social <= 1.0 else ("warn" if inmovilizacion_social <= 1.5 else "danger"), 
                },
                {
                    "label": "Inmovilización de Cap. Contable",
                    "value": f"{inmovilizacion_contable:.2f}",
                    "status": "ok" if inmovilizacion_contable <= 1.0 else ("warn" if inmovilizacion_contable <= 1.5 else "danger"),
                },
            ],
        }