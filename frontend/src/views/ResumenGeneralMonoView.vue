<script setup>
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { collection, getDocs } from "firebase/firestore"; 
import { db } from "@/firebase/config"; 

const router = useRouter();
const route = useRoute();

const loading = ref(true);
const projectId = ref(null);

// Formateadores
const currencyFmt = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2, maximumFractionDigits: 2 });
const percentFmt = new Intl.NumberFormat('es-MX', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 2 });

// ===== ESTADO REACTIVO =====
const kpis = ref([
  { label: "Ingresos Totales", value: "$0", status: "gray" },
  { label: "Utilidad Neta", value: "$0", status: "gray" },
  { label: "Margen Neto", value: "0%", status: "gray" },
  { label: "Liquidez General", value: "0.0", status: "gray" },
]);

const cards = ref([
  { title: "Rentabilidad", icon: "trending_up", detailRoute: "rentabilidad", items: [] },
  { title: "Liquidez", icon: "attach_money", detailRoute: "liquidez", items: [] },
  { title: "Endeudamiento", icon: "account_balance_wallet", detailRoute: "endeudamiento", items: [] },
  { title: "Estructura Financiera", icon: "layers", detailRoute: "estructura", items: [] },
]);

const edoResultados = ref([]);
const periodLabel = ref(""); 
const interpretation = ref("Cargando datos...");

// ===== LÓGICA DE CARGA DE DATOS =====
const fetchDashboardData = async () => {
  try {
    projectId.value = route.params.id_proyecto; 
    
    if (!projectId.value) {
        console.error("Falta ID Proyecto");
        return;
    }

    const periodosRef = collection(db, "proyectos", projectId.value, "periodos");
    const snapshot = await getDocs(periodosRef);

    let data_list = [];

    snapshot.forEach((docSnap) => {
      const pData = docSnap.data();
      // Validamos si guardaste como 'rentabilidad' o 'analisis_rentabilidad'
      if (pData.rentabilidad || pData.analisis_rentabilidad) {
         data_list.push({
            id: docSnap.id,
            label: pData.label || docSnap.id,
            data: pData
         });
      }
    });

    if (data_list.length > 0) {
      // Ordenar alfabéticamente por label y tomar el último
      data_list.sort((a, b) => a.label.localeCompare(b.label));
      const latest = data_list[data_list.length - 1];
      const d = latest.data;

      // Unificamos estructura (Backend -> Frontend)
      const dashboardData = {
        rentabilidad: d.rentabilidad || d.analisis_rentabilidad || {},
        liquidez: d.liquidez || d.analisis_liquidez || {},
        endeudamiento: d.endeudamiento || d.analisis_endeudamiento || {},
        estructura: d.estructura || d.analisis_estructura || {},
        rotacion: d.rotacion || d.analisis_rotacion || {},
        periodo: latest.label
      };

      mapDataToDashboard(dashboardData);
      periodLabel.value = dashboardData.periodo ? `Periodo: ${dashboardData.periodo}` : 'Periodo Actual';
    } else {
        interpretation.value = "No hay análisis disponibles.";
    }
  } catch (error) {
    console.error("Error cargando dashboard:", error);
    interpretation.value = "Error de conexión.";
  } finally {
    loading.value = false;
  }
};

