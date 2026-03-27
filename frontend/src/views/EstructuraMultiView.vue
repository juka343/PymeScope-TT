<script setup>
import { computed, ref } from "vue";

const activeKpi = ref("solvencia");
const hoveredPoint = ref(null);

const currencyFmt = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const periods = ["Q3 '23", "Q4 '23", "Q1 '24", "Q2 '24", "Q3 '24"];

function buildChart(values, title, subtitle, legendLabel) {
  const maxVal = Math.max(...values, 1);
  let minVal = Math.min(...values, 0);

  if (minVal > 0) minVal = 0;

  const rawRange = maxVal - minVal;
  let step = 0.2;
  if (rawRange > 1.2) step = 0.5;
  if (rawRange > 3) step = 1;

  const yMin = Math.floor(minVal / step) * step;
  const yMax = Math.ceil(maxVal / step) * step;
  const finalRange = Math.max(yMax - yMin, step);

  const yAxisLabels = [
    yMax.toFixed(2),
    (yMax - finalRange / 3).toFixed(2),
    (yMax - (finalRange / 3) * 2).toFixed(2),
    yMin.toFixed(2),
  ];

  const xStep = values.length > 1 ? 700 / (values.length - 1) : 0;

  const points = values.map((val, i) => {
    const x = values.length > 1 ? 50 + i * xStep : 400;
    const y = 230 - ((val - yMin) / finalRange) * 160;
    return {
      x,
      y,
      label: periods[i],
      bold: i === values.length - 1,
      value: val,
    };
  });

  return {
    chartTitle: title,
    chartSubtitle: subtitle,
    legendLabel,
    yAxisLabels,
    points,
  };
}

const metrics = ref([
  {
    key: "solvencia",
    label: "Solvencia",
    kpiValue: "2.15",
    status: "ok",
    deltaType: "up",
    deltaValue: "+5%",
    deltaNote: "vs periodo base",
    ...buildChart(
      [1.72, 1.86, 1.96, 2.04, 2.15],
      "Evolución de Solvencia",
      "Análisis histórico del índice de solvencia",
      "Solvencia"
    ),
  },
  {
    key: "seguridad",
    label: "Seguridad a largo plazo",
    kpiValue: "1.84",
    status: "ok",
    deltaType: "up",
    deltaValue: "+2%",
    deltaNote: "vs periodo base",
    ...buildChart(
      [1.60, 1.68, 1.75, 1.80, 1.84],
      "Evolución de Seguridad a Largo Plazo",
      "Respaldo financiero para obligaciones de largo plazo",
      "Seguridad LP"
    ),
  },
  {
    key: "inmovSocial",
    label: "Inmov. cap. social",
    kpiValue: "0.92",
    status: "warn",
    deltaType: "flat",
    deltaValue: "0%",
    deltaNote: "vs periodo base",
    ...buildChart(
      [0.88, 0.90, 0.91, 0.92, 0.92],
      "Evolución de Inmovilización del Capital Social",
      "Proporción del capital social comprometida en activos fijos",
      "Inmov. Cap. Social"
    ),
  },
  {
    key: "inmovContable",
    label: "Inmov. cap. contable",
    kpiValue: "1.15",
    status: "danger",
    deltaType: "down",
    deltaValue: "+8%",
    deltaNote: "vs periodo base",
    ...buildChart(
      [0.94, 0.98, 1.05, 1.10, 1.15],
      "Evolución de Inmovilización del Capital Contable",
      "Proporción del capital contable comprometida en activos fijos",
      "Inmov. Cap. Contable"
    ),
  },
]);

const selectedKpi = computed(() => {
  return metrics.value.find((m) => m.key === activeKpi.value) || metrics.value[0];
});

function setActive(key) {
  activeKpi.value = key;
}

