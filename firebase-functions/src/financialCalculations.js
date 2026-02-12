function metric(value, formula, interpretation, riskLevel) {
  return { value, formula, interpretation, riskLevel };
}

function safeDivide(numerator, denominator) {
  if (!denominator) {
    return 0;
  }
  return numerator / denominator;
}

function calculateLiquidityRatios(balance) {
  const currentAssets = balance.activos.circulantes;
  const currentLiabilities = balance.pasivos.cortoPlazo;
  const ratio = safeDivide(currentAssets, currentLiabilities);
  const quickRatio = safeDivide(currentAssets, currentLiabilities);
  const workingCapital = currentAssets - currentLiabilities;

  return {
    razon_circulante: metric(
      ratio,
      "activos_circulantes / pasivos_corto_plazo",
      ratio >= 1.2 ? "Liquidez adecuada" : "Liquidez baja",
      ratio >= 1.2 ? "low" : "medium"
    ),
    prueba_acido: metric(
      quickRatio,
      "(activos_circulantes - inventarios) / pasivos_corto_plazo",
      quickRatio >= 1 ? "Cobertura inmediata" : "Cobertura insuficiente",
      quickRatio >= 1 ? "low" : "high"
    ),
    capital_trabajo: metric(
      workingCapital,
      "activos_circulantes - pasivos_corto_plazo",
      workingCapital >= 0 ? "Capital de trabajo positivo" : "Capital de trabajo negativo",
      workingCapital >= 0 ? "low" : "high"
    ),
  };
}

function calculateProfitabilityRatios(income, balance) {
  const margin = safeDivide(income.utilidadNeta, income.ingresos);
  const assets = balance.activos.circulantes + balance.activos.noCirculantes;
  const rat = safeDivide(income.utilidadNeta, assets);
  const roe = safeDivide(income.utilidadNeta, balance.capitalContable);

  return {
    margen_utilidad: metric(
      margin,
      "utilidad_neta / ingresos",
      margin >= 0.1 ? "Margen saludable" : "Margen bajo",
      margin >= 0.1 ? "low" : "medium"
    ),
    rat: metric(
      rat,
      "utilidad_neta / activos_totales",
      rat >= 0.08 ? "Buen rendimiento sobre activos" : "Rendimiento bajo",
      rat >= 0.08 ? "low" : "medium"
    ),
    roe: metric(
      roe,
      "utilidad_neta / capital_contable",
      roe >= 0.1 ? "Buen retorno a socios" : "Retorno limitado",
      roe >= 0.1 ? "low" : "medium"
    ),
  };
}

function calculateLeverageRatios(balance, income) {
  const totalLiabilities = balance.pasivos.cortoPlazo + balance.pasivos.largoPlazo;
  const debtToEquity = safeDivide(totalLiabilities, balance.capitalContable);
  const interestCoverage = safeDivide(income.utilidadOperativa, Math.max(income.gastos, 1));

  return {
    apalancamiento_total: metric(
      debtToEquity,
      "pasivos_totales / capital_contable",
      debtToEquity <= 1.5 ? "Apalancamiento controlado" : "Apalancamiento alto",
      debtToEquity <= 1.5 ? "low" : "high"
    ),
    cobertura_intereses: metric(
      interestCoverage,
      "utilidad_operativa / gastos_financieros",
      interestCoverage >= 2 ? "Cobertura saludable" : "Cobertura riesgosa",
      interestCoverage >= 2 ? "low" : "high"
    ),
    estabilidad_financiera: metric(
      safeDivide(balance.capitalContable, balance.capitalContable + totalLiabilities),
      "capital_contable / (capital_contable + pasivos_totales)",
      "Participacion del capital propio",
      "medium"
    ),
  };
}

function calculateStructureRatios(balance) {
  const totalAssets = balance.activos.circulantes + balance.activos.noCirculantes;
  const solvency = safeDivide(totalAssets, balance.pasivos.cortoPlazo + balance.pasivos.largoPlazo);

  return {
    solvencia: metric(
      solvency,
      "activos_totales / pasivos_totales",
      solvency >= 1.5 ? "Solvencia adecuada" : "Solvencia baja",
      solvency >= 1.5 ? "low" : "high"
    ),
    seguridad_largo_plazo: metric(
      safeDivide(balance.capitalContable, totalAssets),
      "capital_contable / activos_totales",
      "Respaldo patrimonial",
      "medium"
    ),
    inmovilizacion_cap_social: metric(
      safeDivide(balance.activos.noCirculantes, balance.capitalContable),
      "activos_no_circulantes / capital_contable",
      "Capital inmovilizado",
      "medium"
    ),
    inmovilizacion_cap_contable: metric(
      safeDivide(balance.activos.noCirculantes, totalAssets),
      "activos_no_circulantes / activos_totales",
      "Proporcion de activos fijos",
      "medium"
    ),
  };
}

function calculateRotationRatios(income, balance) {
  const sales = income.ingresos;
  const totalAssets = balance.activos.circulantes + balance.activos.noCirculantes;

  return {
    rotacion_cartera: metric(
      safeDivide(sales, Math.max(balance.activos.circulantes, 1)),
      "ventas / cuentas_por_cobrar",
      "Velocidad de cobranza",
      "medium"
    ),
    periodo_promedio_recaudo: metric(
      safeDivide(360, Math.max(safeDivide(sales, Math.max(balance.activos.circulantes, 1)), 1)),
      "360 / rotacion_cartera",
      "Dias promedio de cobro",
      "medium"
    ),
    rotacion_inventarios: metric(
      safeDivide(income.costos, Math.max(balance.activos.circulantes, 1)),
      "costos / inventarios",
      "Rotacion de inventarios",
      "medium"
    ),
    rotacion_activos_fijos: metric(
      safeDivide(sales, Math.max(balance.activos.noCirculantes, 1)),
      "ventas / activos_fijos",
      "Uso de activos fijos",
      "medium"
    ),
    rotacion_activos_totales: metric(
      safeDivide(sales, Math.max(totalAssets, 1)),
      "ventas / activos_totales",
      "Eficiencia global",
      "medium"
    ),
  };
}

function buildFinancialRatios(income, balance) {
  return {
    rentabilidad: calculateProfitabilityRatios(income, balance),
    liquidez: calculateLiquidityRatios(balance),
    estructura: calculateStructureRatios(balance),
    endeudamiento: calculateLeverageRatios(balance, income),
    rotacion: calculateRotationRatios(income, balance),
  };
}

module.exports = {
  calculateLiquidityRatios,
  calculateProfitabilityRatios,
  calculateLeverageRatios,
  calculateStructureRatios,
  calculateRotationRatios,
  buildFinancialRatios,
};