// ===== MAPEO DE DATOS =====
const mapDataToDashboard = (data) => {
  // Inicializamos objetos vacíos si falla la carga parcial
  const rent = data.rentabilidad || { datos_crudos: {}, kpis: [] };
  const liq = data.liquidez || { datos_crudos: {}, kpis: [] };
  const end = data.endeudamiento || { datos_crudos: {}, kpis: [] };
  const est = data.estructura || { datos_crudos: {}, kpis: [] };
  const rot = data.rotacion || { datos_crudos: {} };

  // --- 1. EXTRACCIÓN DE DATOS CRUDOS ---
  // Estos nombres vienen DIRECTO de tu Python (return "datos_crudos": {...})
  
  // Python: "ventas_netas" en calcular_rentabilidad
  const ventas = rent.datos_crudos?.ventas_netas || 0;
  
  // Python: "utilidad_neta" en calcular_rentabilidad
  const ut_neta = rent.datos_crudos?.utilidad_neta || 0;
  
  // Python: "costo_ventas" en calcular_rotacion
  const costo = rot.datos_crudos?.costo_ventas || 0; 
  
  // Python: "utilidad_operacion" en calcular_endeudamiento
  const ut_operacion = end.datos_crudos?.utilidad_operacion || 0;
  
  // Cálculos derivados para la tabla visual
  const ut_bruta = ventas - costo;
  const gastos_op = ut_bruta - ut_operacion;

  // --- 2. KPIS PRINCIPALES (TOP BAR) ---
  kpis.value = [
    { label: "Ingresos Totales", value: currencyFmt.format(ventas), status: ventas > 0 ? "ok" : "warn" },
    { label: "Utilidad Neta", value: currencyFmt.format(ut_neta), status: ut_neta > 0 ? "ok" : "warn" },
    { label: "Margen Neto", value: percentFmt.format(ventas ? ut_neta / ventas : 0), status: (ventas && (ut_neta/ventas) > 0.10) ? "ok" : "warn" },
    
    // CORRECCIÓN: Python emite "Razón de Liquidez"
    { 
      label: "Liquidez General", 
      value: findKpiValue(liq.kpis, "Razón de Liquidez") || "0.0", 
      status: isStatusOk(liq.kpis, "Razón de Liquidez") ? "ok" : "warn" 
    },
  ];

  // --- 3. TARJETAS (MAPPING EXACTO CON PYTHON) ---
  
  // A) Rentabilidad
  cards.value[0].items = [
    // Python label: "Rendimiento sobre el Patrimonio"
    { label: "ROE", target: ">10%", value: findKpiValue(rent.kpis, "Patrimonio") || "-", dot: getDotColor(rent.kpis, "Patrimonio") },
    // Python label: "Margen de Rentabilidad"
    { label: "Margen Neto", target: ">10%", value: findKpiValue(rent.kpis, "Margen de Rentabilidad") || "-", dot: getDotColor(rent.kpis, "Margen de Rentabilidad") },
  ];

  // B) Liquidez
  cards.value[1].items = [
    // Python label: "Prueba del Ácido"
    { label: "Prueba Ácida", target: ">0.8", value: findKpiValue(liq.kpis, "Prueba del Ácido") || "-", dot: getDotColor(liq.kpis, "Prueba del Ácido") },
    // Python label: "Capital de Trabajo"
    { label: "Cap. Trabajo", target: "> $0", value: findKpiValue(liq.kpis, "Capital de Trabajo") || "-", dot: getDotColor(liq.kpis, "Capital de Trabajo") },
  ];

  // C) Endeudamiento
  cards.value[2].items = [
    // Python label: "Apalancamiento" (NO es "Nivel Deuda")
    { label: "Nivel Deuda", target: "<0.5", value: findKpiValue(end.kpis, "Apalancamiento") || "-", dot: getDotColor(end.kpis, "Apalancamiento") },
    // Python label: "Razón de Cobertura de Intereses"
    { label: "Cobertura Int.", target: ">1.5x", value: findKpiValue(end.kpis, "Cobertura de Intereses") || "-", dot: getDotColor(end.kpis, "Cobertura de Intereses") },
  ];

  // D) Estructura
  cards.value[3].items = [
    // Python label: "Solvencia General"
    { label: "Solvencia", target: ">1.0", value: findKpiValue(est.kpis, "Solvencia General") || "-", dot: getDotColor(est.kpis, "Solvencia General") },
    // Python label: "Seguridad a largo plazo"
    { label: "Seguridad LP", target: ">=1.0", value: findKpiValue(est.kpis, "Seguridad a largo plazo") || "-", dot: getDotColor(est.kpis, "Seguridad a largo plazo") },
  ];

  // --- 4. TABLA ESTADO DE RESULTADOS ---
  edoResultados.value = [
    { concept: "Ventas Netas", value: currencyFmt.format(ventas), pct: "100%", tone: "normal" },
    { concept: "Costo de Ventas", value: currencyFmt.format(costo), pct: calcPct(costo, ventas), tone: "neg" },
    { concept: "Utilidad Bruta", value: currencyFmt.format(ut_bruta), pct: calcPct(ut_bruta, ventas), tone: "strong" },
    { concept: "Gastos Operación", value: currencyFmt.format(gastos_op), pct: calcPct(gastos_op, ventas), tone: "neg" },
    { concept: "Utilidad Operación", value: currencyFmt.format(ut_operacion), pct: calcPct(ut_operacion, ventas), tone: "strong" },
    { concept: "Utilidad Neta", value: currencyFmt.format(ut_neta), pct: calcPct(ut_neta, ventas), tone: "strong" },
  ];

  interpretation.value = ut_neta > 0 
    ? "La empresa genera utilidades netas positivas." 
    : "La empresa reporta pérdidas o faltan datos.";
};

// ===== FUNCIONES AUXILIARES =====
const findKpiValue = (list, labelPart) => {
    if (!list) return null;
    // Buscamos si la etiqueta del backend INCLUYE el texto que le pasamos
    const item = list.find(k => k.label.toLowerCase().includes(labelPart.toLowerCase()));
    return item ? item.value : null;
};

const getDotColor = (list, labelPart) => {
    if (!list) return "gray";
    const item = list.find(k => k.label.toLowerCase().includes(labelPart.toLowerCase()));
    if (!item) return "gray";
    return item.status === 'ok' ? 'ok' : 'warn';
};

const isStatusOk = (list, labelPart) => {
    return getDotColor(list, labelPart) === 'ok';
};

const calcPct = (val, total) => {
    if (!total) return "0%";
    return ((val / total) * 100).toFixed(1) + "%";
};

function goDetail(routeName) {
  if (!projectId.value) return;
  router.push({ name: routeName, params: { id_proyecto: projectId.value } });
}

onMounted(() => {
    fetchDashboardData();
});
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
        <span class="pill" v-if="periodLabel">{{ periodLabel }}</span>
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

/* Para el punto grande del KPI */
.kpi-dot.warn {
  background: #facc15; /* Amarillo alerta */
  box-shadow: 0 0 8px rgba(250, 204, 21, 0.4);
}
.kpi-dot.alert { /* Por si decides usar rojo */
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}
.kpi-dot.gray {
  background: #9ca3af; /* Gris mientras carga */
}

/* Para el punto pequeño de las listas */
.mini-dot.gray { background: #9ca3af; }
.mini-dot.alert { background: #ef4444; }

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