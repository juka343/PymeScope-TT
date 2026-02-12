function generateProjectionScenarios(income, balance, options) {
  const scenarios = [];
  const scenarioRates = [
    { name: "conservador", delta: -0.02 },
    { name: "moderado", delta: 0 },
    { name: "agresivo", delta: 0.03 },
  ];

  for (const scenario of scenarioRates) {
    const growthRate = Math.max(options.baseGrowthRate + scenario.delta, 0);
    const incomeProforma = {};
    const balanceProforma = {};

    for (let year = 1; year <= options.horizonYears; year += 1) {
      const factor = Math.pow(1 + growthRate, year);
      incomeProforma[`year_${year}`] = income.ingresos * factor;
      balanceProforma[`year_${year}`] =
        (balance.activos.circulantes + balance.activos.noCirculantes) * factor;
    }

    scenarios.push({
      name: scenario.name,
      horizonYears: options.horizonYears,
      growthRate,
      incomeStatementProforma: incomeProforma,
      balanceSheetProforma: balanceProforma,
    });
  }

  return scenarios;
}

module.exports = { generateProjectionScenarios };
