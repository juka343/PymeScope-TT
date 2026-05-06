<script setup>
import { computed, ref, onMounted } from "vue";
import { collection, getDocs } from "firebase/firestore";
import { db } from "@/firebase/config";
import { useRouter, useRoute } from "vue-router";
import { useFinancialAiBlock } from "@/composables/useFinancialAiBlock";

const router = useRouter();
const route = useRoute();

const {
  loadAiResult,
  interpretationText,
  mainFindings,
  recommendationItems,
  alertItems,
  aiBlockLoading,
  aiBlockError,
} = useFinancialAiBlock("rentabilidad");

const centroDeAprendizaje = () => {
  const routeData = router.resolve({ name: "teoriaRentabilidad" });
  window.open(routeData.href, "_blank");
};

const projectId = route.params.id_proyecto;

const loading = ref(true);
const rawPeriods = ref([]);
const metrics = ref([]);
const activeKpi = ref("margen");
const tableRows = ref([]);
const hoveredPoint = ref(null);

const currencyFmt = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const parseVal = (val) => {
  if (!val) return 0;
  if (typeof val === "number") return val;
  return parseFloat(val.toString().replace(/[^0-9.-]/g, ""));
};

const fetchDashboardData = async () => {
  try {
    if (!projectId) return;

    const periodosRef = collection(db, "proyectos", projectId, "periodos");
    const snapshot = await getDocs(periodosRef);

    let loaded = [];
    snapshot.forEach((docSnap) => {
      const data = docSnap.data();
      if (data.rentabilidad || data.analisis_rentabilidad) {
        loaded.push({
          id: docSnap.id,
          label: data.label || "Periodo",
          periodDate: data.periodDate || data.label,
          rentabilidad:
            data.analisis_rentabilidad ||
            data.rentabilidad || { datos_crudos: {}, kpis: [] },
          rotacion: data.analisis_rotacion || { datos_crudos: {} },
          endeudamiento: data.analisis_endeudamiento || { datos_crudos: {} },
        });
      }
    });

    loaded.sort((a, b) => String(a.periodDate).localeCompare(String(b.periodDate)));
    rawPeriods.value = loaded;

    const kpisParaIA = loaded.map((p) => ({
      periodo: p.label,
      kpis: p.rentabilidad.kpis,
    }));

    console.log("📊 KPIs DE RENTABILIDAD (MULTIPERIODO):", kpisParaIA);

    if (loaded.length > 0) {
      generateDashboardData();
    }
  } catch (error) {
    console.error("Error cargando multiperiodo rentabilidad:", error);
  } finally {
    loading.value = false;
  }
};

