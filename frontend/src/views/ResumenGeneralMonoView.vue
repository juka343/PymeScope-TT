<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

// ===== Datos dummy (luego lo conectas a tu backend) =====
const kpis = ref([
  { label: "Ingresos Totales", value: "$4,250,000", status: "ok" },
  { label: "Utilidad Neta", value: "$845,000", status: "ok" },
  { label: "Margen Rentabilidad", value: "19.8%", status: "ok" },
  { label: "Liquidez General", value: "1.5", status: "ok" },
]);

const cards = ref([
  {
    title: "Rentabilidad",
    icon: "trending_up",
    detailRoute: "rentabilidad",
    items: [
      { label: "ROE (Retorno s/ Capital)", target: "Objetivo: >15%", value: "15.4%", dot: "ok" },
      { label: "ROA (Retorno s/ Activos)", target: "Objetivo: >10%", value: "8.2%", dot: "warn" },
    ],
  },
  {
    title: "Liquidez",
    icon: "attach_money",
    detailRoute: "liquidez",
    items: [
      { label: "Prueba Ácida", target: "Objetivo: >1.0", value: "1.2", dot: "ok" },
      { label: "Capital de Trabajo", target: "Suficiente para 3m", value: "$520k", dot: "ok" },
    ],
  },
  {
    title: "Endeudamiento",
    icon: "account_balance_wallet",
    detailRoute: "endeudamiento",
    items: [
      { label: "Razón de Deuda", target: "Objetivo: <0.5", value: "0.45", dot: "ok" },
      { label: "Cobertura Intereses", target: "Capacidad de pago", value: "3.8x", dot: "warn" },
    ],
  },
  {
    title: "Estructura Financiera",
    icon: "layers",
    detailRoute: "estructura",
    items: [
      { label: "Solvencia", target: "Objetivo: >1.5", value: "1.82", dot: "ok" },
      { label: "Seguridad a Largo Plazo", target: "Ratio de garantía", value: "2.1x", dot: "ok" },
    ],
  },
]);

const periodLabel = ref("Q3 2024");

const edoResultados = ref([
  { concept: "Ventas Netas", value: "$4,250,000", pct: "100%", tone: "normal" },
  { concept: "Costo de Ventas", value: "($2,465,000)", pct: "58.0%", tone: "neg" },
  { concept: "Utilidad Bruta", value: "$1,785,000", pct: "42.0%", tone: "strong" },
  { concept: "Gastos de Operación", value: "($943,500)", pct: "22.2%", tone: "neg" },
  { concept: "Utilidad de Operación", value: "$841,500", pct: "19.8%", tone: "strong" },
]);

const interpretation = ref(
  "El margen operativo presenta un rendimiento sólido en el periodo actual, aunque el margen neto se ve afectado por costos financieros elevados."
);

const recommendations = ref([
  "Control de costos operativos",
  "Revisión de estrategia de precios",
  "Optimización de procesos internos",
]);

function goDetail(path) {
  router.push(path);
}

function viewFullIncomeStatement() {
  console.log("Ver estado de resultados completo");
}
</script>

