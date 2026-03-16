<script setup>
import { computed, ref } from "vue";

/**
 * UI demo: puedes conectar estos valores a Firestore después.
 * Lo importante aquí: selectedMetric controla qué gráfica se muestra.
 */

const metrics = [
  {
    key: "margen",
    kpiTitle: "Margen de Rentabilidad",
    kpiValue: "12.8%",
    status: "ok",
    deltaType: "up",
    deltaValue: "+0.5%",
    deltaText: "vs periodo base",

    chartTitle: "Evolución de Margen de Rentabilidad",
    chartSubtitle: "Tendencia histórica de Margen de Rentabilidad por trimestre",
    legendLabel: "Margen de Rentabilidad (%)",
    yAxisLabels: ["20%", "15%", "10%", "5%"],

    // puntos del SVG (x fijo, y cambia por métrica)
    points: [
      { x: 50, y: 200, label: "Q3 '23" },
      { x: 225, y: 190, label: "Q4 '23" },
      { x: 400, y: 170, label: "Q1 '24" },
      { x: 575, y: 185, label: "Q2 '24" },
      { x: 750, y: 160, label: "Q3 '24", bold: true },
    ],
  },
  {
    key: "rat",
    kpiTitle: "Rendimiento sobre Activos Totales (RAT)",
    kpiValue: "15.4%",
    status: "ok",
    deltaType: "up",
    deltaValue: "+1.2%",
    deltaText: "vs periodo base",

    chartTitle: "Evolución de RAT",
    chartSubtitle: "Tendencia histórica de RAT por trimestre",
    legendLabel: "RAT (%)",
    yAxisLabels: ["20%", "15%", "10%", "5%"],

    points: [
      { x: 50, y: 210, label: "Q3 '23" },
      { x: 225, y: 195, label: "Q4 '23" },
      { x: 400, y: 180, label: "Q1 '24" },
      { x: 575, y: 165, label: "Q2 '24" },
      { x: 750, y: 150, label: "Q3 '24", bold: true },
    ],
  },
  {
    key: "roe",
    kpiTitle: "Rendimiento sobre el Patrimonio",
    kpiValue: "21.0%",
    status: "warn",
    deltaType: "down",
    deltaValue: "-0.8%",
    deltaText: "vs periodo base",

    chartTitle: "Evolución de ROE",
    chartSubtitle: "Tendencia histórica de ROE por trimestre",
    legendLabel: "ROE (%)",
    yAxisLabels: ["30%", "25%", "20%", "15%"],

    points: [
      { x: 50, y: 160, label: "Q3 '23" },
      { x: 225, y: 150, label: "Q4 '23" },
      { x: 400, y: 165, label: "Q1 '24" },
      { x: 575, y: 155, label: "Q2 '24" },
      { x: 750, y: 170, label: "Q3 '24", bold: true },
    ],
  },
];

const selectedMetric = ref("margen");

const activeMetric = computed(
  () => metrics.find((m) => m.key === selectedMetric.value) || metrics[0]
);

function selectMetric(key) {
  selectedMetric.value = key;
}

// helpers SVG
const baselineY = 230;

const linePath = computed(() => {
  const pts = activeMetric.value.points;
  if (!pts.length) return "";
  return pts
    .map((p, i) => (i === 0 ? `M${p.x} ${p.y}` : `L${p.x} ${p.y}`))
    .join(" ");
});

const areaPath = computed(() => {
  const pts = activeMetric.value.points;
  if (!pts.length) return "";
  const first = pts[0];
  const last = pts[pts.length - 1];
  const mid = pts.map((p) => `L${p.x} ${p.y}`).join(" ");
  return `M${first.x} ${baselineY} L${first.x} ${first.y} ${mid} L${last.x} ${baselineY} Z`;
});
</script>

