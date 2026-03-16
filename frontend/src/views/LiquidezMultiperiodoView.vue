<script setup>
import { computed, ref } from "vue";

/**
 * Dummy data (luego lo conectas a tu Firestore/API).
 * Mantengo la UI tal cual tu Tailwind: KPIs seleccionables, chart SVG, “donuts”, tabla y cajas.
 */

const activeKpi = ref("razon"); // razon | acida | capital

const kpis = ref([
  {
    key: "razon",
    label: "Razón Circulante",
    value: "1.85",
    status: "ok",
    deltaType: "up",
    deltaValue: "+0.12",
    deltaNote: "vs mes anterior",
  },
  {
    key: "acida",
    label: "Prueba Ácida",
    value: "1.20",
    status: "warn",
    deltaType: "down",
    deltaValue: "-0.05",
    deltaNote: "vs mes anterior",
  },
  {
    key: "capital",
    label: "Capital de Trabajo",
    value: "$1.25M",
    status: "ok",
    deltaType: "up",
    deltaValue: "+5.4%",
    deltaNote: "Recursos netos",
  },
]);

const selectedKpi = computed(() => kpis.value.find((k) => k.key === activeKpi.value) || kpis.value[0]);

const tableRows = ref([
  { period: "Q3 '23", activo: "$2,664,500", pasivo: "$1,614,500", rc: "1.65", pa: "1.05", ct: "$1,050,000", highlight: false },
  { period: "Q4 '23", activo: "$2,627,700", pasivo: "$1,527,700", rc: "1.72", pa: "1.10", ct: "$1,100,000", highlight: false },
  { period: "Q1 '24", activo: "$2,624,300", pasivo: "$1,474,300", rc: "1.78", pa: "1.15", ct: "$1,150,000", highlight: false },
  { period: "Q2 '24", activo: "$2,681,400", pasivo: "$1,481,400", rc: "1.81", pa: "1.18", ct: "$1,200,000", highlight: false },
  { period: "Q3 '24", activo: "$2,720,500", pasivo: "$1,470,500", rc: "1.85", pa: "1.20", ct: "$1,250,000", highlight: true },
]);

const recommendations = ref([
  "Mejorar políticas de cobranza para reducir el ciclo de efectivo.",
  "Optimizar niveles de inventario para liberar capital de trabajo.",
  "Incrementar reservas de efectivo como contingencia operativa.",
]);

function setActive(k) {
  activeKpi.value = k;
}

function learnMore() {
  // Aquí luego haces router.push a tu “Centro de aprendizaje” de Liquidez.
  // Ej: router.push(`/proyecto/${route.params.id_proyecto}/dashboard-multi/learning/liquidez`)
  console.log("TODO: navegar a teoría de Liquidez");
}
</script>