const generateDashboardData = () => {
  const periods = rawPeriods.value;
  const labels = periods.map((p) => p.label);

  const findKpi = (kpis, keyword) => {
    if (!kpis) return 0;
    const item = kpis.find((k) =>
      k.label.toLowerCase().includes(keyword.toLowerCase())
    );
    return item ? parseVal(item.value) : 0;
  };

  const getKpiStatus = (kpis, keyword) => {
    if (!kpis) return "warn";
    const item = kpis.find((k) =>
      k.label.toLowerCase().includes(keyword.toLowerCase())
    );
    return item ? item.status : "warn";
  };

  const dataMargen = periods.map((p) => findKpi(p.rentabilidad.kpis, "margen"));
  const dataRat = periods.map((p) => findKpi(p.rentabilidad.kpis, "activos"));
  const dataRoe = periods.map((p) => findKpi(p.rentabilidad.kpis, "patrimonio"));

  const buildChart = (values, title, subtitle, legendLabel, type, backendStatus = "warn") => {
    const maxVal = Math.max(...values, type === "margen" ? 10 : 5);
    let minVal = Math.min(...values, 0);
    if (minVal > 0) minVal = 0;

    const rawRange = maxVal - minVal;

    let step = 5;
    if (rawRange > 15) step = 10;
    if (rawRange > 40) step = 20;
    if (rawRange > 100) step = 50;

    const yMin = Math.floor(minVal / step) * step;
    const yMax = Math.ceil(maxVal / step) * step;
    const finalRange = Math.max(yMax - yMin, 1);

    const fmtLabel = (val) => `${val.toFixed(0)}%`;

    const yAxisLabels = [
      fmtLabel(yMax),
      fmtLabel(yMax - finalRange / 3),
      fmtLabel(yMax - (finalRange / 3) * 2),
      fmtLabel(yMin),
    ];

    const xStep = periods.length > 1 ? 600 / (periods.length - 1) : 0;

    const points = values.map((val, i) => {
      const x = periods.length > 1 ? 100 + i * xStep : 400;
      const y = 230 - ((val - yMin) / finalRange) * 180;
      return {
        x,
        y,
        label: labels[i],
        bold: i === values.length - 1,
        value: val,
      };
    });

    const lastVal = values[values.length - 1];
    const prevVal = values.length > 1 ? values[values.length - 2] : lastVal;
    const delta = lastVal - prevVal;

    return {
      kpiValue: `${lastVal.toFixed(2)}%`,
      status: backendStatus,
      deltaType: delta >= 0 ? "up" : "down",
      deltaValue: `${delta > 0 ? "+" : ""}${delta.toFixed(2)}%`,
      deltaNote:
        periods.length > 1 ? `vs ${labels[labels.length - 2]}` : "Sin periodo previo",
      chartTitle: title,
      chartSubtitle: subtitle,
      legendLabel,
      yAxisLabels,
      points,
    };
  };

  const lastP = periods[periods.length - 1];

  metrics.value = [
    {
      key: "margen",
      label: "Margen de Rentabilidad",
      ...buildChart(
        dataMargen,
        "Evolución Margen de Rentabilidad",
        "Tendencia histórica por periodo",
        "Margen Neto",
        "margen",
        getKpiStatus(lastP.rentabilidad.kpis, "margen")
      ),
    },
    {
      key: "rat",
      label: "Rendimiento sobre Activos Totales (RAT)",
      ...buildChart(
        dataRat,
        "Evolución RAT",
        "Capacidad de los activos para generar utilidad",
        "RAT",
        "rat",
        getKpiStatus(lastP.rentabilidad.kpis, "activos")
      ),
    },
    {
      key: "roe",
      label: "Rendimiento sobre el Patrimonio (ROE)",
      ...buildChart(
        dataRoe,
        "Evolución ROE",
        "Rentabilidad generada sobre el capital propio",
        "ROE",
        "roe",
        getKpiStatus(lastP.rentabilidad.kpis, "patrimonio")
      ),
    },
  ];

  const reversedPeriods = [...periods].reverse();
  const reversedMargen = [...dataMargen].reverse();
  const reversedRat = [...dataRat].reverse();
  const reversedRoe = [...dataRoe].reverse();

  tableRows.value = reversedPeriods.map((p, i) => ({
    period: p.label,
    ingresos: currencyFmt.format(p.rentabilidad.datos_crudos?.ventas_netas || 0),
    utilidad: currencyFmt.format(p.rentabilidad.datos_crudos?.utilidad_neta || 0),
    margen: `${reversedMargen[i].toFixed(2)}%`,
    rat: `${reversedRat[i].toFixed(2)}%`,
    roe: `${reversedRoe[i].toFixed(2)}%`,
    highlight: i === 0,
  }));
};

const selectedKpi = computed(() => {
  if (metrics.value.length === 0) return null;
  return metrics.value.find((m) => m.key === activeKpi.value) || metrics.value[0];
});

function setActive(k) {
  activeKpi.value = k;
}

function showTooltip(p) {
  hoveredPoint.value = p;
}

function hideTooltip() {
  hoveredPoint.value = null;
}

const baselineY = 230;

