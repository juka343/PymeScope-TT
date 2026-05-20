from pydantic import BaseModel, Field
from typing import List, Optional

class LineaSupuesto(BaseModel):
    concepto: str
    variacion: Optional[float] = None
    mantener_igual: bool

class ProyeccionSupuestosRequest(BaseModel):
    project_id: str
    period_id: str
    results_url: str
    periodo_proyectado_label: str
    inflacion_esperada: float
    periodo_base: Optional[str] = None
    ingresos: List[LineaSupuesto]
    costos: List[LineaSupuesto]
    impuestos: List[LineaSupuesto]

class FilaProyectada(BaseModel):
    concepto: str
    valor_base: float
    variacion_aplicada: float
    valor_proyectado: float

class ResultadoProyeccion(BaseModel):
    tablas_proyectadas: List[FilaProyectada]
    # Subtotales para el Estado de Resultados Proforma
    utilidad_bruta: Optional[float] = None
    utilidad_operativa: Optional[float] = None
    utilidad_antes_impuestos: Optional[float] = None
    impuestos_totales: Optional[float] = None
    utilidad_neta: Optional[float] = None
    # Subtotales para el Balance General Proforma
    total_activo: Optional[float] = None
    total_pasivo: Optional[float] = None
    total_capital: Optional[float] = None
    fer: Optional[float] = None  # Fondos Externos Requeridos

class ProyeccionBalanceRequest(BaseModel):
    project_id: str
    period_id: str
    results_url: str
    periodo_proyectado_label: str
    inflacion_esperada: float
    utilidad_neta_proforma: float
    ventas_proy_incremento_pct: float
    total_impuestos_proforma: float = 0.0
    utilidad_neta_base: float = 0.0
    periodicidad: str = "mensual"
    activo_circulante: List[LineaSupuesto]
    activo_no_circulante: List[LineaSupuesto]
    pasivo_corto_plazo: List[LineaSupuesto]
    pasivo_largo_plazo: List[LineaSupuesto]
    capital_contribuido: List[LineaSupuesto]
    capital_ganado: List[LineaSupuesto]

class SolicitudAnalisisFER(BaseModel):
    project_id: str
    analysis_payload: dict

class AlertIAFER(BaseModel):
    severityKey: str
    title: str
    message: str
    implication: str

class RecommendationIAFER(BaseModel):
    title: str
    description: str
    reason: str

class RespuestaFERIA(BaseModel):
    summary: str
    paragraph: str         # Un solo párrafo conciso, máximo 2 oraciones
    alerts: List[AlertIAFER]
    recommendations: List[RecommendationIAFER]


# --- MODELOS PARA PROYECCIONES MULTIPERIODO ---

class ColumnaSupuestosER(BaseModel):
    """Supuestos del Estado de Resultados para un periodo especifico."""
    ingresos: List[LineaSupuesto]
    costos: List[LineaSupuesto]
    impuestos: List[LineaSupuesto]
    inflacion_esperada: float = 0.0
    ventas_incremento_pct: float = 0.0  # para pasarlo al BG como referencia


class ColumnaSupuestosBG(BaseModel):
    """Supuestos del Balance General para un periodo especifico."""
    activo_circulante: List[LineaSupuesto]
    activo_no_circulante: List[LineaSupuesto]
    pasivo_corto_plazo: List[LineaSupuesto]
    pasivo_largo_plazo: List[LineaSupuesto]
    capital_contribuido: List[LineaSupuesto]
    capital_ganado: List[LineaSupuesto]


class MultiPeriodoRequest(BaseModel):
    """
    Payload principal del endpoint /multiperiodo.
    Recibe las URLs de los PDFs base y N columnas de supuestos
    (una por cada periodo a proyectar).
    """
    # Configuracion del proyecto
    periodicidad: str = "mensual"  # "mensual", "trimestral", "anual"
    n_periodos: int = Field(..., ge=1, le=5, description="Numero de periodos a proyectar (maximo 5)")
    periodos: List[str] = Field(..., description="Etiquetas de cada periodo. Ej: ['Febrero 2026', 'Marzo 2026']")

    # URLs de los PDFs base - el backend descarga el OCR en tiempo de ejecucion
    url_er_base: str = Field(..., description="URL del PDF del Estado de Resultados base")
    url_bg_base: str = Field(..., description="URL del PDF del Balance General base")

    # Supuestos por periodo - una columna por cada periodo
    columnas_er: List[ColumnaSupuestosER] = Field(..., description="Supuestos del ER, uno por periodo")
    columnas_bg: List[ColumnaSupuestosBG] = Field(..., description="Supuestos del BG, uno por periodo")

    # Datos adicionales del contexto financiero
    utilidad_neta_base: float = 0.0   # utilidad real del PDF base (guardada en Firebase)
    project_id: str = ""              # para guardar resultados en Firebase
    periodo_base_label: str = ""      # label del periodo base original del PDF (ej. "Enero 2026")


# --- MODELOS PARA FLUJO MULTIPERIODO EN DOS PASOS ---

class ERPeriodoResultado(BaseModel):
    """Resultado del ER de un periodo - para pasarlo al endpoint del BG."""
    periodo: str
    numero: int
    utilidad_neta: float = 0.0
    impuestos_totales: float = 0.0
    utilidad_neta_base: float = 0.0
    tablas_proyectadas: List[dict] = []


class MultiPeriodoBGRequest(BaseModel):
    """
    Payload para el paso 2 del flujo multiperiodo: calcular los BGs.
    Recibe los resultados del ER ya calculados y los supuestos del BG.
    """
    periodicidad: str = "mensual"
    n_periodos: int = Field(..., ge=1, le=5)
    periodos: List[str]
    url_bg_base: str
    utilidad_neta_base: float = 0.0
    periodo_base_label: str = ""      # label del periodo base original del PDF (mensual)
    columnas_bg: List[ColumnaSupuestosBG]
    # Resultados del ER por periodo - vienen del paso 1
    resultados_er: List[ERPeriodoResultado]