<template>
  <div class="wrap">
    <!-- TITLE -->
    <div class="title">
      <div class="title-row">
        <h1>Liquidez</h1>

        <button class="btn-learn" type="button" @click="learnMore">
          <span class="material-symbols-outlined">info</span>
          <span>Saber más</span>
        </button>
      </div>

      <div class="subtitle">
        <p>Capacidad de la empresa para cumplir con sus obligaciones a corto plazo</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">Indicadores calculados a partir del Balance General</p>
      </div>
    </div>

    <!-- KPI CARDS -->
    <section class="kpis">
      <button
        v-for="k in kpis"
        :key="k.key"
        type="button"
        class="kpi"
        :class="{ selected: activeKpi === k.key }"
        @click="setActive(k.key)"
      >
        <div class="kpi-top">
          <p class="kpi-label" :class="{ 'kpi-label-selected': activeKpi === k.key }">{{ k.label }}</p>
          <span class="kpi-dot" :class="k.status" aria-hidden="true"></span>
        </div>

        <div class="kpi-value">{{ k.value }}</div>

        <div class="kpi-delta">
          <span
            class="delta-pill"
            :class="k.deltaType === 'up' ? 'delta-up' : 'delta-down'"
          >
            <span class="material-symbols-outlined">
              {{ k.deltaType === "up" ? "trending_up" : "trending_down" }}
            </span>
            {{ k.deltaValue }}
          </span>
          <span class="delta-note">{{ k.deltaNote }}</span>
        </div>
      </button>
    </section>

    <!-- CHART PANEL -->
    <section class="panel">
      <div class="panel-head">
        <div>
          <h3>Evolución de {{ selectedKpi.label }}</h3>
          <p class="panel-sub">
            Tendencia de {{ selectedKpi.label }} sobre el tiempo
          </p>
        </div>

        <div class="legend">
          <div class="legend-item">
            <span class="legend-dot" aria-hidden="true"></span>
            <span>{{ selectedKpi.label }}</span>
          </div>
        </div>
      </div>

      <div class="chart">
        <!-- Dejo el SVG tal cual (estático) como tu mockup -->
        <svg class="chart-svg" fill="none" preserveAspectRatio="none" viewBox="0 0 800 300">
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

          <path
            d="M50 230 L 50 190 Q 150 180 225 160 T 400 150 T 575 110 T 750 70 L 750 230 Z"
            fill="url(#gradient-rc)"
            opacity="0.1"
          ></path>

          <path
            d="M50 190 Q 150 180 225 160 T 400 150 T 575 110 T 750 70"
            fill="none"
            stroke="#299de0"
            stroke-linecap="round"
            stroke-width="3"
          ></path>

          <circle cx="50" cy="190" fill="white" r="5" stroke="#299de0" stroke-width="2.5"></circle>
          <circle cx="225" cy="160" fill="white" r="5" stroke="#299de0" stroke-width="2.5"></circle>
          <circle cx="400" cy="150" fill="white" r="5" stroke="#299de0" stroke-width="2.5"></circle>
          <circle cx="575" cy="110" fill="white" r="5" stroke="#299de0" stroke-width="2.5"></circle>
          <circle cx="750" cy="70" fill="white" r="5" stroke="#299de0" stroke-width="2.5"></circle>

          <text fill="#0e161b" font-family="Inter, sans-serif" font-size="12" font-weight="600" text-anchor="middle" x="50" y="175">1.65</text>
          <text fill="#0e161b" font-family="Inter, sans-serif" font-size="12" font-weight="600" text-anchor="middle" x="225" y="145">1.72</text>
          <text fill="#0e161b" font-family="Inter, sans-serif" font-size="12" font-weight="600" text-anchor="middle" x="400" y="135">1.78</text>
          <text fill="#0e161b" font-family="Inter, sans-serif" font-size="12" font-weight="600" text-anchor="middle" x="575" y="95">1.81</text>
          <text fill="#0e161b" font-family="Inter, sans-serif" font-size="12" font-weight="bold" text-anchor="middle" x="750" y="55">1.85</text>

          <text fill="#507c95" font-family="Inter, sans-serif" font-size="12" text-anchor="middle" x="50" y="260">Q3 '23</text>
          <text fill="#507c95" font-family="Inter, sans-serif" font-size="12" text-anchor="middle" x="225" y="260">Q4 '23</text>
          <text fill="#507c95" font-family="Inter, sans-serif" font-size="12" text-anchor="middle" x="400" y="260">Q1 '24</text>
          <text fill="#507c95" font-family="Inter, sans-serif" font-size="12" text-anchor="middle" x="575" y="260">Q2 '24</text>
          <text fill="#0e161b" font-family="Inter, sans-serif" font-size="12" font-weight="bold" text-anchor="middle" x="750" y="260">Q3 '24</text>

          <defs>
            <linearGradient id="gradient-rc" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#299de0"></stop>
              <stop offset="100%" stop-color="white"></stop>
            </linearGradient>
          </defs>
        </svg>
      </div>
    </section>

    <!-- DONUTS -->
    <section class="grid-2">
      <article class="card">
        <h3>Composición Activo Circulante</h3>
        <p class="card-sub">Desglose del Activo Circulante</p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#299de0" stroke-dasharray="25 100" stroke-dashoffset="25" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#1e293b" stroke-dasharray="45 100" stroke-dashoffset="0" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#507c95" stroke-dasharray="20 100" stroke-dashoffset="-45" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#d1dee6" stroke-dasharray="10 100" stroke-dashoffset="-65" stroke-width="4"></circle>
            </svg>

            <div class="donut-center">
              <span class="donut-kicker">Total</span>
              <span class="donut-total">$2.7M</span>
            </div>
          </div>
        </div>

        <div class="legend-grid">
          <div class="legend-row">
            <span class="dot" style="background:#1e293b" aria-hidden="true"></span>
            <span>Cuentas por Cobrar (45%)</span>
          </div>
          <div class="legend-row">
            <span class="dot" style="background:#299de0" aria-hidden="true"></span>
            <span>Efectivo y Eq. (25%)</span>
          </div>
          <div class="legend-row">
            <span class="dot" style="background:#507c95" aria-hidden="true"></span>
            <span>Inventarios (20%)</span>
          </div>
          <div class="legend-row">
            <span class="dot" style="background:#d1dee6" aria-hidden="true"></span>
            <span>Otros Activos (10%)</span>
          </div>
        </div>
      </article>

      <article class="card">
        <h3>Composición Pasivo Circulante</h3>
        <p class="card-sub">Desglose del Pasivo Circulante</p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e11d48" stroke-dasharray="35 100" stroke-dashoffset="0" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#fb923c" stroke-dasharray="40 100" stroke-dashoffset="-35" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#fcd34d" stroke-dasharray="15 100" stroke-dashoffset="-75" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#fecdd3" stroke-dasharray="10 100" stroke-dashoffset="-90" stroke-width="4"></circle>
            </svg>

            <div class="donut-center">
              <span class="donut-kicker">Total</span>
              <span class="donut-total">$1.5M</span>
            </div>
          </div>
        </div>

        <div class="legend-grid">
          <div class="legend-row">
            <span class="dot" style="background:#e11d48" aria-hidden="true"></span>
            <span>Proveedores (35%)</span>
          </div>
          <div class="legend-row">
            <span class="dot" style="background:#fb923c" aria-hidden="true"></span>
            <span>Deuda a Corto Plazo (40%)</span>
          </div>
          <div class="legend-row">
            <span class="dot" style="background:#fcd34d" aria-hidden="true"></span>
            <span>Impuestos por Pagar (15%)</span>
          </div>
          <div class="legend-row">
            <span class="dot" style="background:#fecdd3" aria-hidden="true"></span>
            <span>Otros Pasivos (10%)</span>
          </div>
        </div>
      </article>
    </section>

    <!-- TABLE -->
    <section class="panel">
      <div class="panel-head">
        <h3>Comparativa por periodo</h3>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Periodo</th>
              <th class="right">Activo Circulante</th>
              <th class="right">Pasivo Circulante</th>
              <th class="right">Razón Circulante</th>
              <th class="right">Prueba Ácida</th>
              <th class="right">Capital de Trabajo</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="r in tableRows"
              :key="r.period"
              :class="{ highlight: r.highlight }"
            >
              <td class="strong" :class="{ primary: r.highlight }">{{ r.period }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.activo }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.pasivo }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.rc }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.pa }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.ct }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- INTERPRETATION + RECS -->
    <section class="grid-2">
      <article class="note note-warn">
        <div class="note-bg" aria-hidden="true">
          <span class="material-symbols-outlined">warning</span>
        </div>

        <div class="note-mini">
          <span class="material-symbols-outlined">info</span>
          <span>Interpretación del Sistema</span>
        </div>

        <h3>Interpretación y alertas</h3>
        <p>
          La empresa mantiene una razón circulante aceptable, pero una alta dependencia de cuentas por cobrar podría
          generar problemas de liquidez inmediata. Se recomienda vigilar los plazos de cobranza para asegurar el flujo
          de caja operativo.
        </p>
      </article>

      <article class="note note-ok">
        <div class="note-head">
          <span class="tag-green">
            <span class="material-symbols-outlined">rocket_launch</span>
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
}

.kpi-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34,197,94,0.4);
}

.kpi-dot.warn {
  background: #facc15;
  box-shadow: 0 0 8px rgba(250,204,21,0.4);
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

.legend-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
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