const linePath = computed(() => {
  if (!selectedKpi.value) return "";
  const pts = selectedKpi.value.points;
  if (!pts.length) return "";
  return pts.map((p, i) => (i === 0 ? `M${p.x} ${p.y}` : `L${p.x} ${p.y}`)).join(" ");
});

const areaPath = computed(() => {
  if (!selectedKpi.value) return "";
  const pts = selectedKpi.value.points;
  if (!pts.length) return "";
  const first = pts[0];
  const last = pts[pts.length - 1];
  const mid = pts.map((p) => `L${p.x} ${p.y}`).join(" ");
  return `M${first.x} ${baselineY} L${first.x} ${first.y} ${mid} L${last.x} ${baselineY} Z`;
});

const analysisText = computed(() => {
  if (!selectedKpi.value) return "";

  if (selectedKpi.value.key === "margen") {
    return selectedKpi.value.status === "ok"
      ? "La empresa presenta un margen de rentabilidad favorable en su último periodo. Esto indica una buena capacidad para convertir ventas en utilidad neta."
      : "El margen de rentabilidad del último periodo es bajo respecto a niveles deseables. Conviene revisar costos, gastos operativos y políticas de precios.";
  }

  if (selectedKpi.value.key === "rat") {
    return selectedKpi.value.status === "ok"
      ? "El rendimiento sobre activos muestra que la empresa está utilizando sus recursos de forma eficiente para generar utilidad."
      : "El rendimiento sobre activos es reducido. Esto puede indicar activos sobredimensionados o bajo aprovechamiento operativo.";
  }

  return selectedKpi.value.status === "ok"
    ? "El rendimiento sobre el patrimonio es saludable y refleja una buena rentabilidad para los socios o propietarios."
    : "El rendimiento sobre el patrimonio es bajo. Es recomendable revisar la utilidad neta y la estructura de capital para mejorar el retorno al propietario.";
});

const recommendationList = computed(() => {
  if (!selectedKpi.value) return [];

  if (selectedKpi.value.key === "margen") {
    return [
      "Monitorear de cerca los márgenes de operación y costos indirectos.",
      "Revisar las estrategias de fijación de precios según inflación y proveedores.",
      "Optimizar procesos que puedan estar erosionando el margen neto.",
    ];
  }

  if (selectedKpi.value.key === "rat") {
    return [
      "Evaluar si los activos actuales están generando el rendimiento esperado.",
      "Reducir activos ociosos que no aporten valor operativo.",
      "Mejorar la productividad del activo total mediante control de costos y ventas.",
    ];
  }

  return [
    "Fortalecer la utilidad neta sin comprometer el patrimonio innecesariamente.",
    "Cuidar la estructura de capital para no diluir el rendimiento al propietario.",
    "Comparar periódicamente el ROE contra metas internas o benchmarks del sector.",
  ];
});

const finalAnalysisText = computed(() => {
  return interpretationText.value || analysisText.value;
});

const lastPeriodData = computed(() =>
  rawPeriods.value.length > 0 ? rawPeriods.value[rawPeriods.value.length - 1] : null
);

const rentabilidadBreakdown = computed(() => {
  if (!lastPeriodData.value) return { total: "$0", segments: [] };

  const rentCrudos = lastPeriodData.value.rentabilidad?.datos_crudos || {};
  const rotCrudos = lastPeriodData.value.rotacion?.datos_crudos || {};

  const ventas = rentCrudos.ventas_netas || 1;
  const utilidad = rentCrudos.utilidad_neta || 0;
  let costoVentas = rotCrudos.costo_ventas || 0;

  let gastos = ventas - costoVentas - utilidad;

  if (gastos < 0) {
    gastos = ventas - utilidad;
    costoVentas = 0;
  }

  const items = [
    { label: "Costo de Ventas", value: costoVentas, color: "#1e293b" },
    { label: "Gastos y Otros", value: gastos, color: "#299de0" },
    { label: "Utilidad Neta", value: utilidad, color: "#507c95" },
  ].filter((i) => i.value > 0);

  const totalCalculo = items.reduce((acc, curr) => acc + curr.value, 0) || 1;

  let currentOffset = 0;
  const segments = items.map((item) => {
    const pct = (item.value / totalCalculo) * 100;
    const dashoffset = -currentOffset;
    currentOffset += pct;
    return {
      ...item,
      pct: pct.toFixed(1),
      dasharray: `${pct} 100`,
      dashoffset,
    };
  });

  return {
    total: ventas >= 1000000 ? `$${(ventas / 1000000).toFixed(1)}M` : currencyFmt.format(ventas),
    segments,
  };
});