function showTooltip(point) {
  hoveredPoint.value = point;
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

const capitalContable = computed(() => ({
  total: "$4.7M",
  segments: [
    { label: "Capital Social", pct: "65", color: "#1e293b", dasharray: "65 100", dashoffset: 0 },
    { label: "Capital Ganado", pct: "35", color: "#299de0", dasharray: "35 100", dashoffset: -65 },
  ],
}));

const distribucionActivo = computed(() => ({
  total: "$8.9M",
  segments: [
    { label: "Activo Fijo Neto", pct: "60", color: "#fb923c", dasharray: "60 100", dashoffset: 0 },
    { label: "Activo Circulante", pct: "40", color: "#fcd34d", dasharray: "40 100", dashoffset: -60 },
  ],
}));

const tableRows = ref([
  {
    period: "Q1 '24",
    activoTotal: currencyFmt.format(8840000),
    pasivoTotal: currencyFmt.format(4500000),
    solvencia: "1.96",
    seguridad: "1.75",
    inmovContable: "1.05",
    highlight: false,
  },
  {
    period: "Q2 '24",
    activoTotal: currencyFmt.format(8890000),
    pasivoTotal: currencyFmt.format(4350000),
    solvencia: "2.04",
    seguridad: "1.80",
    inmovContable: "1.10",
    highlight: false,
  },
  {
    period: "Q3 '24",
    activoTotal: currencyFmt.format(8900000),
    pasivoTotal: currencyFmt.format(4140000),
    solvencia: "2.15",
    seguridad: "1.84",
    inmovContable: "1.15",
    highlight: true,
  },
]);

const analysisText = computed(() => {
  if (!selectedKpi.value) return "";

  if (selectedKpi.value.key === "solvencia") {
    return "La solvencia presenta una mejora sostenida y se ubica en niveles saludables. La empresa muestra capacidad suficiente para respaldar sus obligaciones totales con su estructura de activos.";
  }

  if (selectedKpi.value.key === "seguridad") {
    return "La seguridad a largo plazo mantiene una trayectoria favorable. Esto sugiere una base patrimonial razonablemente sólida para sostener compromisos de mayor plazo.";
  }

  if (selectedKpi.value.key === "inmovSocial") {
    return "La inmovilización del capital social se mantiene estable. Aunque no es una señal crítica, conviene vigilar que el capital aportado no quede excesivamente atrapado en activos con poca liquidez.";
  }

  return "La estructura financiera muestra una tendencia hacia la consolidación, con ratios de solvencia y seguridad a largo plazo en niveles saludables. Sin embargo, el índice de inmovilización del capital contable ha superado el umbral recomendable, lo que sugiere que una proporción elevada de los recursos propios está comprometida en activos fijos.";
});

const recommendationList = computed(() => {
  if (!selectedKpi.value) return [];

  if (selectedKpi.value.key === "solvencia") {
    return [
      "Mantener la disciplina financiera que ha fortalecido la capacidad de respaldo de activos.",
      "Evitar incrementos abruptos en pasivos sin crecimiento proporcional del activo útil.",
      "Monitorear periódicamente la solvencia frente a metas internas del proyecto.",
    ];
  }

  if (selectedKpi.value.key === "seguridad") {
    return [
      "Mantener la política de fortalecimiento patrimonial.",
      "Conservar una mezcla sana entre financiamiento propio y ajeno a largo plazo.",
      "Evaluar el costo de capital antes de asumir nuevas obligaciones de largo plazo.",
    ];
  }

  if (selectedKpi.value.key === "inmovSocial") {
    return [
      "Revisar si el capital social está financiando activos poco líquidos o poco rentables.",
      "Buscar una mejor proporción entre recursos fijos y recursos operativos.",
      "Evitar inmovilizar aportaciones de socios en activos sin impacto productivo claro.",
    ];
  }

  return [
    "Evaluar la desinversión de activos fijos no productivos para mejorar la liquidez del capital contable.",
    "Mantener la política de retención de utilidades para fortalecer la base de capital propio.",
    "Explorar opciones de financiamiento a largo plazo con tasas preferenciales para optimizar el costo de capital.",
  ];
});

function learnMore() {
  // placeholder
}
</script>

<template>
  <div class="wrap">
    <div class="title">
      <div class="title-row">
        <h1>Estructura Financiera</h1>
        <button class="btn-learn" type="button" @click="learnMore">
          <span class="material-symbols-outlined">info</span>
          <span>Ir a centro de aprendizaje</span>
        </button>
      </div>

      <div class="subtitle">
        <p>Composición del capital y estabilidad financiera de la empresa</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">Indicadores calculados a partir del Balance General</p>
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
          <span
            class="kpi-dot"
            :class="{
              ok: k.status === 'ok',
              warn: k.status === 'warn',
              danger: k.status === 'danger'
            }"
            aria-hidden="true"
          ></span>
        </div>

        <div class="kpi-value">{{ k.kpiValue }}</div>

        <div class="kpi-delta">
          <span
            class="delta-pill"
            :class="{
              'delta-up': k.deltaType === 'up',
              'delta-down': k.deltaType === 'down',
              'delta-flat': k.deltaType === 'flat'
            }"
          >
            <span class="material-symbols-outlined">
              {{
                k.deltaType === "up"
                  ? "trending_up"
                  : k.deltaType === "down"
                  ? "trending_down"
                  : "remove"
              }}
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
            <linearGradient id="gradient-ef" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#299de0" stop-opacity="0.15"></stop>
              <stop offset="100%" stop-color="#299de0" stop-opacity="0"></stop>
            </linearGradient>
          </defs>

          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

          <path :d="areaPath" fill="url(#gradient-ef)"></path>
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
              :x="hoveredPoint.x - 34"
              :y="hoveredPoint.y - 42"
              width="68"
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
              {{ hoveredPoint.value.toFixed(2) }}
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
        <h3>Composición del Capital Contable</h3>
        <p class="card-sub">
          Desglose del capital aportado por socios y las utilidades acumuladas por la empresa.
        </p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle
                v-for="(seg, idx) in capitalContable.segments"
                :key="idx"
                cx="18"
                cy="18"
                fill="none"
                r="16"
                :stroke="seg.color"
                :stroke-dasharray="seg.dasharray"
                :stroke-dashoffset="seg.dashoffset"
                stroke-width="4"
              ></circle>
            </svg>
            <div class="donut-center">
              <span class="donut-kicker two-line">Capital<br />Contable</span>
              <span class="donut-total">{{ capitalContable.total }}</span>
            </div>
          </div>
        </div>

        <div class="legend-grid">
          <div class="legend-row" v-for="(seg, idx) in capitalContable.segments" :key="`leg-c-${idx}`">
            <span class="dot" :style="{ background: seg.color }" aria-hidden="true"></span>
            <span class="truncate">{{ seg.label }} ({{ seg.pct }}%)</span>
          </div>
        </div>
      </article>

      <article class="card">
        <h3>Distribución del Activo Total</h3>
        <p class="card-sub">
          Proporción entre activos fijos y activos circulantes para medir la inmovilización de recursos.
        </p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle
                v-for="(seg, idx) in distribucionActivo.segments"
                :key="idx"
                cx="18"
                cy="18"
                fill="none"
                r="16"
                :stroke="seg.color"
                :stroke-dasharray="seg.dasharray"
                :stroke-dashoffset="seg.dashoffset"
                stroke-width="4"
              ></circle>
            </svg>
            <div class="donut-center">
              <span class="donut-kicker two-line">Activo<br />Total</span>
              <span class="donut-total">{{ distribucionActivo.total }}</span>
            </div>
          </div>
        </div>

        <div class="legend-grid">
          <div class="legend-row" v-for="(seg, idx) in distribucionActivo.segments" :key="`leg-a-${idx}`">
            <span class="dot" :style="{ background: seg.color }" aria-hidden="true"></span>
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
              <th class="right">Activo Total</th>
              <th class="right">Pasivo Total</th>
              <th class="right">Solvencia</th>
              <th class="right">Seguridad LP</th>
              <th class="right">Inmov. Cap. Contable</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in tableRows" :key="r.period" :class="{ highlight: r.highlight }">
              <td class="strong" :class="{ primary: r.highlight }">{{ r.period }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.activoTotal }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.pasivoTotal }}</td>
              <td class="right" :class="{ strong: r.highlight }">
                <span v-if="r.highlight" class="table-badge">{{ r.solvencia }}</span>
                <span v-else>{{ r.solvencia }}</span>
              </td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.seguridad }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.inmovContable }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid-2">
      <article class="note note-warn">
        <div class="note-bg" aria-hidden="true">
          <span class="material-symbols-outlined">account_balance</span>
        </div>

        <div class="note-mini">
          <span class="material-symbols-outlined">info</span>
          <span>Interpretación del Sistema</span>
        </div>

        <h3>Interpretación y alertas</h3>
        <p>{{ analysisText }}</p>
      </article>

      <article class="note note-ok">
        <div class="note-head">
          <span class="tag-green">
            <span class="material-symbols-outlined">shield</span>
          </span>
          <h3>Recomendaciones</h3>
        </div>

        <ul class="list">
          <li v-for="(item, idx) in recommendationList" :key="idx">
            <span class="material-symbols-outlined">check_circle</span>
            <span>{{ item }}</span>
          </li>
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
</template>