<template>
  <div class="wrap">
    <!-- KPIs -->
    <section class="kpi-grid">
      <article v-for="k in kpis" :key="k.label" class="kpi-card">
        <div class="kpi-top">
          <p class="kpi-label">{{ k.label }}</p>
          <span class="kpi-dot" :class="k.status" aria-hidden="true"></span>
        </div>
        <div class="kpi-value">{{ k.value }}</div>
      </article>
    </section>

    <!-- Cards 4 columnas -->
    <section class="cards-grid">
      <article v-for="c in cards" :key="c.title" class="card">
        <div class="card-head">
          <span class="material-symbols-outlined card-ico" aria-hidden="true">{{ c.icon }}</span>
          <h4>{{ c.title }}</h4>
        </div>

        <div class="card-body">
          <div v-for="(it, idx) in c.items" :key="it.label" class="metric">
            <div class="metric-left">
              <p class="metric-name">{{ it.label }}</p>
              <p class="metric-target">{{ it.target }}</p>
            </div>

            <div class="metric-right">
              <p class="metric-value">{{ it.value }}</p>
              <span class="mini-dot" :class="it.dot" aria-hidden="true"></span>
            </div>

            <div v-if="idx !== c.items.length - 1" class="sep"></div>
          </div>
        </div>

        <div class="card-foot">
          <button class="link-btn" type="button" @click="goDetail(c.detailRoute)">Ver detalle</button>
        </div>
      </article>
    </section>

    <!-- Tabla: Estructura del Resultado -->
    <section class="table-card">
      <div class="table-head">
        <div class="table-title">
          <span class="material-symbols-outlined" aria-hidden="true">receipt_long</span>
          <h4>Estructura del Resultado</h4>
        </div>
        <!-- <span class="pill">{{ periodLabel }}</span> -->
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Concepto</th>
              <th class="right">Valor</th>
              <th class="right">% Ventas</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in edoResultados"
              :key="r.concept"
              :class="[
                r.tone === 'strong' ? 'row-strong' : '',
                r.tone === 'neg' ? 'row-neg' : ''
              ]"
            >
              <td class="concept" :class="{ strong: r.tone === 'strong' }">{{ r.concept }}</td>
              <td class="right" :class="{ strong: r.tone === 'strong' }">{{ r.value }}</td>
              <td class="right" :class="{ strong: r.tone === 'strong' }">{{ r.pct }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- <div class="table-foot">
        <button class="link-btn" type="button" @click="viewFullIncomeStatement">
          Ver estado de resultados completo
        </button>
      </div> -->
    </section>

    <!-- Interpretación + Recomendaciones -->
    <section class="notes-grid">
      <article class="note note-blue">
        <div class="note-bg" aria-hidden="true">
          <span class="material-symbols-outlined">warning</span>
        </div>

        <div class="note-head">
          <div class="tag tag-blue">
            <span class="material-symbols-outlined">insights</span>
          </div>
          <h3>Interpretación y alertas</h3>
        </div>

        <p class="note-text">{{ interpretation }}</p>
      </article>

      <article class="note note-white">
        <div class="note-head">
          <div class="tag tag-green">
            <span class="material-symbols-outlined">checklist</span>
          </div>
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

    <!-- Info -->
    <div class="info">
      <span class="material-symbols-outlined">info</span>
      <p>Para visualizar gráficas de evolución y comparativas detalladas, añade más periodos a tu análisis.</p>
    </div>

    <footer class="foot">
      <p>
        Todos los datos son confidenciales. <br />
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
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

/* ===== KPI GRID ===== */
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.kpi-card {
  background: #fff;
  border: 1px solid #e8eff3;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  transition: box-shadow 0.15s ease;
}

.kpi-card:hover {
  box-shadow: 0 10px 22px rgba(0,0,0,0.08);
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
  box-shadow: 0 0 8px rgba(34,197,94,0.4);
}

.kpi-value {
  margin-top: 8px;
  font-size: 22px;
  font-weight: 900;
}

/* ===== Cards grid (4) ===== */
.cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.card {
  background: #fff;
  border: 1px solid #e8eff3;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
}

.card-head {
  padding: 14px 16px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-ico {
  color: #299de0;
  font-size: 20px;
}

.card-head h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 900;
}

.card-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric {
  position: relative;
  display: grid;
  gap: 10px;
}

.metric-left .metric-name {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  font-weight: 800;
}

.metric-left .metric-target {
  margin: 4px 0 0;
  color: #9ca3af;
  font-size: 12px;
  font-weight: 700;
}

.metric-right {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
}

.metric-value {
  margin: 0;
  font-weight: 900;
}

.mini-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}
.mini-dot.ok { background: #22c55e; }
.mini-dot.warn { background: #facc15; }

.sep {
  height: 1px;
  background: #f1f5f9;
  margin-top: 10px;
}

.card-foot {
  margin-top: auto;
  padding: 10px 12px;
  border-top: 1px solid #f1f5f9;
  background: #f8fafc;
  text-align: center;
}

/* ===== Table ===== */
.table-card {
  background: #fff;
  border: 1px solid #e8eff3;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}

.table-head {
  padding: 14px 16px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.table-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.table-title span {
  color: #299de0;
  font-size: 20px;
}

.table-title h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 900;
}

.pill {
  font-size: 12px;
  font-weight: 800;
  color: #507c95;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 6px 10px;
  border-radius: 10px;
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
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
  color: #507c95;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 12px 16px;
  font-weight: 900;
  text-align: left;
}

.table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
}

.table tbody tr:hover {
  background: rgba(248, 250, 252, 0.6);
}

.right { text-align: right; }

.row-strong {
  background: rgba(219, 234, 254, 0.35);
}

.row-neg .right {
  color: #dc2626;
  font-weight: 800;
}

.strong {
  font-weight: 900;
}

.table-foot {
  padding: 10px 12px;
  border-top: 1px solid #f1f5f9;
  background: #f8fafc;
  text-align: center;
}

/* ===== Notes ===== */
.notes-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.note {
  position: relative;
  border-radius: 16px;
  border: 1px solid #dbeafe;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 70%);
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  overflow: hidden;
}

.note-bg {
  position: absolute;
  top: 6px;
  right: 10px;
  opacity: 0.1;
}

.note-bg span {
  font-size: 120px;
  color: #299de0;
}

.note-head {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
  margin-bottom: 10px;
}

.tag {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
}

.tag-blue { background: #dbeafe; color: #299de0; }
.tag-green { background: #dcfce7; color: #15803d; }

.note-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
}

.note-text {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.6;
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

/* ===== Info + footer ===== */
.info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
}

.info span { color: #299de0; }
.info p {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: #299de0;
}

.link-btn {
  color: #299de0;
  font-weight: 900;
  font-size: 12px;
  background: transparent;
}
.link-btn:hover {
  text-decoration: underline;
}

.foot {
  margin: 8px 0 22px;
  text-align: center;
  color: #9ca3af;
  font-weight: 700;
  font-size: 12px;
}
.foot p { margin: 0; }

/* ===== Responsive ===== */
@media (min-width: 640px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 768px) {
  .notes-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) {
  .kpi-grid { grid-template-columns: repeat(4, 1fr); }
  .cards-grid { grid-template-columns: repeat(4, 1fr); }
}
</style>