const margenesBreakdown = computed(() => {
  if (!lastPeriodData.value) return { total: "0%", segments: [] };

  const rentCrudos = lastPeriodData.value.rentabilidad?.datos_crudos || {};
  const rotCrudos = lastPeriodData.value.rotacion?.datos_crudos || {};
  const endCrudos = lastPeriodData.value.endeudamiento?.datos_crudos || {};

  const ventas = rentCrudos.ventas_netas || 1;
  const utilidad = rentCrudos.utilidad_neta || 0;

  let costoVentas = rotCrudos.costo_ventas || 0;
  if (costoVentas === 0 && ventas > 0 && endCrudos.utilidad_operacion) {
    costoVentas = ventas - endCrudos.utilidad_operacion;
  } else if (costoVentas === 0) {
    costoVentas = (ventas - utilidad) * 0.5;
  }

  let utilidadBruta = ventas - costoVentas;
  if (utilidadBruta < utilidad) utilidadBruta = utilidad * 1.5;

  const margenBruto = (utilidadBruta / ventas) * 100;
  const margenNeto = (utilidad / ventas) * 100;

  let merma = margenBruto - margenNeto;
  if (merma < 0) merma = 0;

  const items = [
    { label: "Gastos Operativos (Absorbidos)", value: merma, color: "#fb923c" },
    { label: "Margen Neto Final", value: margenNeto, color: "#fcd34d" },
  ].filter((i) => i.value > 0);

  const totalCalculo = items.reduce((acc, curr) => acc + curr.value, 0) || 1;

  let currentOffset = 0;
  const segments = items.map((item) => {
    const pct = (item.value / totalCalculo) * 100;
    const dashoffset = -currentOffset;
    currentOffset += pct;
    return {
      ...item,
      pct: pct.toFixed(1),
      dasharray: `${pct} 100`,
      dashoffset,
    };
  });

  return {
    total: `${margenBruto.toFixed(1)}%`,
    segments,
  };
});

onMounted(() => {
  loadAiResult();
  fetchDashboardData();
});
</script>

