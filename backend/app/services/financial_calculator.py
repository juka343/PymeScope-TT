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
            "remanente del ejercicio",
            "operaciones continuas", "operaciones discontinuas"
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
            # Variantes plurales con prefijo "total" (ej. Coca-Cola BMV: "Total activos circulantes")
            # NOTA: "activos circulantes" sin "total" NO se agrega — coincide con
            # encabezados de sección en balances corporativos (Bimbo, FEMSA) que tienen
            # un número adyacente erróneo antes de la fila de total real.
            "total activos circulantes",
            "activos corrientes totales",
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
            "pasivos totales", "total pasivos", "total pasivo", "total de pasivos",
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
            # Formas de total (más largas → prioridad en sort descendente)
            "total de capital social",
            "total capital social",
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

        # ===== Subcuentas para rescate por suma (layouts sin subtotales explícitos) =====
        self.kw_efectivo = [
            "efectivo y equivalentes de efectivo",
            "efectivo y equivalentes",
            "efectivo", "caja y bancos", "caja", "bancos",
        ]
        self.kw_pagos_anticipados = [
            "seguros anticipados", "pagos anticipados",
            "gastos pagados por anticipado", "gastos anticipados", "anticipos",
        ]
        self.kw_terrenos = ["terrenos", "terreno"]
        self.kw_maquinaria_equipo = [
            "maquinaria y equipo", "maquinaria", "edificios",
            "mobiliario y equipo", "equipo de transporte", "equipo de computo",
        ]
        self.kw_depreciacion_acum = [
            "depreciación acumulada", "depreciacion acumulada",
            "(-) depreciación acumulada", "(-) depreciacion acumulada",
            "depreciación y amortización acumulada", "deprec. acum",
        ]
        self.kw_proveedores = [
            "proveedores", "cuentas por pagar a proveedores",
        ]
        self.kw_ptu_pagar = ["ptu por pagar", "p.t.u. por pagar"]
        self.kw_isr_pagar = ["isr por pagar", "i.s.r. por pagar"]
        self.kw_reservas = ["reservas", "reserva legal", "otras reservas"]
        self.kw_utilidades_acumuladas = [
            "utilidades de ejercicios anteriores",
            "utilidad de ejercicios anteriores",
            "utilidades acumuladas", "resultados acumulados",
            "utilid. ejercicios", "utilidades retenidas",
        ]

        # ===== Telemetría de extracción =====
        # _trace_buffer acumula cómo se obtuvo cada concepto en el módulo activo.
        # _last_match_info es la "variable de salida" que _keyword_search/_semantic_search
        # rellenan antes de retornar, para que _find_value la copie al buffer.
        self._trace_buffer: Dict[str, dict] = {}
        self._last_match_info: dict = {}
        self._current_formato_perfil: str = "vertical_simple"

        # Marcadores de cuentas compuestas en una sola fila.
        # Cuando una fila del balance combina dos cuentas NIF distintas (ej.
        # "Clientes y otras cuentas por cobrar"), no se puede separar el monto
        # entre los componentes sin información externa — emitimos un warning
        # para que el usuario sepa que el valor es agregado.
        # NOTA: "y equivalentes de efectivo" NO está aquí porque la NIF B-6 lo
        # reconoce como UNA sola cuenta canónica, no como composición.
        self._composed_markers: List[str] = [
            " y otras cuentas por cobrar",
            " y otras cuentas por pagar",
            " y otros activos",
            " y otros pasivos",
            " y otros deudores",
            " y otros acreedores",
            " y otras partidas",
            " e otros activos",
            " e intangibles",
        ]

        # Cargar catálogo NIF y hacer merge con diccionarios
        self._load_nif_catalog()

        # ===== Fuentes NIF (trazabilidad normativa por concepto canónico) =====
        self.fuentes_nif: Dict[str, Dict[str, str]] = {
            # NIF B-3 — Estado de Resultados
            "ventas_netas":             {"norma": "NIF B-3", "cuenta_nif": "Ventas o Ingresos netos"},
            "costo_de_ventas":          {"norma": "NIF B-3", "cuenta_nif": "Costo de ventas"},
            "utilidad_operacion":       {"norma": "NIF B-3", "cuenta_nif": "Utilidad de operación"},
            "gastos_financieros":       {"norma": "NIF B-3", "cuenta_nif": "Gastos financieros (Intereses a cargo)"},
            "utilidad_antes_impuestos": {"norma": "NIF B-3", "cuenta_nif": "Utilidad antes de impuestos a la utilidad"},
            "impuestos":                {"norma": "NIF B-3", "cuenta_nif": "Impuestos a la utilidad"},
            "utilidad_neta":            {"norma": "NIF B-3", "cuenta_nif": "Utilidad / pérdida del ejercicio"},
            # NIF B-6 — Estado de Situación Financiera
            "activo_circulante":        {"norma": "NIF B-6", "cuenta_nif": "Activo a corto plazo (circulante)"},
            "cuentas_por_cobrar":       {"norma": "NIF B-6", "cuenta_nif": "Cuentas por cobrar a clientes"},
            "inventario":               {"norma": "NIF B-6", "cuenta_nif": "Inventarios"},
            "activo_fijo":              {"norma": "NIF B-6", "cuenta_nif": "Propiedades, planta y equipo"},
            "activo_total":             {"norma": "NIF B-6", "cuenta_nif": "Total del Activo"},
            "pasivo_circulante":        {"norma": "NIF B-6", "cuenta_nif": "Pasivo a corto plazo"},
            "pasivo_largo_plazo":       {"norma": "NIF B-6", "cuenta_nif": "Pasivo a largo plazo"},
            "pasivo_total":             {"norma": "NIF B-6", "cuenta_nif": "Total del Pasivo"},
            "capital_social":           {"norma": "NIF B-6", "cuenta_nif": "Capital social"},
            "capital_contable":         {"norma": "NIF B-6", "cuenta_nif": "Capital Contable"},
        }

    # -------------------------------------------------------------------------
    # Helpers internos
    # -------------------------------------------------------------------------
    def _load_nif_catalog(self):
        """Carga el catálogo NIF y fusiona sus cuentas oficiales con las listas de alias."""
        import os, json
        nif_path = os.path.join(os.path.dirname(__file__), "catalogo_nif.json")
        if not os.path.exists(nif_path):
            return
            
        try:
            with open(nif_path, "r", encoding="utf-8") as f:
                nif_data = json.load(f)
        except Exception as e:
            print(f"⚠️ FinancialCalculator: Error al cargar catalogo_nif.json: {e}")
            return

        # Mapeo estricto para Exact Match.
        # NOTA: Omitimos "A corto plazo" o "A largo plazo" porque como substring causan falsos positivos
        # (ej. "a corto plazo" matchea "Activo a Corto Plazo" al buscar pasivo).
        # Para kw_pasivo_circulante y kw_pasivo_largo_plazo: el nombre NIF es peligroso como keyword;
        # se omiten del mapping para no inyectar términos ambiguos en las listas de búsqueda.
        nif_mapping = {
            # === NIF B-6 / B-3: conceptos que ya tenían sustento ===
            "kw_inventario": ["Inventarios"],
            "kw_capital_social": ["Capital social"],
            "kw_utilidad_neta": ["Utilidad / pérdida del ejercicio"],
            "kw_ventas_netas": ["Ventas o Ingresos netos", "Ventas totales"],
            "kw_costo_de_ventas": ["Costo de ventas", "Costo de mercancía vendida", "Costo de servicios prestados"],
            "kw_cuentas_por_cobrar": ["Cuentas por cobrar a clientes", "Otras cuentas por cobrar (deudores diversos)"],
            "kw_activo_fijo": ["Propiedades, planta y equipo (activo fijo)"],
            "kw_impuestos": ["Impuestos a la utilidad", "ISR (Impuesto Sobre la Renta)", "PTU (Participación de los Trabajadores en las Utilidades)"],
            "kw_capital": ["Capital Contable"],
            # === NIF B-6: 3 conceptos que faltaban (solo términos seguros como keyword) ===
            # "Corto plazo, circulante o corriente" es el nombre de clasificación NIF B-6 —
            # demasiado verboso para aparecer en documentos reales, pero establece el vínculo normativo.
            "kw_activo_circulante": ["Corto plazo, circulante o corriente"],
            # === Extensiones NIF (totales estructurales de catalogo_nif.json#extensiones) ===
            "kw_activo_total": ["Total del Activo"],
            "kw_pasivo_total": ["Total del Pasivo"],
            "kw_utilidad_operacion": ["Utilidad de operación"],
            "kw_utilidad_antes_impuestos": ["Utilidad antes de impuestos a la utilidad"],
        }

        def extract_terms(data, target_names, current_terms):
            if isinstance(data, dict):
                name = data.get("nombre") or data.get("elemento")
                if name and name in target_names:
                    current_terms.add(name.lower())
                    # ¡CRÍTICO!: NO agregamos las "subcuentas" aquí. 
                    # El Exact Match busca la fila de TOTAL (ej. "Total Cuentas por Cobrar"). 
                    # Si inyectamos subcuentas (ej. "Clientes nacionales"), el escáner capturará una fracción del total.
                for key, value in data.items():
                    extract_terms(value, target_names, current_terms)
            elif isinstance(data, list):
                for item in data:
                    extract_terms(item, target_names, current_terms)

        for kw_attr, target_names in nif_mapping.items():
            if hasattr(self, kw_attr):
                terms = set()
                extract_terms(nif_data, target_names, terms)
                existing_list = getattr(self, kw_attr)
                merged = list(set(existing_list) | terms)
                # Ordenar por longitud descendente para búsquedas más seguras
                merged.sort(key=len, reverse=True)
                setattr(self, kw_attr, merged)

    def _parse_periodicidad(self, periodicidad: str) -> tuple:
        """Retorna (usar_acumulado, dias_periodo) según la periodicidad indicada."""
        p = str(periodicidad).lower().strip()
        usar_acumulado = p in ("anual", "acumulado")
        dias_map = {"mensual": 30, "trimestral": 90, "semestral": 180}
        return usar_acumulado, dias_map.get(p, 360)

    def _nota_periodo(self, periodicidad: str) -> Optional[str]:
        """Devuelve la etiqueta sutil para KPIs flujo÷stock cuando el periodo no es anual.

        Aplica a RAT, RSP y las 4 rotaciones: el valor refleja el periodo, no es una tasa anualizada.
        """
        p = str(periodicidad).lower().strip()
        notas = {
            "mensual": "valor mensual",
            "trimestral": "valor trimestral",
            "semestral": "valor semestral",
        }
        return notas.get(p)

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
        self._last_match_info = {"method": "not_found"}

        # --- Paso 1: Búsqueda por keywords (rápida, determinística, gratis) ---
        result = self._keyword_search(tables_data, keywords, take_last, col_index, skip_if_row_contains)
        if result != 0.0:
            if concept_key:
                self._trace_buffer[concept_key] = dict(self._last_match_info)
            return result

        # --- Paso 2: Fallback semántico con embeddings (solo si el diccionario falló) ---
        if concept_key and self._embedding_service and self._embedding_service.is_available():
            semantic_result = self._semantic_search(tables_data, concept_key, take_last, col_index, skip_if_row_contains)
            if semantic_result != 0.0:
                info = dict(self._last_match_info)
                score = info.get("score", 0.0)
                zona = info.get("zone", "")
                if zona == "gris":
                    print(
                        f"  ⚠️  Embedding zona gris: '{concept_key}' "
                        f"raw={score:.3f} anti={info.get('score_anti', 0.0):.3f} "
                        f"adj={info.get('score_adjusted', 0.0):.3f} → {semantic_result:,.2f}"
                    )
                else:
                    print(f"  🧠 Embedding         : '{concept_key}' score={score:.3f} → {semantic_result:,.2f}")
                self._trace_buffer[concept_key] = info
                return semantic_result

        if concept_key:
            self._trace_buffer[concept_key] = {"method": "not_found"}
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

                            # Detectar columna de % al final: si hay 3+ valores y el
                            # último es < 1% del máximo en magnitud, es una columna de
                            # variación/porcentaje (ej. -251.17% en GCMK vs -324,525.87).
                            # Cubre % > 100 que el filtro >100 no puede descartar.
                            if (
                                len(found_values) >= 3
                                and max_magnitude > 0
                                and abs(found_values[-1]) < max_magnitude * 0.01
                            ):
                                found_values = found_values[:-1]
                                max_magnitude = max(abs(v) for v in found_values)

                            val_monetarios = [v for v in found_values if abs(v) > 100 or abs(v) == max_magnitude or v == 0]

                            # Determinamos la lista a usar
                            lista_final = val_monetarios if val_monetarios else found_values

                            # Registrar match para telemetría (antes de cualquier return)
                            self._last_match_info = {
                                "method": "keyword",
                                "matched_term": kw,
                                "row_snippet": row_text[:120].strip(),
                            }
                            # Detección de cuenta compuesta (ej. "Clientes y otras cuentas por cobrar")
                            for marker in self._composed_markers:
                                if marker in row_text:
                                    self._last_match_info["composed"] = True
                                    self._last_match_info["composed_marker"] = marker.strip()
                                    break

                            # Lógica de extracción de columna
                            # col_index tiene prioridad; take_last es solo fallback
                            # cuando col_index queda fuera de rango (mantenido por
                            # _pick_column_value que retorna lista_final[-1] como default).
                            flow_kws = (
                                getattr(self, "kw_ventas_netas", []) + getattr(self, "kw_utilidad_neta", [])
                                + getattr(self, "kw_utilidad_antes_impuestos", []) + getattr(self, "kw_utilidad_operacion", [])
                                + getattr(self, "kw_costo_de_ventas", []) + getattr(self, "kw_intereses", [])
                                + getattr(self, "kw_impuestos", []) + getattr(self, "kw_compras", [])
                                + getattr(self, "kw_devoluciones_costo", []) + ["ingresos"]
                            )
                            is_flow = any(kw in flow_kws for kw in keywords)
                            return self._pick_column_value(lista_final, col_index, is_flow)

                        # Fallback si texto y número están pegados en la misma celda
                        for cell in row_cells:
                            if kw in str(cell.get("text", "")).lower():
                                val = self._clean_number(cell.get("text", ""))
                                if val is not None:
                                    self._last_match_info = {
                                        "method": "keyword",
                                        "matched_term": kw,
                                        "row_snippet": row_text[:120].strip(),
                                    }
                                    return float(val)
        return 0.0

    def _semantic_search(self, tables_data: List[List[Dict[str, Any]]], concept_key: str, take_last: bool = False, col_index: int = 0, skip_if_row_contains: List[str] = None) -> float:
        """Búsqueda semántica con umbral graduado y penalización por anti-conceptos.

        Para cada fila se calcula:
          - score_raw: similitud con el concepto buscado
          - score_anti: similitud máxima con sus anti-conceptos (ej. activo_circulante ↔ pasivo_circulante)
          - score_adjusted = score_raw - 0.5 * score_anti

        Aceptación:
          - score_adjusted >= THRESHOLD_ALTO (0.88)  → aceptado (zona segura)
          - THRESHOLD_BAJO (0.75) <= adj < ALTO     → zona gris. Aceptar solo si la
            ventaja sobre el anti-concepto (raw - anti) es >= MARGIN (0.05).
          - score_adjusted < THRESHOLD_BAJO          → rechazado.
        """
        THRESHOLD_ALTO = 0.88
        THRESHOLD_BAJO = 0.75
        MARGIN_ANTI = 0.05

        best_adjusted = 0.0
        best_raw = 0.0
        best_anti = 0.0
        best_values = []
        best_row_label = ""

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

                # Score crudo + anti-concepto (un solo embedding por fila)
                score_raw, score_anti, score_adj = self._embedding_service.find_match_with_anticoncepts(
                    row_label, concept_key
                )

                if score_adj > best_adjusted:
                    best_adjusted = score_adj
                    best_raw = score_raw
                    best_anti = score_anti
                    best_row_label = row_label
                    # Extraer valores numéricos de la fila
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
                        # Mismo filtro anti-porcentajes que _keyword_search:
                        # columna de % al final con magnitud < 1% del max.
                        if (
                            len(found_values) >= 3
                            and max_magnitude > 0
                            and abs(found_values[-1]) < max_magnitude * 0.01
                        ):
                            found_values = found_values[:-1]
                            max_magnitude = max(abs(v) for v in found_values)
                        val_monetarios = [v for v in found_values if abs(v) > 100 or abs(v) == max_magnitude or v == 0]
                        best_values = val_monetarios if val_monetarios else found_values

        # Reglas de aceptación por umbral graduado
        if not best_values:
            return 0.0

        accepted = False
        zona = None
        if best_adjusted >= THRESHOLD_ALTO:
            accepted = True
            zona = "alta"
        elif best_adjusted >= THRESHOLD_BAJO:
            # Zona gris solo es válida si el concepto tiene anti-conceptos definidos
            # que aporten señal de desambiguación. Sin anti-concepto, el margin check
            # es trivial (anti=0 → cualquier raw lo cumple) y se filtran falsos
            # positivos exigiendo zona alta.
            if best_anti > 0 and (best_raw - best_anti) >= MARGIN_ANTI:
                accepted = True
                zona = "gris"

        if not accepted:
            if best_raw >= THRESHOLD_BAJO:
                print(
                    f"  ⛔ Embedding rechazado: '{concept_key}' raw={best_raw:.3f} "
                    f"anti={best_anti:.3f} adj={best_adjusted:.3f}"
                )
            return 0.0

        # Registrar match semántico para telemetría
        self._last_match_info = {
            "method": "semantic",
            "score": round(best_raw, 4),
            "score_adjusted": round(best_adjusted, 4),
            "score_anti": round(best_anti, 4),
            "zone": zona,
            "row_snippet": best_row_label[:120],
        }

        lista_final = best_values

        # --- REGLA FRANCOTIRADOR (Sábanas Mensuales) ---
        p = getattr(self, "_current_periodicidad", "").lower()
        if len(lista_final) >= 12 and p in ("trimestral", "semestral"):
            is_flow = concept_key in ("ventas_netas", "utilidad_neta", "utilidad_antes_impuestos", "utilidad_operacion", "costo_de_ventas", "gastos_financieros", "impuestos")
            step = 3 if p == "trimestral" else 6
            start = col_index * step
            if start + step <= len(lista_final):
                if is_flow:
                    return sum(lista_final[start:start+step])
                else:
                    return lista_final[start + step - 1]

        # Respeta col_index primero: en comparativos multi-año la columna elegida
        # por _detect_period_columns es la fuente de verdad. take_last es fallback
        # legado para layouts donde el último valor de la fila es el "actual"
        # (ej. sábanas con columna "Total" al final) y solo aplica si col_index
        # quedó fuera de rango.
        if col_index < len(lista_final):
            return lista_final[col_index]

        if take_last:
            return lista_final[-1]

        if p == "mensual":
            return lista_final[0]
        return lista_final[-1]


    def _suma_subcuentas(
        self,
        tablas: list,
        kw_lists_add: List[List[str]],
        col_index: int,
        usar_acumulado: bool,
        multiplicador: float = 1.0,
        kw_lists_sub: List[List[str]] = None,
    ) -> float:
        """Suma subcuentas cuando el subtotal no tiene línea explícita en el documento.

        Solo retorna > 0 si al menos una subcuenta tiene valor, evitando
        falsos positivos en empresas con subtotales legítimamente en cero.
        Las listas en kw_lists_sub se restan (ej. depreciación acumulada).
        """
        total = 0.0
        found_any = False
        for kw_list in kw_lists_add:
            val = self._find_value(tablas, kw_list, take_last=usar_acumulado, col_index=col_index)
            if val != 0:
                found_any = True
                total += abs(val) * multiplicador
        if kw_lists_sub:
            for kw_list in kw_lists_sub:
                val = self._find_value(tablas, kw_list, take_last=usar_acumulado, col_index=col_index)
                if val != 0:
                    found_any = True
                    total -= abs(val) * multiplicador
        return max(total, 0.0) if found_any else 0.0

    def _record_rescue(self, concept_key: str, formula: str, value: float) -> None:
        """Registra que un rescate matemático calculó/sobreescribió el valor de un concepto."""
        if not concept_key:
            return
        self._trace_buffer[concept_key] = {
            "method": "math_rescue",
            "formula": formula,
            "value": round(value, 2),
        }
        print(f"  🔧 Rescate matemático: '{concept_key}' = {value:,.2f}  [{formula}]")

    def _collect_trace(self) -> Optional[Dict[str, dict]]:
        """Retorna el trace acumulado y limpia el buffer para el siguiente módulo."""
        trace = dict(self._trace_buffer) if self._trace_buffer else None
        self._trace_buffer.clear()
        return trace

    def _collect_fuentes(self, concept_keys: List[str]) -> Dict[str, Dict[str, str]]:
        """Retorna las fuentes NIF para los conceptos usados en el módulo."""
        return {k: self.fuentes_nif[k] for k in concept_keys if k in self.fuentes_nif}

    def _pick_column_value(self, lista_final: List[float], col_index: int, is_flow: bool = False) -> float:
        """Selecciona el valor correcto de lista_final según el perfil de formato activo.

        Perfiles:
          - sabana_mensual   : francotirador explícito (col_index navega grupos de meses)
          - corporativo_bmv  : col_index directo, nunca activa el francotirador
          - vertical_simple  : col_index directo + heurística legacy (len>=12) para compatibilidad
          - lado_a_lado      : col_index directo (el stop-at-text ya filtró el lado correcto)
        """
        perfil = getattr(self, "_current_formato_perfil", "vertical_simple")
        p = getattr(self, "_current_periodicidad", "").lower()

        if perfil == "sabana_mensual":
            step = 3 if p == "trimestral" else 6
            start = col_index * step
            if start + step <= len(lista_final):
                return sum(lista_final[start:start + step]) if is_flow else lista_final[start + step - 1]
            return lista_final[0]

        if perfil == "corporativo_bmv":
            if col_index < len(lista_final):
                return lista_final[col_index]
            return lista_final[-1]

        # vertical_simple y lado_a_lado: mantener heurística legacy para compatibilidad
        if len(lista_final) >= 12 and p in ("trimestral", "semestral"):
            step = 3 if p == "trimestral" else 6
            start = col_index * step
            if start + step <= len(lista_final):
                return sum(lista_final[start:start + step]) if is_flow else lista_final[start + step - 1]

        if col_index < len(lista_final):
            return lista_final[col_index]
        if p == "mensual":
            return lista_final[0]
        return lista_final[-1]

    # -------------------------------------------------------------------------
    # Detección de periodo por columna (Fase 8)
    # -------------------------------------------------------------------------
    _MESES_ES = {
        "enero": "01", "ene": "01",
        "febrero": "02", "feb": "02",
        "marzo": "03", "mar": "03",
        "abril": "04", "abr": "04",
        "mayo": "05", "may": "05",
        "junio": "06", "jun": "06",
        "julio": "07", "jul": "07",
        "agosto": "08", "ago": "08",
        "septiembre": "09", "sept": "09", "sep": "09",
        "octubre": "10", "oct": "10",
        "noviembre": "11", "nov": "11",
        "diciembre": "12", "dic": "12",
    }

    def _parse_period_label(self, text: str) -> Optional[str]:
        """Detecta un periodo en un texto y devuelve etiqueta normalizada.

        Formatos detectados:
          - "2024"                → "2024"
          - "Enero 2024"          → "2024-01"
          - "Dic 2023"            → "2023-12"
          - "1T24" / "Q1 2024"    → "2024-Q1"
          - "2024-01" / "01/2024" → "2024-01"
        """
        if not text or len(text) < 2:
            return None

        s = text.strip().lower()

        # Año (20xx)
        year_match = re.search(r"\b(20\d{2})\b", s)
        year = year_match.group(1) if year_match else None

        # Año corto al final de patrones tipo "1T24"
        short_year_match = re.search(r"\b[1-4]\s*[tq]\s*(\d{2})\b", s)

        # Mes (nombre español, completo o abreviado)
        mes_num: Optional[str] = None
        for mes_name, num in self._MESES_ES.items():
            if re.search(rf"\b{mes_name}\b", s):
                mes_num = num
                break

        # Fecha numérica: YYYY-MM o MM/YYYY
        if not mes_num:
            iso_match = re.search(r"\b(20\d{2})[-/](\d{1,2})\b", s)
            if iso_match:
                year = iso_match.group(1)
                mes_num = iso_match.group(2).zfill(2)
            else:
                rev_match = re.search(r"\b(\d{1,2})[-/](20\d{2})\b", s)
                if rev_match:
                    mes_num = rev_match.group(1).zfill(2)
                    year = rev_match.group(2)

        # Trimestre
        q_num: Optional[str] = None
        q_match = (
            re.search(r"\b([1-4])\s*[tq]\s*\d{2,4}\b", s)   # 1T24, 1T 2024
            or re.search(r"\b([1-4])\s*[tq]\b", s)           # 1T standalone
            or re.search(r"\b[tq]([1-4])\b", s)              # T1, Q1
            or re.search(r"trimestre\s+([1-4])", s)          # trimestre 1
        )
        if q_match:
            q_num = q_match.group(1)
            if not year and short_year_match:
                year = f"20{short_year_match.group(1)}"

        if mes_num and year:
            return f"{year}-{mes_num}"
        if q_num and year:
            return f"{year}-Q{q_num}"
        if year:
            return year
        return None

    def _detect_period_columns(self, tables_data: List[List[Dict[str, Any]]]) -> Dict[str, int]:
        """Escanea headers de las tablas y devuelve mapa {periodo: data_col_index}.

        Mira las primeras 3 filas de cada tabla, agrupa el texto por columna
        (para soportar headers multi-fila tipo "Enero" sobre "2024"), y aplica
        _parse_period_label a cada combinación.

        El índice devuelto es POSICIONAL entre las columnas de periodo encontradas
        (0, 1, 2, …), no el índice de celda OCR. Así queda alineado con
        _find_value, que construye lista_final únicamente con los valores
        numéricos de la fila (ignorando la celda de etiqueta).
        """
        detected: Dict[str, int] = {}

        for table in tables_data:
            rows: Dict[int, List[Dict[str, Any]]] = {}
            for cell in table:
                r_idx = int(cell.get("row", 0))
                rows.setdefault(r_idx, []).append(cell)

            header_row_ids = sorted(rows.keys())[:3]
            column_texts: Dict[int, List[str]] = {}
            for r_idx in header_row_ids:
                for cell in rows[r_idx]:
                    col = int(cell.get("col", 0))
                    text = str(cell.get("text", "")).strip()
                    if text:
                        column_texts.setdefault(col, []).append(text)

            data_idx = 0
            for col in sorted(column_texts.keys()):
                combined = " ".join(column_texts[col])
                label = self._parse_period_label(combined)
                if not label:
                    continue
                if label not in detected:
                    detected[label] = data_idx
                data_idx += 1

        return detected

    def _validate_extractions(
        self,
        values: Dict[str, float],
        trace: Optional[Dict[str, dict]] = None,
        tolerancia: float = 0.02,
    ) -> List[str]:
        """
        Valida identidades contables sobre los valores ya extraídos y rescatados.
        Retorna una lista de strings de advertencia (vacía = todo OK).

        Usa el trace para evitar falsos positivos:
        - Si un valor proviene de 'math_rescue', la ecuación contable se deriva
          matemáticamente de los otros dos y siempre sería consistente → se omite.
        """
        warnings: List[str] = []
        tr = trace or {}

        def _method(key: str) -> str:
            return tr.get(key, {}).get("method", "")

        ac  = values.get("activo_circulante", 0) or 0
        pc  = values.get("pasivo_circulante", 0) or 0
        inv = values.get("inventario", 0) or 0
        at  = values.get("activo_total", 0) or 0
        pt  = values.get("pasivo_total", 0) or 0
        cc  = values.get("capital_contable", 0) or 0
        af  = values.get("activo_fijo", 0) or 0
        plp = values.get("pasivo_largo_plazo", 0) or 0
        vn  = values.get("ventas_netas", 0) or 0
        un  = values.get("utilidad_neta", 0) or 0
        uai = values.get("utilidad_antes_impuestos", 0) or 0

        # 1. Un componente no puede superar su contenedor
        if inv > 0 and ac > 0 and inv > ac:
            warnings.append(
                f"inventario ({inv:,.2f}) > activo_circulante ({ac:,.2f}) — "
                "posible extracción incorrecta de activo_circulante"
            )

        if ac > 0 and at > 0 and ac > at:
            warnings.append(
                f"activo_circulante ({ac:,.2f}) > activo_total ({at:,.2f}) — "
                "posible extracción incorrecta"
            )

        if af > 0 and at > 0 and af > at:
            warnings.append(
                f"activo_fijo ({af:,.2f}) > activo_total ({at:,.2f}) — "
                "posible extracción incorrecta"
            )

        if plp > 0 and pt > 0 and plp > pt:
            warnings.append(
                f"pasivo_largo_plazo ({plp:,.2f}) > pasivo_total ({pt:,.2f}) — "
                "posible extracción incorrecta"
            )

        # 2. Ecuación contable: Activo = Pasivo + Capital (±tolerancia)
        #    Se omite si pasivo_total viene de math_rescue (se derivó de la ecuación).
        if (
            at > 0 and pt > 0 and cc > 0
            and _method("pasivo_total") != "math_rescue"
        ):
            suma = pt + cc
            diff_rel = abs(at - suma) / at
            if diff_rel > tolerancia:
                warnings.append(
                    f"Ecuación contable rota: activo ({at:,.2f}) ≠ "
                    f"pasivo ({pt:,.2f}) + capital ({cc:,.2f}) — "
                    f"diferencia {diff_rel * 100:.1f}%"
                )

        # 3. Consistencia P&L: utilidad neta no puede superar utilidad antes de impuestos
        if uai != 0 and un != 0 and abs(un) > abs(uai) * 1.05:
            warnings.append(
                f"utilidad_neta ({un:,.2f}) > utilidad_antes_impuestos ({uai:,.2f}) — "
                "posible inversión de valores"
            )

        # 4. Valores obligatoriamente positivos
        if at < 0:
            warnings.append(f"activo_total negativo ({at:,.2f}) — valor imposible")
        if vn < 0:
            warnings.append(f"ventas_netas negativas ({vn:,.2f}) — revisar extracción")

        # 5. Cuentas compuestas: informativo, no bloqueante
        for concept_key, info in tr.items():
            if info.get("composed"):
                marker = info.get("composed_marker", "")
                warnings.append(
                    f"{concept_key}: valor extraído de una cuenta compuesta "
                    f"(fila contiene '{marker}'). Incluye sub-cuentas que no pueden "
                    f"separarse sin información adicional."
                )

        if warnings:
            for w in warnings:
                print(f"  ⚠️  Validación    : {w}")

        return warnings or None

    # -------------------------------------------------------------------------
    # Escala
    # -------------------------------------------------------------------------
    def _detect_scale(self, data: Dict[str, Any]) -> int:
        """Detecta la escala (miles o millones) en el texto del documento para normalizar los valores absolutos."""
        text = str(data.get("text_content", "")).lower()
        if re.search(r'\b(millones\s+de\s+pesos|cifras\s+en\s+millones|en\s+millones|mdp|millones\s+de\s+dólares)\b', text):
            return 1000000
        if re.search(r'\b(miles\s+de\s+pesos|cifras\s+en\s+miles|en\s+miles)\b', text):
            return 1000
        return 1

    # -------------------------------------------------------------------------
    # KPIs
    # -------------------------------------------------------------------------
    def calcular_rentabilidad(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0, formato_perfil: str = "vertical_simple", col_index_balance: Optional[int] = None, col_index_resultados: Optional[int] = None) -> Dict[str, Any]:
        """Calcula indicadores de rentabilidad cruzando Balance y Estado de Resultados.

        col_index_balance / col_index_resultados: índices independientes por documento (recomendado).
        col_index: valor legacy usado como fallback si los duales no se proveen.
        """
        self._trace_buffer.clear()
        self._current_periodicidad = periodicidad
        self._current_formato_perfil = formato_perfil
        tablas_resultados = self._get_tables(resultados_data)
        tablas_balance = self._get_tables(balance_data)
        usar_acumulado, dias_periodo = self._parse_periodicidad(periodicidad)

        idx_b = col_index_balance if col_index_balance is not None else col_index
        idx_r = col_index_resultados if col_index_resultados is not None else col_index

        multiplicador = max(self._detect_scale(balance_data), self._detect_scale(resultados_data))
        ventas_netas = self._find_value(tablas_resultados, self.kw_ventas_netas, take_last=usar_acumulado, col_index=idx_r, concept_key="ventas_netas") * multiplicador
        if ventas_netas == 0:
            ventas_netas = self._find_value(tablas_resultados, ["ingresos"], take_last=usar_acumulado, col_index=idx_r) * multiplicador

        utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_neta, take_last=usar_acumulado, col_index=idx_r, skip_if_row_contains=["atribuible", "controladora", "no controladora", "minoritaria", "mayoritaria", "participación", "participacion"], concept_key="utilidad_neta") * multiplicador

        # Fallback 1: buscar utilidad antes de impuestos en el Estado de Resultados
        if utilidad_neta == 0:
            utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_antes_impuestos, take_last=usar_acumulado, col_index=idx_r, concept_key="utilidad_antes_impuestos") * multiplicador

        # Fallback 2: buscar utilidad neta en el Balance General
        if utilidad_neta == 0:
            utilidad_neta = self._find_value(tablas_balance, self.kw_utilidad_neta, take_last=usar_acumulado, col_index=idx_b) * multiplicador

        if utilidad_neta == 0:
                utilidad_neta = self._find_value(tablas_balance, self.kw_utilidad_antes_impuestos, take_last=usar_acumulado, col_index=idx_b) * multiplicador

        # 3) Balance
        activo_total = self._find_value(tablas_balance, self.kw_activo_total, take_last=usar_acumulado, col_index=idx_b, concept_key="activo_total") * multiplicador
        capital_contable = self._find_value(tablas_balance, self.kw_capital, take_last=usar_acumulado, col_index=idx_b, skip_if_row_contains=["pasivo y capital", "pasivo + capital", "pasivo y hacienda"], concept_key="capital_contable") * multiplicador

        if capital_contable == 0:
            rescatado = self._suma_subcuentas(
                tablas_balance,
                [self.kw_capital_social, self.kw_reservas, self.kw_utilidades_acumuladas],
                idx_b, usar_acumulado, multiplicador,
            )
            if rescatado > 0:
                capital_contable = rescatado
                self._record_rescue("capital_contable", "suma: capital_social+reservas+utilidades_acum", capital_contable)

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

        nota = self._nota_periodo(periodicidad)

        trace = self._collect_trace()
        warnings = self._validate_extractions(
            {"ventas_netas": ventas_netas, "activo_total": activo_total,
             "capital_contable": capital_contable},
            trace=trace,
        )

        return {
            "datos_crudos": {
                "utilidad_neta": utilidad_neta,
                "ventas_netas": ventas_netas,
                "activo_total": activo_total,
                "capital_contable": capital_contable,
                "multiplicador": multiplicador,
                "_extraction_trace": trace,
                "_warnings": warnings,
                "fuentes": self._collect_fuentes(["utilidad_neta", "ventas_netas", "activo_total", "capital_contable"]),
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
                    **({"nota_periodo": nota} if nota else {}),
                },
                {
                    "label": "Rendimiento sobre el Patrimonio",
                    "value": f"{roe * 100:.2f}%",
                    "status": "ok" if roe >= roe_ok else ("warn" if roe >= 0 else "danger"),
                    **({"nota_periodo": nota} if nota else {}),
                },
            ],
        }

    def calcular_liquidez(self, balance_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0, formato_perfil: str = "vertical_simple", col_index_balance: Optional[int] = None) -> Dict[str, Any]:
        """Calcula indicadores de liquidez usando únicamente el Balance General."""
        self._trace_buffer.clear()
        self._current_periodicidad = periodicidad
        self._current_formato_perfil = formato_perfil
        tablas_balance = self._get_tables(balance_data)
        usar_acumulado, _ = self._parse_periodicidad(periodicidad)

        idx_b = col_index_balance if col_index_balance is not None else col_index

        multiplicador = self._detect_scale(balance_data)

        activo_circulante = self._find_value(tablas_balance, self.kw_activo_circulante, take_last=usar_acumulado, col_index=idx_b, concept_key="activo_circulante") * multiplicador
        pasivo_circulante = self._find_value(tablas_balance, self.kw_pasivo_circulante, take_last=usar_acumulado, col_index=idx_b, concept_key="pasivo_circulante") * multiplicador
        inventario = self._find_value(tablas_balance, self.kw_inventario, take_last=usar_acumulado, col_index=idx_b, concept_key="inventario") * multiplicador

        if activo_circulante == 0:
            rescatado = self._suma_subcuentas(
                tablas_balance,
                [self.kw_efectivo, self.kw_cuentas_por_cobrar, self.kw_inventario, self.kw_pagos_anticipados],
                idx_b, usar_acumulado, multiplicador,
            )
            if rescatado > 0:
                activo_circulante = rescatado
                self._record_rescue("activo_circulante", "suma: efectivo+clientes+inventario+anticipos", activo_circulante)

        if pasivo_circulante == 0:
            rescatado = self._suma_subcuentas(
                tablas_balance,
                [self.kw_proveedores, self.kw_ptu_pagar, self.kw_isr_pagar],
                idx_b, usar_acumulado, multiplicador,
            )
            if rescatado > 0:
                pasivo_circulante = rescatado
                self._record_rescue("pasivo_circulante", "suma: proveedores+ptu+isr", pasivo_circulante)

        if pasivo_circulante < 0:
            pasivo_circulante = abs(pasivo_circulante)

        trace = self._collect_trace()
        warnings = self._validate_extractions(
            {"activo_circulante": activo_circulante,
             "pasivo_circulante": pasivo_circulante,
             "inventario": inventario},
            trace=trace,
        )

        razon_liquidez = (activo_circulante / pasivo_circulante) if pasivo_circulante else 0
        prueba_acido = ((activo_circulante - inventario) / pasivo_circulante) if pasivo_circulante else 0
        capital_trabajo = activo_circulante - pasivo_circulante

        return {
            "datos_crudos": {
                "activo_circulante": activo_circulante,
                "pasivo_circulante": pasivo_circulante,
                "inventario": inventario,
                "multiplicador": multiplicador,
                "_extraction_trace": trace,
                "_warnings": warnings,
                "fuentes": self._collect_fuentes(["activo_circulante", "pasivo_circulante", "inventario"]),
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

    def calcular_endeudamiento(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0, formato_perfil: str = "vertical_simple", col_index_balance: Optional[int] = None, col_index_resultados: Optional[int] = None) -> Dict[str, Any]:
        """Calcula indicadores de endeudamiento cruzando Balance y Estado de Resultados."""
        self._trace_buffer.clear()
        self._current_periodicidad = periodicidad
        self._current_formato_perfil = formato_perfil
        tablas_balance = self._get_tables(balance_data)
        tablas_resultados = self._get_tables(resultados_data)
        usar_acumulado, _ = self._parse_periodicidad(periodicidad)

        idx_b = col_index_balance if col_index_balance is not None else col_index
        idx_r = col_index_resultados if col_index_resultados is not None else col_index

        multiplicador = max(self._detect_scale(balance_data), self._detect_scale(resultados_data))

        # --- EXTRACCIÓN DEL BALANCE ---
        activo_total = self._find_value(tablas_balance, self.kw_activo_total, take_last=usar_acumulado, col_index=idx_b, concept_key="activo_total") * multiplicador

        # Renombramos a capital_contable para evitar confusiones y asegurar la fórmula
        capital_contable = self._find_value(tablas_balance, self.kw_capital, take_last=usar_acumulado, col_index=idx_b, skip_if_row_contains=["pasivo y capital", "pasivo + capital", "pasivo y hacienda"], concept_key="capital_contable") * multiplicador

        if capital_contable == 0:
            rescatado = self._suma_subcuentas(
                tablas_balance,
                [self.kw_capital_social, self.kw_reservas, self.kw_utilidades_acumuladas],
                idx_b, usar_acumulado, multiplicador,
            )
            if rescatado > 0:
                capital_contable = rescatado
                self._record_rescue("capital_contable", "suma: capital_social+reservas+utilidades_acum", capital_contable)

        pasivo_total_doc = self._find_value(tablas_balance, self.kw_pasivo_total, take_last=usar_acumulado, col_index=idx_b, skip_if_row_contains=["capital contable", "y capital", "+ capital", "y hacienda"], concept_key="pasivo_total") * multiplicador

        # Lógica de rescate para Pasivo Total (Ecuación Contable: P = A - C)
        # Si no lo encuentra (0) o si captura la fila "Total Pasivo + Capital" (>= activo_total)
        if (pasivo_total_doc == 0 or pasivo_total_doc >= activo_total) and activo_total > 0:
            pasivo_total = activo_total - capital_contable
            self._record_rescue("pasivo_total", "activo_total - capital_contable", pasivo_total)
        else:
            pasivo_total = pasivo_total_doc

        # Limpieza de signos
        if pasivo_total < 0: pasivo_total = abs(pasivo_total)



        # --- EXTRACCIÓN DEL ESTADO DE RESULTADOS ---
        utilidad_operacion = self._find_value(tablas_resultados, self.kw_utilidad_operacion, take_last=usar_acumulado, col_index=idx_r, skip_if_row_contains=["neta", "total", "ejercicio", "antes de", "cambiaria", "bruta", "financier"], concept_key="utilidad_operacion") * multiplicador
        intereses = self._find_value(tablas_resultados, self.kw_intereses, take_last=usar_acumulado, col_index=idx_r, concept_key="gastos_financieros", skip_if_row_contains=["de operacion", "operativos", "de venta", "de administracion"]) * multiplicador
        utilidad_neta = self._find_value(tablas_resultados, self.kw_utilidad_neta, take_last=usar_acumulado, col_index=idx_r, skip_if_row_contains=["atribuible", "controladora", "no controladora", "minoritaria", "mayoritaria", "participación", "participacion"], concept_key="utilidad_neta") * multiplicador
        impuestos = self._find_value(tablas_resultados, self.kw_impuestos, take_last=usar_acumulado, col_index=idx_r, concept_key="impuestos") * multiplicador

        if intereses < 0: intereses = abs(intereses)
        if impuestos < 0: impuestos = abs(impuestos)

        # --- LÓGICA DE RESCATE (100% UNIVERSAL Y MATEMÁTICA) ---
        if utilidad_operacion == 0 or utilidad_operacion == intereses:
            # Rescate Nivel 1: EBT + Intereses
            util_antes_imp = self._find_value(tablas_resultados, self.kw_utilidad_antes_impuestos, take_last=usar_acumulado, col_index=idx_r, concept_key="utilidad_antes_impuestos") * multiplicador

            if util_antes_imp != 0:
                utilidad_operacion = util_antes_imp + intereses
                self._record_rescue("utilidad_operacion", "utilidad_antes_impuestos + gastos_financieros", utilidad_operacion)
            elif utilidad_neta != 0:
                # Rescate Nivel 2: Utilidad Neta + Impuestos Reales Extraídos + Intereses
                utilidad_operacion = utilidad_neta + impuestos + intereses
                self._record_rescue("utilidad_operacion", "utilidad_neta + impuestos + gastos_financieros", utilidad_operacion)

        # --- CÁLCULOS ---
        apalancamiento = (pasivo_total / activo_total) if activo_total else 0
        cobertura_intereses = (utilidad_operacion / intereses) if intereses else 0
        estabilidad_financiera = (pasivo_total / capital_contable) if capital_contable else 0

        trace = self._collect_trace()
        warnings = self._validate_extractions(
            {"activo_total": activo_total, "pasivo_total": pasivo_total,
             "capital_contable": capital_contable, "ventas_netas": 0},
            trace=trace,
        )

        return {
            "datos_crudos": {
                "pasivo_total": pasivo_total,
                "activo_total": activo_total,
                "capital_social": capital_contable,  # campo llamado capital_social por compatibilidad con el frontend, pero el valor es capital_contable
                "utilidad_operacion": utilidad_operacion,
                "intereses": intereses,
                "multiplicador": multiplicador,
                "_extraction_trace": trace,
                "_warnings": warnings,
                "fuentes": self._collect_fuentes(["pasivo_total", "activo_total", "capital_contable", "utilidad_operacion", "gastos_financieros", "utilidad_neta", "impuestos"]),
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

    def calcular_rotacion(self, balance_data: Dict[str, Any], resultados_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0, formato_perfil: str = "vertical_simple", col_index_balance: Optional[int] = None, col_index_resultados: Optional[int] = None) -> Dict[str, Any]:
        """Calcula indicadores de rotación adaptándose dinámicamente al tipo de periodo."""
        self._trace_buffer.clear()
        self._current_periodicidad = periodicidad
        self._current_formato_perfil = formato_perfil
        tablas_balance = self._get_tables(balance_data)
        tablas_resultados = self._get_tables(resultados_data)
        usar_acumulado, dias_periodo = self._parse_periodicidad(periodicidad)

        idx_b = col_index_balance if col_index_balance is not None else col_index
        idx_r = col_index_resultados if col_index_resultados is not None else col_index

        multiplicador = max(self._detect_scale(balance_data), self._detect_scale(resultados_data))

        # --- EXTRACCIÓN BÁSICA ---
        cuentas_por_cobrar = self._find_value(tablas_balance, self.kw_cuentas_por_cobrar, take_last=usar_acumulado, col_index=idx_b, skip_if_row_contains=["nacionales", "extranjeros"], concept_key="cuentas_por_cobrar") * multiplicador
        inventario = self._find_value(tablas_balance, self.kw_inventario, take_last=usar_acumulado, col_index=idx_b, concept_key="inventario") * multiplicador
        activo_fijo_neto = self._find_value(tablas_balance, self.kw_activo_fijo, take_last=usar_acumulado, col_index=idx_b, concept_key="activo_fijo") * multiplicador

        if activo_fijo_neto == 0:
            rescatado = self._suma_subcuentas(
                tablas_balance,
                [self.kw_terrenos, self.kw_maquinaria_equipo],
                idx_b, usar_acumulado, multiplicador,
                kw_lists_sub=[self.kw_depreciacion_acum],
            )
            if rescatado > 0:
                activo_fijo_neto = rescatado
                self._record_rescue("activo_fijo", "suma: terrenos+maquinaria-depreciacion_acum", activo_fijo_neto)

        activo_total = self._find_value(tablas_balance, self.kw_activo_total, take_last=usar_acumulado, col_index=idx_b, concept_key="activo_total") * multiplicador

        # Usamos nuestra variable dinámica 'usar_acumulado' en lugar del True hardcodeado
        ventas_netas = self._find_value(tablas_resultados, self.kw_ventas_netas, take_last=usar_acumulado, col_index=idx_r, concept_key="ventas_netas") * multiplicador

        if ventas_netas == 0:
            ventas_netas = self._find_value(tablas_resultados, ["ingresos"], take_last=usar_acumulado, col_index=idx_r) * multiplicador

        costo_directo = self._find_value(tablas_resultados, self.kw_costo_de_ventas, take_last=usar_acumulado, col_index=idx_r, concept_key="costo_de_ventas") * multiplicador
        compras = self._find_value(tablas_resultados, self.kw_compras, take_last=usar_acumulado, col_index=idx_r) * multiplicador
        devoluciones = self._find_value(tablas_resultados, self.kw_devoluciones_costo, take_last=usar_acumulado, col_index=idx_r) * multiplicador
        
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

        nota = self._nota_periodo(periodicidad)

        trace = self._collect_trace()
        warnings = self._validate_extractions(
            {"activo_total": activo_total, "activo_fijo": activo_fijo_neto,
             "inventario": inventario, "ventas_netas": ventas_netas},
            trace=trace,
        )

        return {
            "datos_crudos": {
                "cuentas_por_cobrar": cuentas_por_cobrar,
                "inventario": inventario,
                "activo_fijo_neto": activo_fijo_neto,
                "activo_total": activo_total,
                "ventas_netas": ventas_netas,
                "costo_ventas": costo_ventas_calculado,
                "dias_calculo": dias_periodo,
                "multiplicador": multiplicador,
                "_extraction_trace": trace,
                "_warnings": warnings,
                "fuentes": self._collect_fuentes(["cuentas_por_cobrar", "inventario", "activo_fijo", "activo_total", "ventas_netas", "costo_de_ventas"]),
            },
            "kpis": [
                {
                    "label": "Rotación de la Cartera",
                    "value": f"{rotacion_cartera:.2f}",
                    "status": "ok" if rotacion_cartera >= rot_cartera_ok else ("warn" if rotacion_cartera > 0 else "danger"),
                    **({"nota_periodo": nota} if nota else {}),
                },
                {
                    "label": "Periodo Promedio de Recaudo",
                    "value": f"{periodo_recaudo:,.0f} días",
                    "status": "ok" if 0 < periodo_recaudo <= 60 else ("warn" if 60 < periodo_recaudo <= 90 else "danger"),
                },
                {
                    "label": "Rotación de Inventarios",
                    "value": "N/A" if inventario == 0 else f"{rotacion_inventarios:.2f}",
                    "status": "neutral" if inventario == 0 else ("ok" if rotacion_inventarios > 0 else "danger"),
                    **({"nota_periodo": nota} if nota and inventario != 0 else {}),
                },
                {
                    "label": "Rotación de Activos Fijos",
                    "value": f"{rotacion_activos_fijos:.2f}",
                    "status": "ok" if rotacion_activos_fijos >= rot_af_ok else ("warn" if rotacion_activos_fijos >= rot_af_warn else "danger"),
                    **({"nota_periodo": nota} if nota else {}),
                },
                {
                    "label": "Rotación de Activos Totales",
                    "value": f"{rotacion_activos_totales:.2f}",
                    "status": "ok" if rotacion_activos_totales >= rot_at_ok else ("warn" if rotacion_activos_totales >= rot_at_warn else "danger"),
                    **({"nota_periodo": nota} if nota else {}),
                },
            ],
        }

    def calcular_estructura(self, balance_data: Dict[str, Any], periodicidad: str = "anual", col_index: int = 0, formato_perfil: str = "vertical_simple", col_index_balance: Optional[int] = None) -> Dict[str, Any]:
        """Calcula indicadores de estructura financiera basándose en el Balance General."""
        self._trace_buffer.clear()
        self._current_periodicidad = periodicidad
        self._current_formato_perfil = formato_perfil
        tablas_balance = self._get_tables(balance_data)
        usar_acumulado, _ = self._parse_periodicidad(periodicidad)

        idx_b = col_index_balance if col_index_balance is not None else col_index

        multiplicador = self._detect_scale(balance_data)

        # --- 1. EXTRACCIÓN BÁSICA ---
        activo_total = self._find_value(tablas_balance, self.kw_activo_total, take_last=usar_acumulado, col_index=idx_b, concept_key="activo_total") * multiplicador
        activo_fijo = self._find_value(tablas_balance, self.kw_activo_fijo, take_last=usar_acumulado, col_index=idx_b, concept_key="activo_fijo") * multiplicador

        if activo_fijo == 0:
            rescatado = self._suma_subcuentas(
                tablas_balance,
                [self.kw_terrenos, self.kw_maquinaria_equipo],
                idx_b, usar_acumulado, multiplicador,
                kw_lists_sub=[self.kw_depreciacion_acum],
            )
            if rescatado > 0:
                activo_fijo = rescatado
                self._record_rescue("activo_fijo", "suma: terrenos+maquinaria-depreciacion_acum", activo_fijo)

        pasivo_total_doc = self._find_value(tablas_balance, self.kw_pasivo_total, take_last=usar_acumulado, col_index=idx_b, skip_if_row_contains=["capital contable", "y capital", "y hacienda"], concept_key="pasivo_total") * multiplicador
        capital_contable = self._find_value(tablas_balance, self.kw_capital, take_last=usar_acumulado, col_index=idx_b, skip_if_row_contains=["pasivo y capital", "pasivo + capital", "pasivo y hacienda", "minoritario", "mayoritario", "minoritaria", "mayoritaria", "participación", "participacion"], concept_key="capital_contable") * multiplicador

        if capital_contable == 0:
            rescatado = self._suma_subcuentas(
                tablas_balance,
                [self.kw_capital_social, self.kw_reservas, self.kw_utilidades_acumuladas],
                idx_b, usar_acumulado, multiplicador,
            )
            if rescatado > 0:
                capital_contable = rescatado
                self._record_rescue("capital_contable", "suma: capital_social+reservas+utilidades_acum", capital_contable)

        pasivo_largo_plazo = self._find_value(tablas_balance, self.kw_pasivo_largo_plazo, take_last=usar_acumulado, col_index=idx_b, skip_if_row_contains=["capital", "circulante", "corto", "deudores", "acreedores", "clientes", "activo"], concept_key="pasivo_largo_plazo") * multiplicador
        pasivo_circulante = self._find_value(tablas_balance, self.kw_pasivo_circulante, take_last=usar_acumulado, col_index=idx_b, concept_key="pasivo_circulante") * multiplicador

        if pasivo_circulante == 0:
            rescatado = self._suma_subcuentas(
                tablas_balance,
                [self.kw_proveedores, self.kw_ptu_pagar, self.kw_isr_pagar],
                idx_b, usar_acumulado, multiplicador,
            )
            if rescatado > 0:
                pasivo_circulante = rescatado
                self._record_rescue("pasivo_circulante", "suma: proveedores+ptu+isr", pasivo_circulante)

        # --- 2. LÓGICA INTELIGENTE PARA CAPITAL SOCIAL ---
        capital_social_doc = self._find_value(tablas_balance, self.kw_capital_social, take_last=usar_acumulado, col_index=idx_b, skip_if_row_contains=["pasivo y capital", "pasivo + capital", "pasivo y hacienda", "minoritario", "mayoritario", "contable"]) * multiplicador
        capital_variable = self._find_value(tablas_balance, ["capital variable", "capital social variable"], take_last=usar_acumulado, col_index=idx_b) * multiplicador
        capital_fijo = self._find_value(tablas_balance, ["capital fijo", "capital social fijo"], take_last=usar_acumulado, col_index=idx_b) * multiplicador
        
        suma_capitales = capital_fijo + capital_variable

        if suma_capitales > capital_social_doc:
            capital_social = suma_capitales
            self._record_rescue("capital_social", "capital_social_fijo + capital_social_variable", capital_social)
        elif capital_social_doc == capital_variable and capital_fijo == 0 and capital_variable > 0:
            capital_social = capital_social_doc + capital_variable
            self._record_rescue("capital_social", "capital_social_doc + capital_social_variable (duplicado detectado)", capital_social)
        else:
            capital_social = capital_social_doc

        # --- 3. RESCATE PARA PASIVO TOTAL ---
        # Si lee 0, o si se confunde con "Suma de Pasivo y Capital" (dando un valor >= al activo)
        if (pasivo_total_doc == 0 or pasivo_total_doc >= activo_total) and activo_total > 0:
            pasivo_total = activo_total - capital_contable
            self._record_rescue("pasivo_total", "activo_total - capital_contable", pasivo_total)
        else:
            pasivo_total = pasivo_total_doc

        if pasivo_total < 0:
            pasivo_total = abs(pasivo_total)

        # --- 3.5. RESCATE PARA PASIVO LARGO PLAZO ---
        # Si no lo encontró, o si capturó solo una fracción (ej. "Otros pasivos de largo plazo"),
        # asumimos que el pasivo largo plazo debería ser la diferencia exacta entre Total y Circulante.
        if pasivo_total > 0 and pasivo_circulante > 0:
            pasivo_largo_plazo_calc = round(pasivo_total - pasivo_circulante, 2)
            if pasivo_largo_plazo == 0 or pasivo_largo_plazo < (pasivo_largo_plazo_calc * 0.8):
                pasivo_largo_plazo = pasivo_largo_plazo_calc
                self._record_rescue("pasivo_largo_plazo", "pasivo_total - pasivo_circulante", pasivo_largo_plazo)

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
        trace = self._collect_trace()
        warnings = self._validate_extractions(
            {"activo_total": activo_total, "pasivo_total": pasivo_total,
             "capital_contable": capital_contable, "activo_fijo": activo_fijo,
             "pasivo_largo_plazo": pasivo_largo_plazo,
             "pasivo_circulante": pasivo_circulante},
            trace=trace,
        )

        return {
            "datos_crudos": {
                "activo_total": activo_total,
                "pasivo_total": pasivo_total,
                "capital_social": capital_social,
                "capital_contable": capital_contable,
                "activo_fijo": activo_fijo,
                "pasivo_largo_plazo": pasivo_largo_plazo,
                "multiplicador": multiplicador,
                "_extraction_trace": trace,
                "_warnings": warnings,
                "fuentes": self._collect_fuentes(["activo_total", "pasivo_total", "capital_social", "capital_contable", "activo_fijo", "pasivo_largo_plazo", "pasivo_circulante"]),
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
                    "status": "neutral" if seguridad_largo_plazo is None else ("ok" if seguridad_largo_plazo >= 1.0 else ("warn" if seguridad_largo_plazo >= 0.5 else "danger")),
                },
                {
                    "label": "Inmovilización de Cap. Social",
                    "value": "N/A" if capital_social == 0 else f"{inmovilizacion_social:.2f}",
                    "status": "neutral" if capital_social == 0 else ("ok" if inmovilizacion_social <= 1.0 else ("warn" if inmovilizacion_social <= 1.5 else "danger")), 
                },
                {
                    "label": "Inmovilización de Cap. Contable",
                    "value": f"{inmovilizacion_contable:.2f}",
                    "status": "ok" if inmovilizacion_contable <= 1.0 else ("warn" if inmovilizacion_contable <= 1.5 else "danger"),
                },
            ],
        }