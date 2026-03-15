<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";


// === Dummy data (luego lo conectas a backend / Firestore) ===
const view = ref({
  title: "Rentabilidad",
  helpLabel: "Ir a centro de aprendizaje",
  description: "Evalúa la capacidad de la empresa para generar utilidades",
  note: "Indicadores calculados a partir del Estado de Resultados",
});

// “Periodo base” solo UI
const basePeriod = ref("Q2 2024");

// KPIs multiperiodo (valor actual + delta vs base)
const kpis = ref([
  {
    label: "Margen de Rentabilidad",
    value: "12.8%",
    dot: "ok",
    delta: { type: "up", value: "+0.5%" },
  },
  {
    label: "Rendimiento sobre Activos Totales (RAT)",
    value: "15.4%",
    dot: "ok",
    delta: { type: "up", value: "+1.2%" },
  },
  {
    label: "Rendimiento sobre el Patrimonio",
    value: "21.0%",
    dot: "warn",
    delta: { type: "down", value: "-0.8%" },
  },
]);

// Tabla comparativa multiperiodo
const periodRows = ref([
  {
    period: "Q3 2024",
    ingresos: "$4,250,000",
    utilidad: "$845,000",
    margen: "19.8%",
    varTrimestral: "+5.2%",
    varType: "up",
    margenPill: "blue",
  },
  {
    period: "Q2 2024",
    ingresos: "$3,820,000",
    utilidad: "$802,000",
    margen: "21.0%",
    varTrimestral: "+2.8%",
    varType: "up",
    margenPill: "gray",
  },
  {
    period: "Q1 2024",
    ingresos: "$3,500,000",
    utilidad: "$715,000",
    margen: "20.4%",
    varTrimestral: "-1.2%",
    varType: "down",
    margenPill: "gray",
  },
]);

const interpretation = ref(
  "La empresa presenta una mejora sostenida en el margen operativo, aunque el margen neto se ve afectado por costos financieros elevados."
);

const recommendations = ref([
  "Control de costos operativos",
  "Revisión de estrategia de precios",
  "Optimización de procesos internos",
]);

const route = useRoute();
const router=useRouter();

function handleLearnMore() {

  const resolved = router.resolve({
    name: "teoriaRentabilidad", // el name de tu ruta
  });

  window.open(resolved.href, "_blank", "noopener,noreferrer");
}

const basePeriodLabel = computed(() => `Periodo Base: ${basePeriod.value}`);
</script>

