<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { db } from "@/firebase/config";
import { collection, getDocs } from "firebase/firestore";

const route = useRoute();
const projectId = route.params.id_proyecto;

const kpis = ref([]);
const periodRows = ref([]);

const capitalPie = ref({
  totalLabel: "$0",
  pasivoPct: 0,
  capPct: 0,
  pasivo: "$0",
  cap: "$0",
});

const interpretation = ref(
  "Los indicadores de endeudamiento muestran la dependencia de la empresa frente a terceros y la suficiencia del capital propio."
);

const recommendations = ref([
  "Reestructurar deuda si el apalancamiento es alto",
  "Evaluar opciones de financiamiento interno",
  "Mantener la política actual de reinversión de utilidades",
]);

const formatCurrency = (value) => {
  if (value === undefined || value === null) return "$0";
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(value);
};

onMounted(async () => {
  if (!projectId) return;

  try {
    const periodosRef = collection(db, "proyectos", projectId, "periodos");
    const snapshot = await getDocs(periodosRef);

    const rowsTemp = [];
    let ultimosKpis = null;
    let ultimoPasivo = 0;
    let ultimoCapital = 0;

    snapshot.forEach((docSnap) => {
      const data = docSnap.data();
      
      if (data.analisis_endeudamiento) {
        const analisis = data.analisis_endeudamiento;
        const crudos = analisis.datos_crudos;

        ultimosKpis = analisis.kpis;
        ultimoPasivo = crudos.pasivo_total || 0;
        ultimoCapital = crudos.capital_social || 0;

        rowsTemp.push({
          period: data.label || docSnap.id,
          pasivoTotal: formatCurrency(crudos.pasivo_total),
          activoTotal: formatCurrency(crudos.activo_total),
          capital: formatCurrency(crudos.capital_social)
        });
      }
    });

    rowsTemp.sort((a, b) => a.period.localeCompare(b.period));

    if (ultimosKpis) {
      kpis.value = ultimosKpis;
    }
    periodRows.value = rowsTemp;

    const total = ultimoPasivo + ultimoCapital;
    if (total > 0) {
      capitalPie.value = {
        totalLabel: formatCurrency(total),
        pasivoPct: Math.round((ultimoPasivo / total) * 100),
        capPct: Math.round((ultimoCapital / total) * 100),
        pasivo: formatCurrency(ultimoPasivo),
        cap: formatCurrency(ultimoCapital)
      };
    }

  } catch (error) {
    console.error("Error al cargar los datos de endeudamiento:", error);
  }
});
</script>

<template>
  <div class="wrap">
    <!-- TITULO -->
    <div class="title">
      <h1>Endeudamiento</h1>
      <div class="subtitle">
        <p>Nivel de apalancamiento y estabilidad financiera de la empresa</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">Indicadores calculados a partir del Balance General</p>
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

    <!-- TABLE -->
    <section class="panel">
      <div class="panel-head">
        <h3>Detalle del Periodo</h3>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>PERIODO</th>
              <th>PASIVO TOTAL</th>
              <th>ACTIVO TOTAL</th>
              <th>CAPITAL CONTABLE</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in periodRows" :key="r.period">
              <td class="strong">{{ r.period }}</td>
              <td class="muted">{{ r.pasivoTotal }}</td>
              <td class="muted">{{ r.activoTotal }}</td>
              <td>
                <span class="pill">{{ r.capital }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- INFO -->
    <div class="info">
      <span class="material-symbols-outlined">info</span>
      <p>
        Para visualizar gráficas de evolución y comparativas detalladas, añade más periodos a tu
        análisis.
      </p>
    </div>

    <!-- COMPOSICION DEL CAPITAL -->
    <section class="panel pad">
      <div class="cap-head">
        <div>
          <h3>Composición del Capital</h3>
          <p>Estructura de capital para el periodo actual</p>
        </div>
      </div>

      <div class="cap-body">
        <div
          class="pie"
          :style="{
            background: `conic-gradient(
              #60a5fa 0% ${capitalPie.pasivoPct}%,
              #34d399 ${capitalPie.pasivoPct}% 100%
            )`,
          }"
        >
          <div class="pie-inner">
            <span class="pie-label">Suma</span>
            <span class="pie-total">{{ capitalPie.totalLabel }}</span>
          </div>
        </div>

        <div class="legend">
          <div class="legend-item">
            <span class="dot-color blue"></span>
            <div class="legend-text">
              <span class="legend-title">
                Pasivo Total <span class="pct">{{ capitalPie.pasivoPct }}%</span>
              </span>
              <span class="legend-value">{{ capitalPie.pasivo }}</span>
            </div>
          </div>

          <div class="legend-item">
            <span class="dot-color green"></span>
            <div class="legend-text">
              <span class="legend-title">
                Capital Contable <span class="pct">{{ capitalPie.capPct }}%</span>
              </span>
              <span class="legend-value">{{ capitalPie.cap }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- INTERPRETACION + RECS -->
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

        <p class="note-text">{{ interpretation }}</p>
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
  color: #0e161b;
}

/* TITULO */
.title h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
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
}

/* PANEL + TABLE */
.panel {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.panel.pad {
  padding: 18px;
}

.panel-head {
  padding: 14px 18px;
  border-bottom: 1px solid #e8eff3;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
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

/* INFO */
.info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1e3a8a;
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

/* COMPOSICION DEL CAPITAL */
.cap-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
}
.cap-head p {
  margin: 6px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.cap-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-items: center;
  justify-content: center;
  padding-top: 12px;
}

.pie {
  width: 224px;
  height: 224px;
  border-radius: 999px;
  box-shadow: inset 0 0 0 10px rgba(0, 0, 0, 0.02);
  display: grid;
  place-items: center;
}

.pie-inner {
  width: 140px;
  height: 140px;
  background: #ffffff;
  border-radius: 999px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.pie-label {
  font-size: 11px;
  font-weight: 900;
  color: #507c95;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.pie-total {
  margin-top: 4px;
  font-size: 18px;
  font-weight: 900;
}

.legend {
  width: 100%;
  border-top: 1px solid #f1f5f9;
  padding-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 14px 26px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dot-color {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
.dot-color.blue {
  background: #60a5fa;
}
.dot-color.sky {
  background: #bfdbfe;
}
.dot-color.green {
  background: #34d399;
}

.legend-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.legend-title {
  font-size: 13px;
  font-weight: 800;
}
.pct {
  margin-left: 6px;
  color: #9ca3af;
  font-weight: 700;
}
.legend-value {
  font-size: 12px;
  font-weight: 800;
  color: #507c95;
}

/* INTERPRETACION + RECS */
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
}

.note-text {
  margin: 0;
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
  .cap-body {
    gap: 22px;
  }
}
</style>