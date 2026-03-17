<script setup>
import { computed, ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { collection, getDocs } from "firebase/firestore";
import { db } from "@/firebase/config";

const route = useRoute();
const projectId = route.params.id_proyecto;

const loading = ref(true);  
const rawPeriods = ref([]);
const metrics = ref([]);
const selectedMetric = ref("margen");
const hoveredPoint = ref(null);
function showTooltip(p) { hoveredPoint.value = p; }
function hideTooltip() { hoveredPoint.value = null; }const tableData = ref([]);

// Formateadores
const currencyFmt = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pctFmt = new Intl.NumberFormat('es-MX', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 });

// Carga de datos
const fetchPeriods = async () => {
  try {
    if (!projectId) return;

    const periodosRef = collection(db, "proyectos", projectId, "periodos");
    const snapshot = await getDocs(periodosRef);

    let loaded = [];
    snapshot.forEach((docSnap) => {
      const d = docSnap.data();
      if (d.rentabilidad || d.analisis_rentabilidad) {
        loaded.push({
          id: docSnap.id,
          label: d.label || "Periodo",
          periodDate: d.periodDate || "", // Asumiendo que ya añadiste esto en Carga de Documentos
          rentabilidad: d.rentabilidad || d.analisis_rentabilidad || { datos_crudos: {}, kpis: [] },
        });
      }
    });

    // Ordenamiento cronológico
    loaded.sort((a, b) => {
      const dateA = a.periodDate || a.label;
      const dateB = b.periodDate || b.label;
      return dateA.localeCompare(dateB);
    });

    rawPeriods.value = loaded;
    
    if (loaded.length > 0) {
      generateDashboardData();
    }
  } catch (error) {
    console.error("Error cargando multiperiodo:", error);
  } finally {
    loading.value = false;
  }
};

// Generador de métricas dinámicas
const generateDashboardData = () => {
  const periods = rawPeriods.value;
  const labels = periods.map(p => p.label);

  // 1. Helpers de extracción
  const parsePct = (val) => {
    if (!val) return 0;
    if (typeof val === 'number') return val;
    return parseFloat(val.toString().replace(/[^0-9.-]/g, ''));
  };

  const findKpi = (kpis, keyword) => {
    if (!kpis) return 0;
    const item = kpis.find(k => k.label.toLowerCase().includes(keyword.toLowerCase()));
    return item ? parsePct(item.value) : 0;
  };

  // 2. Extraer series de datos
  const dataMargen = periods.map(p => findKpi(p.rentabilidad.kpis, "Margen"));
  const dataRat = periods.map(p => findKpi(p.rentabilidad.kpis, "Activos"));
  const dataRoe = periods.map(p => findKpi(p.rentabilidad.kpis, "Patrimonio"));

  // 3. Helper para generar la gráfica
  // 3. Helper para generar la gráfica (Mejorado con números redondos)
  const buildChart = (values, title, subtitle, legendLabel) => {
    const maxVal = Math.max(...values, 5); 
    let minVal = Math.min(...values, 0); 
    if (minVal > 0) minVal = 0; 

    // Calculamos un "paso" redondo (5, 10, 20 o 50) dependiendo de qué tan grandes son los números
    const rawRange = maxVal - minVal;
    let step = 5;
    if (rawRange > 15) step = 10;
    if (rawRange > 40) step = 20;
    if (rawRange > 100) step = 50;

    const yMin = Math.floor(minVal / step) * step;
    const yMax = Math.ceil(maxVal / step) * step;
    const finalRange = yMax - yMin;

    // Forzamos 4 etiquetas redondeadas
    const yAxisLabels = [
      `${yMax}%`,
      `${Math.round(yMax - (finalRange / 3))}%`,
      `${Math.round(yMax - (finalRange / 3) * 2)}%`,
      `${yMin}%`
    ];

    const xStep = periods.length > 1 ? 560 / (periods.length - 1) : 0;    
    const points = values.map((val, i) => {
      const x = periods.length > 1 ? 120 + i * xStep : 400; 
      const y = 230 - ((val - yMin) / finalRange) * 180;
      return { x, y, label: labels[i], bold: i === values.length - 1, value: val };
    });

    const lastVal = values[values.length - 1];
    const prevVal = values.length > 1 ? values[values.length - 2] : lastVal;
    const delta = lastVal - prevVal;
    
    return {
      kpiValue: `${lastVal.toFixed(1)}%`,
      status: lastVal >= 10 ? "ok" : "warn",
      deltaType: delta >= 0 ? "up" : "down",
      deltaValue: `${delta > 0 ? '+' : ''}${delta.toFixed(1)}%`,
      deltaText: periods.length > 1 ? `vs ${labels[labels.length - 2]}` : "Sin periodo previo",
      chartTitle: title,
      chartSubtitle: subtitle,
      legendLabel: legendLabel,
      yAxisLabels,
      points
    };
  };

  // 4. Construir métricas
  metrics.value = [
    { key: "margen", kpiTitle: "Margen de Rentabilidad", ...buildChart(dataMargen, "Evolución de Margen de Rentabilidad", "Tendencia histórica por periodo", "Margen (%)") },
    { key: "rat", kpiTitle: "Rendimiento sobre Activos Totales (RAT)", ...buildChart(dataRat, "Evolución de RAT", "Tendencia histórica del RAT por periodo", "RAT (%)") },
    { key: "roe", kpiTitle: "Rendimiento sobre el Patrimonio", ...buildChart(dataRoe, "Evolución de ROE", "Tendencia histórica de ROE por periodo", "ROE (%)") }
  ];

  // 5. Construir Tabla (Orden Inverso: Más reciente primero)
  const reversedPeriods = [...periods].reverse();
  const reversedMargen = [...dataMargen].reverse();
  
  tableData.value = reversedPeriods.map((p, i) => {
    const currentMargen = reversedMargen[i];
    // Como está invertido, el "previo" en el tiempo es el siguiente en el arreglo (i+1)
    const prevMargen = i < reversedPeriods.length - 1 ? reversedMargen[i + 1] : currentMargen;
    const delta = currentMargen - prevMargen;

    return {
      label: p.label,
      ingresos: p.rentabilidad.datos_crudos?.ventas_netas || 0,
      utilidad: p.rentabilidad.datos_crudos?.utilidad_neta || 0,
      margen: currentMargen,
      delta: delta,
      deltaStr: `${delta > 0 ? '+' : ''}${delta.toFixed(1)}%`,
      deltaClass: delta >= 0 ? 'up' : 'down'
    };
  });
};