<template>
  <main class="main">
    <div class="container">
      <!-- Título -->
      <section class="title">
        <div class="title-row">
          <h1>Rentabilidad</h1>

          <router-link to="/teoriaRentabilidad" target="_blank" class="btn-info">
            <span class="material-symbols-outlined">info</span>
            <span>Saber más</span>
          </router-link>
        </div>

        <div class="subtitle">
          <p class="subtitle-main">Evalúa la capacidad de la empresa para generar utilidades</p>
          <span class="dot">•</span>
          <p class="subtitle-secondary">Indicadores calculados a partir del Estado de Resultados</p>
        </div>
      </section>

      <!-- KPIs (clic cambia gráfica) -->
      <section class="kpis">
        <button
          v-for="m in metrics"
          :key="m.key"
          type="button"
          class="kpi"
          :class="{ active: selectedMetric === m.key }"
          @click="selectMetric(m.key)"
        >
          <div class="kpi-top">
            <p class="kpi-title" :class="{ activeTitle: selectedMetric === m.key }">
              {{ m.kpiTitle }}
            </p>

            <span class="status-dot" :class="m.status" aria-hidden="true"></span>
          </div>

          <div class="kpi-value">{{ m.kpiValue }}</div>

          <div class="kpi-delta">
            <span class="chip" :class="m.deltaType === 'up' ? 'chip-up' : 'chip-down'">
              <span class="material-symbols-outlined">
                {{ m.deltaType === "up" ? "trending_up" : "trending_down" }}
              </span>
              {{ m.deltaValue }}
            </span>

            <span class="kpi-delta-text">{{ m.deltaText }}</span>
          </div>
        </button>
      </section>

      <!-- Gráfica (dinámica) -->
      <section class="card">
        <div class="card-head">
          <div>
            <h3>{{ activeMetric.chartTitle }}</h3>
            <p>{{ activeMetric.chartSubtitle }}</p>
          </div>

          <div class="legend">
            <div class="legend-item">
              <span class="legend-dot legend-primary"></span>
              <span>{{ activeMetric.legendLabel }}</span>
            </div>
          </div>
        </div>

        <div class="chart">
          <svg class="chart-svg" fill="none" preserveAspectRatio="none" viewBox="0 0 800 300">
            <defs>
              <linearGradient id="gradientMetric" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#299de0" stop-opacity="0.15"></stop>
                <stop offset="100%" stop-color="#299de0" stop-opacity="0"></stop>
              </linearGradient>
            </defs>

            <!-- grid -->
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

            <!-- area + line -->
            <path :d="areaPath" fill="url(#gradientMetric)"></path>
            <path
              :d="linePath"
              fill="none"
              stroke="#299de0"
              stroke-linecap="round"
              stroke-width="3"
            ></path>

            <!-- points -->
            <circle
              v-for="(p, idx) in activeMetric.points"
              :key="idx"
              :cx="p.x"
              :cy="p.y"
              fill="white"
              r="4"
              stroke="#299de0"
              stroke-width="2"
            ></circle>

            <!-- x labels -->
            <text
              v-for="(p, idx) in activeMetric.points"
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
          </svg>

          <div class="chart-y">
            <span v-for="(lab, i) in activeMetric.yAxisLabels" :key="i">{{ lab }}</span>
          </div>
        </div>
      </section>

      <!-- Tabla (por ahora estática como tu HTML) -->
      <section class="table-card">
        <div class="table-head">
          <h3>Comparativo por Periodo</h3>
        </div>

        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>Periodo</th>
                <th>Ingresos</th>
                <th>Utilidad Neta</th>
                <th>Margen Neto</th>
                <th class="right">Var. Trimestral</th>
              </tr>
            </thead>

            <tbody>
              <tr>
                <td class="strong">Q3 2024</td>
                <td class="muted">$4,250,000</td>
                <td class="muted">$845,000</td>
                <td><span class="badge badge-blue">19.8%</span></td>
                <td class="right up">+5.2%</td>
              </tr>

              <tr>
                <td class="strong">Q2 2024</td>
                <td class="muted">$3,820,000</td>
                <td class="muted">$802,000</td>
                <td><span class="badge badge-gray">21.0%</span></td>
                <td class="right up">+2.8%</td>
              </tr>

              <tr>
                <td class="strong">Q1 2024</td>
                <td class="muted">$3,500,000</td>
                <td class="muted">$715,000</td>
                <td><span class="badge badge-gray">20.4%</span></td>
                <td class="right down">-1.2%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Interpretación + recomendaciones -->
      <section class="blocks">
        <article class="block block-info">
          <div class="block-bg-icon" aria-hidden="true">
            <span class="material-symbols-outlined">warning</span>
          </div>

          <div class="block-body">
            <div class="block-title">
              <div class="block-icon block-icon-blue">
                <span class="material-symbols-outlined">insights</span>
              </div>
              <h3>Interpretación y alertas</h3>
            </div>

            <p>
              La empresa presenta una mejora sostenida en el margen operativo, aunque el margen neto se ve afectado
              por costos financieros elevados.
            </p>
          </div>
        </article>

        <article class="block block-reco">
          <div class="block-title">
            <div class="block-icon block-icon-green">
              <span class="material-symbols-outlined">checklist</span>
            </div>
            <h3>Recomendaciones</h3>
          </div>

          <ul class="reco-list">
            <li>
              <span class="material-symbols-outlined">check_circle</span>
              <span>Control de costos operativos</span>
            </li>
            <li>
              <span class="material-symbols-outlined">check_circle</span>
              <span>Revisión de estrategia de precios</span>
            </li>
            <li>
              <span class="material-symbols-outlined">check_circle</span>
              <span>Optimización de procesos internos</span>
            </li>
          </ul>
        </article>
      </section>

      <footer class="footer">
        <p>
          Todos los datos son confidenciales. <br />
          Este reporte es para fines informativos y no constituye asesoramiento legal o fiscal.
        </p>
      </footer>
    </div>
  </main>
</template>

<style scoped>
.main {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f8fafb;
}