<template>
  <div class="wrap" v-if="!loading && metrics.length > 0">
    <div class="title">
      <div class="title-row">
        <h1>Rentabilidad</h1>
        <button class="btn-learn" type="button" @click="centroDeAprendizaje">
          <span class="material-symbols-outlined">info</span>
          <span>Ir a centro de aprendizaje</span>
        </button>
      </div>

      <div class="subtitle">
        <p>Evalúa la capacidad de la empresa para generar utilidades</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">Indicadores calculados a partir del Estado de Resultados</p>
      </div>
    </div>

    <section class="kpis">
      <button
        v-for="k in metrics"
        :key="k.key"
        type="button"
        class="kpi"
        :class="{ selected: activeKpi === k.key }"
        @click="setActive(k.key)"
      >
        <div class="kpi-top">
          <p class="kpi-label" :class="{ 'kpi-label-selected': activeKpi === k.key }">
            {{ k.label }}
          </p>
          <span class="kpi-dot" :class="k.status" aria-hidden="true"></span>
        </div>

        <div class="kpi-value">{{ k.kpiValue }}</div>

        <div class="kpi-delta">
          <span class="delta-pill" :class="k.deltaType === 'up' ? 'delta-up' : 'delta-down'">
            <span class="material-symbols-outlined">
              {{ k.deltaType === "up" ? "trending_up" : "trending_down" }}
            </span>
            {{ k.deltaValue }}
          </span>
          <span class="delta-note">{{ k.deltaNote }}</span>
        </div>
      </button>
    </section>

    <section class="panel" v-if="selectedKpi">
      <div class="panel-head">
        <div>
          <h3>{{ selectedKpi.chartTitle }}</h3>
          <p class="panel-sub">{{ selectedKpi.chartSubtitle }}</p>
        </div>

        <div class="legend">
          <div class="legend-item">
            <span class="legend-dot" aria-hidden="true"></span>
            <span>{{ selectedKpi.legendLabel }}</span>
          </div>
        </div>
      </div>

      <div class="chart">
        <svg class="chart-svg" fill="none" preserveAspectRatio="none" viewBox="0 0 800 300">
          <defs>
            <linearGradient id="gradient-rent" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#299de0" stop-opacity="0.15"></stop>
              <stop offset="100%" stop-color="#299de0" stop-opacity="0"></stop>
            </linearGradient>
          </defs>

          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

          <path :d="areaPath" fill="url(#gradient-rent)"></path>
          <path :d="linePath" fill="none" stroke="#299de0" stroke-linecap="round" stroke-width="3"></path>

          <circle
            v-for="(p, idx) in selectedKpi.points"
            :key="idx"
            :cx="p.x"
            :cy="p.y"
            fill="white"
            :r="hoveredPoint === p ? 6 : 5"
            stroke="#299de0"
            stroke-width="2.5"
            style="transition: r 0.2s ease;"
          ></circle>

          <circle
            v-for="(p, idx) in selectedKpi.points"
            :key="`hit-${idx}`"
            :cx="p.x"
            :cy="p.y"
            r="20"
            fill="transparent"
            style="cursor: pointer;"
            @mouseover="showTooltip(p)"
            @mouseleave="hideTooltip"
          ></circle>

          <g v-if="hoveredPoint" style="pointer-events: none;">
            <rect
              :x="hoveredPoint.x - 30"
              :y="hoveredPoint.y - 42"
              width="60"
              height="26"
              rx="6"
              fill="#0e161b"
              opacity="0.95"
            ></rect>
            <polygon
              :points="`${hoveredPoint.x - 6},${hoveredPoint.y - 16} ${hoveredPoint.x + 6},${hoveredPoint.y - 16} ${hoveredPoint.x},${hoveredPoint.y - 10}`"
              fill="#0e161b"
              opacity="0.95"
            ></polygon>
            <text
              :x="hoveredPoint.x"
              :y="hoveredPoint.y - 24"
              fill="#ffffff"
              font-size="12"
              font-weight="bold"
              font-family="Inter, sans-serif"
              text-anchor="middle"
            >
              {{ hoveredPoint.value.toFixed(1) }}%
            </text>
          </g>

          <text
            v-for="(p, idx) in selectedKpi.points"
            :key="`t-${idx}`"
            :x="p.x"
            y="260"
            text-anchor="middle"
            font-family="Inter, sans-serif"
            font-size="12"
            :font-weight="p.bold ? 'bold' : 'normal'"
            :fill="p.bold ? '#0e161b' : '#507c95'"
          >
            {{ p.label }}
          </text>

          <g>
            <text
              v-for="(lab, i) in selectedKpi.yAxisLabels"
              :key="`yl-${i}`"
              x="45"
              :y="55 + i * 60"
              text-anchor="end"
              fill="#507c95"
              font-family="Inter"
              font-size="11"
              font-weight="600"
            >
              {{ lab }}
            </text>
          </g>
        </svg>
      </div>
    </section>

    <section class="grid-2">
      <article class="card">
        <h3>Ingresos vs Costos vs Utilidad</h3>
        <p class="card-sub">Composición del resultado ({{ lastPeriodData?.label }})</p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle
                v-for="(seg, idx) in rentabilidadBreakdown.segments"
                :key="idx"
                cx="18" cy="18" fill="none" r="16"
                :stroke="seg.color"
                :stroke-dasharray="seg.dasharray"
                :stroke-dashoffset="seg.dashoffset"
                stroke-width="4"
                style="transition: stroke-dasharray 1s ease-out, stroke-dashoffset 1s ease-out;"
              ></circle>
            </svg>

            <div class="donut-center">
              <span class="donut-kicker">Ventas</span>
              <span class="donut-total">{{ rentabilidadBreakdown.total }}</span>
            </div>
          </div>
        </div>

        <div class="donut-legend-grid">
          <div
            class="donut-legend-row"
            v-for="(seg, idx) in rentabilidadBreakdown.segments"
            :key="`rent-leg-${idx}`"
          >
            <span class="legend-color" :style="{ background: seg.color }" aria-hidden="true"></span>
            <span class="truncate">{{ seg.label }} ({{ seg.pct }}%)</span>
          </div>
        </div>
      </article>

      <article class="card">
        <h3>Estructura del Margen Bruto</h3>
        <p class="card-sub">Relación entre la utilidad bruta y la utilidad final ({{ lastPeriodData?.label }})</p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle
                v-for="(seg, idx) in margenesBreakdown.segments"
                :key="idx"
                cx="18" cy="18" fill="none" r="16"
                :stroke="seg.color"
                :stroke-dasharray="seg.dasharray"
                :stroke-dashoffset="seg.dashoffset"
                stroke-width="4"
                style="transition: stroke-dasharray 1s ease-out, stroke-dashoffset 1s ease-out;"
              ></circle>
            </svg>

            <div class="donut-center">
              <span class="donut-kicker">M. Bruto</span>
              <span class="donut-total">{{ margenesBreakdown.total }}</span>
            </div>
          </div>
        </div>

        <div class="donut-legend-grid">
          <div
            class="donut-legend-row"
            v-for="(seg, idx) in margenesBreakdown.segments"
            :key="`marg-leg-${idx}`"
          >
            <span class="legend-color" :style="{ background: seg.color }" aria-hidden="true"></span>
            <span class="truncate">{{ seg.label }} ({{ seg.pct }}%)</span>
          </div>
        </div>
      </article>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h3>Comparativa por periodo</h3>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Periodo</th>
              <th class="right">Ingresos</th>
              <th class="right">Utilidad Neta</th>
              <th class="center" style="text-align: center;">Margen</th>
              <th class="center" style="text-align: center;">RAT</th>
              <th class="center" style="text-align: center;">ROE</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in tableRows" :key="r.period" :class="{ highlight: r.highlight }">
              <td class="strong" :class="{ primary: r.highlight }">{{ r.period }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.ingresos }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.utilidad }}</td>
              <td class="center" style="text-align: center;" :class="{ strong: r.highlight }">
                <span v-if="r.highlight" class="table-badge">{{ r.margen }}</span>
                <span v-else>{{ r.margen }}</span>
              </td>
              <td class="center" style="text-align: center;" :class="{ strong: r.highlight }">{{ r.rat }}</td>
              <td class="center" style="text-align: center;" :class="{ strong: r.highlight }">{{ r.roe }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid-2">
      <article class="note note-warn">
        <div class="note-bg" aria-hidden="true">
          <span class="material-symbols-outlined">warning</span>
        </div>

        <div class="note-mini">
          <span class="material-symbols-outlined">info</span>
          <span>Interpretación Automática</span>
        </div>

        <h3>Análisis de tendencia</h3>

        <p v-if="aiBlockLoading">
          Cargando interpretación automática...
        </p>

        <p v-else-if="aiBlockError">
          No se pudo cargar la interpretación automática. Se muestra una interpretación base.
        </p>

        <p v-else>
          {{ finalAnalysisText }}
        </p>

        <ul
          v-if="!aiBlockLoading && !aiBlockError && mainFindings.length"
          class="list findings-list"
        >
          <li v-for="(finding, idx) in mainFindings" :key="`finding-${idx}`">
            <span class="material-symbols-outlined">info</span>
            <span>{{ finding }}</span>
          </li>
        </ul>

        <div
          v-if="!aiBlockLoading && !aiBlockError && alertItems.length"
          class="ai-alerts"
        >
          <div
            v-for="(alert, idx) in alertItems"
            :key="`alert-${idx}`"
            class="ai-alert"
          >
            <strong>{{ alert.title }}</strong>
            <p>{{ alert.message }}</p>
            <small>{{ alert.evidence }}</small>
          </div>
        </div>
      </article>

      <article class="note note-ok">
        <div class="note-head">
          <span class="tag-green">
            <span class="material-symbols-outlined">rocket_launch</span>
          </span>
          <h3>Recomendaciones</h3>
        </div>

        <ul class="list">
          <li v-if="aiBlockLoading">
            <span class="material-symbols-outlined">hourglass_empty</span>
            <span>Cargando recomendaciones...</span>
          </li>

          <li v-else-if="aiBlockError">
            <span class="material-symbols-outlined">info</span>
            <span>No se pudieron cargar las recomendaciones automáticas.</span>
          </li>

          <template v-else-if="recommendationItems.length">
            <li v-for="(item, idx) in recommendationItems" :key="`ai-rec-${idx}`">
              <span class="material-symbols-outlined">check_circle</span>
              <span>
                <strong>{{ item.title }}:</strong> {{ item.description }}
              </span>
            </li>
          </template>

          <template v-else>
            <li v-for="(item, idx) in recommendationList" :key="`fallback-rec-${idx}`">
              <span class="material-symbols-outlined">check_circle</span>
              <span>{{ item }}</span>
            </li>
          </template>
        </ul>
      </article>
    </section>

    <footer class="foot">
      <p>
        Todos los datos son confidenciales.<br />
        Este reporte es para fines informativos y no constituye asesoramiento legal o fiscal.
      </p>
    </footer>
  </div>

  <div v-else-if="loading" style="padding: 40px; text-align: center; color: var(--muted);">
    Cargando análisis multiperiodo de rentabilidad...
  </div>
</template>

<style scoped>
.wrap {
  width: min(1200px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Title */
.title h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-learn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid #d1dee6;
  background: #ffffff;
  font-size: 12px;
  font-weight: 900;
  color: #0e161b;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.btn-learn:hover {
  background: #f8fafb;
}

.btn-learn .material-symbols-outlined {
  font-size: 18px;
}

.subtitle {
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #507c95;
  font-weight: 700;
  font-size: 13px;
}

.subtitle .small {
  font-size: 12px;
  font-weight: 700;
}

.dot {
  display: none;
  color: #d1d5db;
}

/* KPIs */
.kpis {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.kpi {
  width: 100%;
  text-align: left;
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.05s ease;
  cursor: pointer;
}

.kpi:hover {
  border-color: #b4d2e6;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.kpi:active {
  transform: translateY(1px);
}

.kpi.selected {
  border: 2px solid #299de0;
  background: #f0f8fd;
}

.kpi-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.kpi-label {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  font-weight: 800;
}

.kpi-label-selected {
  color: #299de0;
  font-weight: 900;
}

.kpi-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-top: 4px;
}

.kpi-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}

.kpi-dot.warn {
  background: #facc15;
  box-shadow: 0 0 8px rgba(250, 204, 21, 0.4);
}

.kpi-dot.alert {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

.kpi-dot.gray {
  background: #9ca3af;
}

.kpi-value {
  margin-top: 10px;
  font-size: 24px;
  font-weight: 900;
  color: #0e161b;
}

.kpi-delta {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.delta-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 900;
}

.delta-pill .material-symbols-outlined {
  font-size: 14px;
}

.delta-up {
  background: #dcfce7;
  color: #078836;
}

.delta-down {
  background: #fee2e2;
  color: #e73508;
}

.delta-note {
  color: #507c95;
  font-size: 12px;
  font-weight: 700;
}

/* Panels */
.panel {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.panel-head {
  padding: 14px 18px;
  border-bottom: 1px solid #e8eff3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.panel-sub {
  margin: 4px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.legend {
  display: flex;
  align-items: center;
  gap: 14px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  color: #0e161b;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: #299de0;
}

.chart {
  padding: 16px 18px 18px;
  position: relative;
}

.chart-svg {
  width: 100%;
  height: 280px;
  display: block;
}

/* Donut cards */
.card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.card-sub {
  margin: -6px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.donut-wrap {
  display: grid;
  place-items: center;
  padding: 10px 0;
}

.donut {
  position: relative;
  width: 160px;
  height: 160px;
}

.donut-svg {
  width: 100%;
  height: 100%;
}

.donut-center {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
}

.donut-kicker {
  font-size: 11px;
  font-weight: 900;
  color: #507c95;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.donut-total {
  font-size: 20px;
  font-weight: 900;
  color: #0e161b;
}

.donut-legend-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px 12px;
  margin-top: 8px;
}

.donut-legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.legend-color {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  flex: 0 0 auto;
}

.truncate {
  line-height: 1.3;
}

/* Table */
.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 900px;
}

.table thead th {
  text-align: left;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #507c95;
  background: #f8fafb;
  border-bottom: 1px solid #e8eff3;
  padding: 12px 16px;
  font-weight: 900;
}

.table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid #e8eff3;
  font-size: 13px;
  color: #0e161b;
}

.table tbody tr:hover {
  background: #f9fafb;
}

.table .right {
  text-align: right;
}

.strong {
  font-weight: 900;
}

.primary {
  color: #299de0;
}

.highlight {
  background: rgba(41, 157, 224, 0.08);
}

.table-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 5px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 900;
}

/* Notes */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.note {
  position: relative;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.note-warn {
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 70%);
  border: 1px solid #dbeafe;
}

.note-ok {
  background: #ffffff;
  border: 1px solid #e8eff3;
}

.note-bg {
  position: absolute;
  right: 10px;
  top: 6px;
  opacity: 0.06;
}

.note-bg .material-symbols-outlined {
  font-size: 100px;
  color: #299de0;
}

.note-mini {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #299de0;
}

.note-mini .material-symbols-outlined {
  font-size: 18px;
}

.note h3 {
  margin: 10px 0 10px;
  font-size: 18px;
  font-weight: 900;
  color: #0e161b;
}

.note p {
  margin: 0;
  color: #0e161b;
  font-weight: 700;
  font-size: 14px;
  line-height: 1.55;
  position: relative;
  z-index: 1;
}

.note-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tag-green {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #dcfce7;
  color: #15803d;
  display: grid;
  place-items: center;
}

.tag-green .material-symbols-outlined {
  font-size: 20px;
}

.list {
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 12px;
}

.findings-list {
  margin-top: 14px;
}

.list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: #0e161b;
  font-weight: 800;
  font-size: 13px;
}

.list .material-symbols-outlined {
  color: #299de0;
  font-size: 18px;
  margin-top: 2px;
}

.ai-alerts {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.ai-alert {
  border: 1px solid #fee2e2;
  background: #fff7f7;
  border-radius: 12px;
  padding: 12px;
  position: relative;
  z-index: 1;
}

.ai-alert strong {
  display: block;
  color: #991b1b;
  font-size: 13px;
  font-weight: 900;
  margin-bottom: 4px;
}

.ai-alert p {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
}

.ai-alert small {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
}

/* Footer */
.foot {
  margin: 8px 0 22px;
  text-align: center;
  color: #9ca3af;
  font-weight: 700;
  font-size: 12px;
}

.foot p {
  margin: 0;
}

/* Responsive */
@media (min-width: 640px) {
  .subtitle {
    flex-direction: row;
    align-items: baseline;
    gap: 10px;
  }

  .dot {
    display: inline;
  }

  .kpis {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 900px) {
  .kpis {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>