<style scoped>
.truncate {
  line-height: 1.3;
}

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
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
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
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.05s ease;
  cursor: pointer;
}

.kpi:hover {
  border-color: #b4d2e6;
  box-shadow: 0 8px 20px rgba(0,0,0,0.06);
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
  flex-shrink: 0;
}

.kpi-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34,197,94,0.4);
}

.kpi-dot.warn {
  background: #facc15;
  box-shadow: 0 0 8px rgba(250,204,21,0.4);
}

.kpi-dot.danger {
  background: #e11d48;
  box-shadow: 0 0 8px rgba(225,29,72,0.35);
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
  flex-wrap: wrap;
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

.delta-flat {
  background: #f3f4f6;
  color: #6b7280;
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
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
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
.grid-2 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

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
  line-height: 1.5;
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
  padding: 0 14px;
}

.donut-kicker {
  font-size: 11px;
  font-weight: 900;
  color: #507c95;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.donut-kicker.two-line {
  font-size: 10px;
  line-height: 1.2;
}

.donut-total {
  font-size: 20px;
  font-weight: 900;
  color: #0e161b;
}

.legend-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px 12px;
  margin-top: 8px;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  flex-shrink: 0;
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
.note {
  position: relative;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
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
  opacity: 0.05;
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
  flex-shrink: 0;
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
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>