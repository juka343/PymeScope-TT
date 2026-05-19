from pydantic import BaseModel
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