<template>
  <div class="wrap">
    <!-- TITLE -->
    <div class="head">
      <div class="head-title">
        <h1>{{ view.title }}</h1>

        <button class="btn-info" type="button" @click="handleLearnMore">
          <span class="material-symbols-outlined">info</span>
          <span>{{ view.helpLabel }}</span>
        </button>
      </div>

      <div class="sub">
        <p>{{ view.description }}</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">{{ view.note }}</p>
      </div>
    </div>

    <!-- KPIs -->
    <section class="kpis">
      <article v-for="k in kpis" :key="k.label" class="kpi">
        <div class="kpi-top">
          <p class="kpi-label">{{ k.label }}</p>
          <span class="kpi-dot" :class="k.dot" aria-hidden="true"></span>
        </div>

        <div class="kpi-value">{{ k.value }}</div>

        <div class="kpi-delta">
          <span
            class="delta-badge"
            :class="k.delta.type === 'up' ? 'delta-up' : 'delta-down'"
          >
            <span class="material-symbols-outlined">
              {{ k.delta.type === "up" ? "trending_up" : "trending_down" }}
            </span>
            {{ k.delta.value }}
          </span>

          <span class="delta-note">vs periodo base</span>
        </div>
      </article>
    </section>

    <!-- CHART PANEL -->
    <section class="panel">
      <div class="panel-head">
        <div>
          <h3>Evolución de Rentabilidad</h3>
          <p>Comparativa de Utilidad Neta y Margen Neto por trimestre</p>
        </div>

        <div class="legend">
          <div class="legend-item">
            <span class="legend-dot dot-utilidad"></span>
            <span>Utilidad Neta ($)</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot dot-margen"></span>
            <span>Margen Neto (%)</span>
          </div>
        </div>
      </div>

      <div class="chart">
        <!-- SVG estático (igual que tu HTML) -->
        <svg class="chart-svg" fill="none" preserveAspectRatio="none" viewBox="0 0 800 300">
          <defs>
            <linearGradient id="gradientUtilidad" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#299de0" stop-opacity="0.15" />
              <stop offset="100%" stop-color="#299de0" stop-opacity="0" />
            </linearGradient>
          </defs>

          <line x1="50" y1="50" x2="750" y2="50" stroke="#f1f5f9" stroke-width="1" />
          <line x1="50" y1="110" x2="750" y2="110" stroke="#f1f5f9" stroke-width="1" />
          <line x1="50" y1="170" x2="750" y2="170" stroke="#f1f5f9" stroke-width="1" />
          <line x1="50" y1="230" x2="750" y2="230" stroke="#f1f5f9" stroke-width="1" />

          <path
            d="M50 230 L 50 180 Q 150 160 225 140 T 400 130 T 575 100 T 750 60 L 750 230 Z"
            fill="url(#gradientUtilidad)"
          />
          <path
            d="M50 180 Q 150 160 225 140 T 400 130 T 575 100 T 750 60"
            fill="none"
            stroke="#299de0"
            stroke-linecap="round"
            stroke-width="3"
          />
          <path
            d="M50 200 L 225 190 L 400 170 L 575 185 L 750 160"
            fill="none"
            stroke="#1e293b"
            stroke-dasharray="6 4"
            stroke-linecap="round"
            stroke-width="2"
          />

          <circle cx="50" cy="180" r="4" fill="white" stroke="#299de0" stroke-width="2" />
          <circle cx="225" cy="140" r="4" fill="white" stroke="#299de0" stroke-width="2" />
          <circle cx="400" cy="130" r="4" fill="white" stroke="#299de0" stroke-width="2" />
          <circle cx="575" cy="100" r="4" fill="white" stroke="#299de0" stroke-width="2" />
          <circle cx="750" cy="60" r="4" fill="white" stroke="#299de0" stroke-width="2" />

          <circle cx="50" cy="200" r="3" fill="#1e293b" />
          <circle cx="225" cy="190" r="3" fill="#1e293b" />
          <circle cx="400" cy="170" r="3" fill="#1e293b" />
          <circle cx="575" cy="185" r="3" fill="#1e293b" />
          <circle cx="750" cy="160" r="3" fill="#1e293b" />

          <text x="50" y="260" text-anchor="middle" font-size="12" fill="#507c95">Q3 '23</text>
          <text x="225" y="260" text-anchor="middle" font-size="12" fill="#507c95">Q4 '23</text>
          <text x="400" y="260" text-anchor="middle" font-size="12" fill="#507c95">Q1 '24</text>
          <text x="575" y="260" text-anchor="middle" font-size="12" fill="#507c95">Q2 '24</text>
          <text
            x="750"
            y="260"
            text-anchor="middle"
            font-size="12"
            font-weight="bold"
            fill="#0e161b"
          >
            Q3 '24
          </text>
        </svg>

        <div class="axis axis-left">
          <span>$1M</span>
          <span>$750k</span>
          <span>$500k</span>
          <span>$250k</span>
        </div>

        <div class="axis axis-right">
          <span>20%</span>
          <span>15%</span>
          <span>10%</span>
          <span>5%</span>
        </div>
      </div>
    </section>

    <!-- TABLE -->
    <section class="table-panel">
      <div class="table-head">
        <h3>Comparativo por Periodo</h3>
        <span class="base-pill">{{ basePeriodLabel }}</span>
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
            <tr v-for="r in periodRows" :key="r.period">
              <td class="strong">{{ r.period }}</td>
              <td class="muted">{{ r.ingresos }}</td>
              <td class="muted">{{ r.utilidad }}</td>
              <td>
                <span class="pill" :class="r.margenPill === 'blue' ? 'pill-blue' : 'pill-gray'">
                  {{ r.margen }}
                </span>
              </td>
              <td class="right" :class="r.varType === 'up' ? 'var-up' : 'var-down'">
                {{ r.varTrimestral }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- NOTES -->
    <section class="notes">
      <article class="note">
        <div class="note-bg" aria-hidden="true">
          <span class="material-symbols-outlined">warning</span>
        </div>

        <div class="note-head">
          <span class="tag tag-blue">
            <span class="material-symbols-outlined">insights</span>
          </span>
          <h3>Interpretación y alertas</h3>
        </div>

        <p class="note-text">{{ interpretation }}</p>
      </article>

      <article class="note">
        <div class="note-head">
          <span class="tag tag-green">
            <span class="material-symbols-outlined">checklist</span>
          </span>
          <h3>Recomendaciones</h3>
        </div>

        <ul class="list">
          <li v-for="(item, idx) in recommendations" :key="idx">
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
.wrap {
  width: min(1200px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Title */
.head {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.head-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.head-title h1 {
  margin: 0;
  font-size: 26px;
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
  transition: border-color 0.15s ease, color 0.15s ease;
}

.btn-info:hover {
  border-color: #299de0;
  color: #299de0;
}

.btn-info .material-symbols-outlined {
  font-size: 18px;
}

.sub {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #507c95;
  font-size: 13px;
  font-weight: 700;
}

.dot {
  display: none;
  color: #d1d5db;
}

.small {
  font-size: 12px;
}

/* KPIs */
.kpis {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.kpi {
  background: #fff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.15s ease;
}

.kpi:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
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

.delta-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 900;
}

.delta-badge .material-symbols-outlined {
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
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

/* Panel (chart) */
.panel {
  background: #fff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.panel-head {
  display: flex;
  align-items: flex-start;
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

.panel-head p {
  margin: 6px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.legend {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #0e161b;
  font-size: 12px;
  font-weight: 800;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
}

.dot-utilidad {
  background: #299de0;
}

.dot-margen {
  background: #1e293b;
}

.chart {
  position: relative;
  width: 100%;
  height: 300px;
  margin-top: 12px;
}

.chart-svg {
  width: 100%;
  height: 100%;
}

.axis {
  position: absolute;
  top: 0;
  bottom: 32px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.axis-left {
  left: 0;
  width: 48px;
  text-align: right;
  padding-right: 8px;
}

.axis-right {
  right: 0;
  width: 48px;
  text-align: left;
  padding-left: 8px;
}

/* Table */
.table-panel {
  background: #fff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.table-head {
  padding: 14px 18px;
  border-bottom: 1px solid #e8eff3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.table-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.base-pill {
  font-size: 10px;
  font-weight: 900;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  padding: 4px 8px;
  border-radius: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 860px;
}

.table thead th {
  text-align: left;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #507c95;
  background: #f8fafb;
  border-bottom: 1px solid #e8eff3;
  padding: 12px 18px;
  font-weight: 900;
}

.table tbody td {
  padding: 14px 18px;
  border-bottom: 1px solid #e8eff3;
  font-size: 13px;
}

.table tbody tr:hover {
  background: #f9fafb;
}

.strong {
  font-weight: 900;
  color: #0e161b;
}

.muted {
  color: #507c95;
  font-weight: 700;
}

.right {
  text-align: right;
}

.pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 900;
  padding: 6px 10px;
  border-radius: 10px;
}

.pill-blue {
  background: #eff6ff;
  color: #1d4ed8;
}

.pill-gray {
  background: #f3f4f6;
  color: #374151;
}

.var-up {
  color: #16a34a;
  font-weight: 800;
}

.var-down {
  color: #ef4444;
  font-weight: 800;
}

/* Notes */
.notes {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.note {
  position: relative;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 70%);
  border: 1px solid #dbeafe;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.note-bg {
  position: absolute;
  right: 10px;
  top: 6px;
  opacity: 0.1;
}

.note-bg .material-symbols-outlined {
  font-size: 120px;
  color: #299de0;
}

.note-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  position: relative;
  z-index: 1;
}

.tag {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
}

.tag-blue {
  background: #dbeafe;
  color: #299de0;
}

.tag-green {
  background: #dcfce7;
  color: #15803d;
}

.tag .material-symbols-outlined {
  font-size: 20px;
}

.note h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.note-text {
  margin: 0;
  color: #0e161b;
  font-weight: 700;
  font-size: 14px;
  line-height: 1.55;
  position: relative;
  z-index: 1;
}

.list {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
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
  .sub {
    flex-direction: row;
    align-items: baseline;
    gap: 10px;
  }
  .dot {
    display: inline;
  }
}

@media (min-width: 768px) {
  .kpis {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1024px) {
  .notes {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>