.container {
  width: min(1200px, 92vw);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ===== Title ===== */
.title {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-row h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 900;
  color: #0e161b;
}

.btn-info {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid #d1dee6;
  background: white;
  color: #0e161b;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.btn-info:hover {
  border-color: #299de0;
  color: #299de0;
}

.btn-info .material-symbols-outlined {
  font-size: 18px;
}

.subtitle {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subtitle-main {
  margin: 0;
  color: #507c95;
  font-size: 14px;
  font-weight: 700;
}

.subtitle-secondary {
  margin: 0;
  color: #507c95;
  font-size: 12px;
}

.dot {
  display: none;
  color: #d1d5db;
}

@media (min-width: 640px) {
  .subtitle {
    flex-direction: row;
    align-items: baseline;
    gap: 10px;
  }
  .dot {
    display: inline;
  }
}

/* ===== KPIs ===== */
.kpis {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

@media (min-width: 768px) {
  .kpis {
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
  }
}

.kpi {
  text-align: left;
  border-radius: 14px;
  border: 1px solid #e8eff3;
  background: white;
  padding: 18px;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: box-shadow 0.15s ease, border-color 0.15s ease, transform 0.05s ease;
}

.kpi:hover {
  border-color: rgba(41, 157, 224, 0.5);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.06);
}

.kpi:active {
  transform: translateY(1px);
}

.kpi.active {
  border: 2px solid #299de0;
  background: rgba(41, 157, 224, 0.12);
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.08);
}

.kpi-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.kpi-title {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: #507c95;
}

.kpi-title.activeTitle {
  color: #299de0;
  font-weight: 900;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-top: 2px;
}

.status-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}

.status-dot.warn {
  background: #facc15;
  box-shadow: 0 0 8px rgba(250, 204, 21, 0.4);
}

.kpi-value {
  margin-top: 6px;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
}

.kpi-delta {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 900;
}

.chip .material-symbols-outlined {
  font-size: 14px;
}

.chip-up {
  background: #dcfce7;
  color: #078836;
}

.chip-down {
  background: #fee2e2;
  color: #e73508;
}

.kpi-delta-text {
  font-size: 12px;
  color: #507c95;
}

/* ===== Card (Chart) ===== */
.card {
  border: 1px solid #e8eff3;
  background: white;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.04);
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
}

.card-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.card-head p {
  margin: 6px 0 0;
  font-size: 12px;
  color: #507c95;
}

.legend {
  display: flex;
  align-items: center;
  gap: 12px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #0e161b;
  font-weight: 700;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
}

.legend-primary {
  background: #299de0;
}

.chart {
  position: relative;
  margin-top: 12px;
  height: 300px;
}

.chart-svg {
  width: 100%;
  height: 100%;
}

.chart-y {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 32px;
  width: 42px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #507c95;
  font-size: 12px;
  font-weight: 700;
  text-align: right;
  padding-right: 10px;
}

/* ===== Table ===== */
.table-card {
  border: 1px solid #e8eff3;
  background: white;
  border-radius: 14px;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.table-head {
  padding: 14px 18px;
  border-bottom: 1px solid #e8eff3;
}

.table-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.table thead th {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 11px;
  color: #507c95;
  background: #f8fafb;
  border-bottom: 1px solid #e8eff3;
  padding: 12px 18px;
  text-align: left;
  font-weight: 900;
}

.table tbody td {
  padding: 12px 18px;
  border-bottom: 1px solid #e8eff3;
  color: #0e161b;
}

.table tbody tr:hover {
  background: #fafafa;
}

.right {
  text-align: right;
}

.strong {
  font-weight: 900;
}

.muted {
  color: #507c95;
  font-weight: 700;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 900;
  padding: 5px 8px;
  border-radius: 8px;
}

.badge-blue {
  background: #eff6ff;
  color: #1d4ed8;
}

.badge-gray {
  background: #f3f4f6;
  color: #374151;
}

.up {
  color: #16a34a;
  font-weight: 900;
}

.down {
  color: #ef4444;
  font-weight: 900;
}

/* ===== Blocks ===== */
.blocks {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

@media (min-width: 1024px) {
  .blocks {
    grid-template-columns: 1fr 1fr;
  }
}

.block {
  border-radius: 14px;
  border: 1px solid #dbeafe;
  background: linear-gradient(135deg, #eff6ff, #ffffff);
  padding: 18px;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.04);
  position: relative;
  overflow: hidden;
}

.block-info .block-bg-icon {
  position: absolute;
  top: 0;
  right: 0;
  padding: 14px;
  opacity: 0.1;
}

.block-bg-icon .material-symbols-outlined {
  font-size: 120px;
  color: #299de0;
}

.block-body {
  position: relative;
  z-index: 1;
}

.block-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.block-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.block-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
}

.block-icon .material-symbols-outlined {
  font-size: 20px;
}

.block-icon-blue {
  background: #dbeafe;
  color: #299de0;
}

.block-icon-green {
  background: #dcfce7;
  color: #15803d;
}

.block p {
  margin: 0;
  color: #0e161b;
  line-height: 1.6;
  font-size: 13px;
}

/* ===== Reco list ===== */
.reco-list {
  list-style: none;
  padding: 0;
  margin: 12px 0 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reco-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: #0e161b;
  font-size: 13px;
  font-weight: 700;
}

.reco-list .material-symbols-outlined {
  color: #299de0;
  font-size: 18px;
  margin-top: 2px;
}

/* ===== Footer ===== */
.footer {
  margin: 16px 0 6px;
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
}

.footer p {
  margin: 0;
}
</style>