// Computadas
const activeMetric = computed(() => {
  if (metrics.value.length === 0) return null;
  return metrics.value.find((m) => m.key === selectedMetric.value) || metrics.value[0];
});

function selectMetric(key) {
  selectedMetric.value = key;
}

// Helpers SVG
const baselineY = 230;

const linePath = computed(() => {
  if (!activeMetric.value) return "";
  const pts = activeMetric.value.points;
  if (!pts.length) return "";
  return pts.map((p, i) => (i === 0 ? `M${p.x} ${p.y}` : `L${p.x} ${p.y}`)).join(" ");
});

const areaPath = computed(() => {
  if (!activeMetric.value) return "";
  const pts = activeMetric.value.points;
  if (!pts.length) return "";
  const first = pts[0];
  const last = pts[pts.length - 1];
  const mid = pts.map((p) => `L${p.x} ${p.y}`).join(" ");
  return `M${first.x} ${baselineY} L${first.x} ${first.y} ${mid} L${last.x} ${baselineY} Z`;
});

onMounted(() => {
  fetchPeriods();
});
</script>

<template>
  <main class="main" v-if="!loading && metrics.length > 0">
    <div class="container">
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

      <section class="card" v-if="activeMetric">
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

            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

            <path :d="areaPath" fill="url(#gradientMetric)"></path>
            <path :d="linePath" fill="none" stroke="#299de0" stroke-linecap="round" stroke-width="3"></path>

            <circle
              v-for="(p, idx) in activeMetric.points"
              :key="idx"
              :cx="p.x"
              :cy="p.y"
              fill="white"
              :r="hoveredPoint === p ? 6 : 4" 
              stroke="#299de0"
              stroke-width="2"
              style="transition: r 0.2s ease;"
            ></circle>

            <circle
              v-for="(p, idx) in activeMetric.points"
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
                :x="hoveredPoint.x - 32"
                :y="hoveredPoint.y - 42"
                width="64"
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

      <section class="table-card">
        <div class="table-head">
          <h3>Comparativo Histórico del Margen</h3>
        </div>

        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>Periodo</th>
                <th>Ingresos</th>
                <th>Utilidad Neta</th>
                <th>Margen Neto</th>
                <th class="center" style="text-align: center;">Variación (vs anterior)</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="(row, idx) in tableData" :key="idx">
                <td :class="idx === 0 ? 'strong' : ''">{{ row.label }}</td>
                <td class="muted">{{ currencyFmt.format(row.ingresos) }}</td>
                <td class="muted">{{ currencyFmt.format(row.utilidad) }}</td>
                <td>
                  <span class="badge" :class="idx === 0 ? 'badge-blue' : 'badge-gray'">
                    {{ row.margen.toFixed(1) }}%
                  </span>
                </td>
                <td class="center" style="text-align: center;" :class="row.deltaClass">
                  <span v-if="idx < tableData.length - 1 || tableData.length === 1">
                    {{ row.deltaStr }}
                  </span>
                  <span v-else class="muted" style="font-weight: normal">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

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
              <h3>Interpretación Automática</h3>
            </div>
            <p v-if="metrics.length > 0 && metrics[0].deltaType === 'up'">
              El margen de rentabilidad del periodo más reciente muestra una tendencia positiva frente al periodo inmediato anterior. La empresa está generando mayor utilidad por cada peso vendido.
            </p>
            <p v-else>
              Alerta: El margen de rentabilidad ha sufrido una contracción respecto al periodo anterior. Es necesario revisar si el costo de ventas o gastos operativos se han incrementado desproporcionadamente.
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
            <li><span class="material-symbols-outlined">check_circle</span><span>Monitorear de cerca los márgenes de operación y costos indirectos.</span></li>
            <li><span class="material-symbols-outlined">check_circle</span><span>Revisar las estrategias de fijación de precios según inflación y proveedores.</span></li>
            <li><span class="material-symbols-outlined">check_circle</span><span>Optimizar procesos que puedan estar erosionando el margen neto.</span></li>
          </ul>
        </article>
      </section>
    </div>
  </main>
  
  <div v-else-if="loading" style="padding: 40px; text-align: center; color: var(--muted);">
      Cargando análisis multiperiodo...
  </div>
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