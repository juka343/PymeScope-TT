<script setup>
import { ref, onMounted } from "vue";
import { db } from "@/firebase/config";
import { collection, getDocs } from "firebase/firestore";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const projectId = route.params.id_proyecto;

const centroDeAprendizaje = () => {
  const routeData = router.resolve({ name: "teoriaRentabilidad" });
  window.open(routeData.href, "_blank");
};

// Estado de carga
const isLoading = ref(true);

// Variables reactivas (ahora empiezan vacías)
const kpis = ref([]);
const periodRows = ref([]);

// Las recomendaciones siguen estáticas por ahora (se pueden hacer dinámicas después)
const recommendations = ref([
  "Control de costos operativos",
  "Revisión de estrategia de precios",
  "Optimización de procesos internos",
]);

// Función auxiliar para darle formato de dinero a los números (ej. 1500000 -> $1,500,000)
const formatCurrency = (value) => {
  if (value === undefined || value === null) return "$0";
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(value);
};

const fetchDashboardData = async () => {
  if (!projectId) return;

  try {
    // 1. Ir a la subcolección de periodos del proyecto actual
    const periodosRef = collection(db, "proyectos", projectId, "periodos");
    const snapshot = await getDocs(periodosRef);

    const rowsTemp = [];
    let ultimosKpis = null;

    // 2. Recorrer todos los periodos que encontremos
    snapshot.forEach((docSnap) => {
      const data = docSnap.data();
      
      // Si el periodo ya tiene un análisis guardado...
      if (data.analisis_rentabilidad) {
        const analisis = data.analisis_rentabilidad;
        const crudos = analisis.datos_crudos;

        // Guardamos los KPIs más recientes para las tarjetas superiores
        ultimosKpis = analisis.kpis;

        // ====== LOG PARA DEMOSTRAR LOS DATOS MONOPERIODO A LA IA ======
        console.log("📊 KPIs DE RENTABILIDAD (MONOPERIODO):", analisis.kpis);
        // =============================================================

        // Armamos la fila para la tabla inferior
        rowsTemp.push({
          period: data.label || docSnap.id,
          ingresos: formatCurrency(crudos.ventas_netas),
          utilidad: formatCurrency(crudos.utilidad_neta),
          margen: analisis.kpis.find(k => k.label === "Margen de Rentabilidad")?.value || "0%"
        });
      }
    });

    // 3. Ordenar la tabla (opcional: asume que la etiqueta es "Periodo 1", "Periodo 2")
    rowsTemp.sort((a, b) => a.period.localeCompare(b.period));

    // 4. Asignar los datos a las variables que usa el HTML
    if (ultimosKpis) {
      kpis.value = ultimosKpis;
    }
    periodRows.value = rowsTemp;

  } catch (error) {
    console.error("Error al cargar los datos del dashboard:", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchDashboardData();
});
</script>

<template>
  <div class="wrap">
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