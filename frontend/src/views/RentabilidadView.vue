<script setup>
import { ref } from "vue";

/**
 * Solo UI (sin backend)
 * Esta view asume que ya está dentro de DashboardLayout.vue
 * (Topbar + Sidebar viven en el layout, NO aquí).
 */

const kpis = ref([
  { label: "Margen de Rentabilidad", value: "12.8%", status: "ok" },
  { label: "Rendimiento sobre Activos Totales (RAT)", value: "8.5%", status: "warn" },
  { label: "Rendimiento sobre el Patrimonio", value: "15.4%", status: "ok" },
]);

const periodRows = ref([
  {
    period: "Q3 2024",
    ingresos: "$4,250,000",
    utilidad: "$845,000",
    margen: "19.8%",
  },
]);

const recommendations = ref([
  "Control de costos operativos",
  "Revisión de estrategia de precios",
  "Optimización de procesos internos",
]);
</script>

<template>
  <div class="wrap">
    <div class="title">
      <h1>Rentabilidad</h1>
      <div class="subtitle">
        <p>Evalúa la capacidad de la empresa para generar utilidades</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">Indicadores calculados a partir del Estado de Resultados</p>
      </div>
    </div>

    <!-- KPI CARDS -->
    <section class="kpis">
      <article v-for="k in kpis" :key="k.label" class="kpi">
        <div class="kpi-top">
          <p class="kpi-label">{{ k.label }}</p>
          <span class="kpi-dot" :class="k.status" aria-hidden="true"></span>
        </div>
        <div class="kpi-value">{{ k.value }}</div>
      </article>
    </section>

    <!-- TABLA-->
    <section class="panel">
      <div class="panel-head">
        <h3>Detalle del Periodo</h3>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Periodo</th>
              <th>Ingresos</th>
              <th>Utilidad Neta</th>
              <th>Margen Neto</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in periodRows" :key="r.period">
              <td class="strong">{{ r.period }}</td>
              <td class="muted">{{ r.ingresos }}</td>
              <td class="muted">{{ r.utilidad }}</td>
              <td>
                <span class="pill">{{ r.margen }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div class="info">
      <span class="material-symbols-outlined">info</span>
      <p>
        Para visualizar gráficas de evolución y comparativas detalladas, añade más periodos a tu
        análisis.
      </p>
    </div>

    <!-- INTERPRETACIÓN (pendiente) -->
    <section class="grid-2">
      <article class="note note-warn">
        <div class="note-bg" aria-hidden="true">
          <span class="material-symbols-outlined">warning</span>
        </div>

        <div class="note-head">
          <span class="tag tag-blue">
            <span class="material-symbols-outlined">insights</span>
          </span>
          <h3>Interpretación y alertas</h3>
        </div>

        <p class="note-text">
          El margen operativo presenta un rendimiento sólido en el periodo actual, aunque el
          margen neto se ve afectado por costos financieros elevados.
        </p>
      </article>

      <article class="note note-ok">
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
.title h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
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
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 16px;
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

/* Panel + table */
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
}

.panel-head h3 {
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
  min-width: 720px;
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

.pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 900;
  padding: 6px 10px;
  border-radius: 10px;
  background: #eff6ff;
  color: #1d4ed8;
}

/* Info */
.info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.info .material-symbols-outlined {
  color: #299de0;
}

.info p {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: #299de0;
}

/* Bottom grid */
.grid-2 {
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

@media (min-width: 1024px) {
  .kpis {
    grid-template-columns: repeat(3, 1fr);
  }
  .grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>