<script setup>
import { ref, computed, onMounted } from "vue";
import { db } from "@/firebase/config";
import { collection, getDocs } from "firebase/firestore";
import { useRoute, useRouter } from "vue-router";
import { useFinancialAiBlock } from "@/composables/useFinancialAiBlock";

const route = useRoute();
const router = useRouter();
const projectId = route.params.id_proyecto;

const {
  loadAiResult,
  hasBlockData,
  interpretationTitle,
  interpretationParagraphs,
  indicatorsExplained,
  recommendationItems,
  alertItems,
  aiBlockLoading,
  aiBlockError,
} = useFinancialAiBlock("estructura");

const centroDeAprendizaje = () => {
  const routeData = router.resolve({ name: "teoriaEstructura" });
  window.open(routeData.href, "_blank");
};

const kpis = ref([]);
const periodRows = ref([]);
const isLoading = ref(true);

const fallbackInterpretationTitle = "Lectura de estructura financiera";
const fallbackInterpretationParagraphs = [
  "Los indicadores de estructura muestran cómo está financiada la empresa y qué tan equilibrada es la relación entre activos, pasivos y capital propio.",
  "En una empresa de servicios, una estructura sana permite sostener operaciones, invertir en capacidad instalada y responder ante obligaciones sin depender excesivamente de deuda externa.",
];

const fallbackRecommendations = [
  {
    title: "Revisar la composición del capital",
    description:
      "Evaluar si la empresa depende más de capital propio o de pasivos para financiar sus activos.",
    reason:
      "Una estructura demasiado cargada hacia deuda puede limitar la capacidad de crecimiento y aumentar presión de pago.",
    priority: "media",
  },
  {
    title: "Controlar la inmovilización de capital",
    description:
      "Identificar activos fijos que no estén generando suficiente valor operativo o comercial.",
    reason:
      "En servicios, tener demasiados recursos atrapados en activos fijos puede reducir flexibilidad financiera.",
    priority: "media",
  },
  {
    title: "Fortalecer el capital contable",
    description:
      "Priorizar reinversión de utilidades o aportaciones de socios cuando se requiera financiar crecimiento.",
    reason:
      "Un capital contable más sólido mejora el respaldo financiero y reduce dependencia de terceros.",
    priority: "alta",
  },
];

const displayInterpretationTitle = computed(() => {
  return hasBlockData.value ? interpretationTitle.value : fallbackInterpretationTitle;
});

const displayInterpretationParagraphs = computed(() => {
  return interpretationParagraphs.value.length > 0
    ? interpretationParagraphs.value
    : fallbackInterpretationParagraphs;
});

const displayRecommendations = computed(() => {
  return recommendationItems.value.length > 0
    ? recommendationItems.value
    : fallbackRecommendations;
});

const displayAlerts = computed(() => {
  return alertItems.value || [];
});

const formatCurrency = (value) => {
  const numeric = Number(value || 0);

  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numeric);
};

const normalizeKpiValue = (value) => {
  if (
    value === "Sin Deuda LP" ||
    value === "Sin deuda LP" ||
    value === "N/A" ||
    value === null ||
    value === undefined
  ) {
    return "N/A";
  }

  return value;
};

const fetchDashboardData = async () => {
  if (!projectId) return;

  try {
    const periodosRef = collection(db, "proyectos", projectId, "periodos");
    const snapshot = await getDocs(periodosRef);

    const loadedPeriods = [];

    snapshot.forEach((docSnap) => {
      const data = docSnap.data();

      const analisis =
        data.analisis_estructura ||
        data.estructura ||
        null;

      if (!analisis) return;

      const crudos = analisis.datos_crudos || {};

      loadedPeriods.push({
        id: docSnap.id,
        label: data.label || docSnap.id,
        periodDate: data.periodDate || data.label || docSnap.id,
        kpis: analisis.kpis || [],
        row: {
          period: data.label || docSnap.id,
          activoTotal: formatCurrency(crudos.activo_total || 0),
          activoFijo: formatCurrency(crudos.activo_fijo || 0),
          pasivoTotal: formatCurrency(crudos.pasivo_total || 0),
          pasivoFijo: formatCurrency(crudos.pasivo_largo_plazo || 0),
          capitalSocial: formatCurrency(crudos.capital_social || 0),
          capitalContable: formatCurrency(crudos.capital_contable || 0),
        },
      });
    });

    loadedPeriods.sort((a, b) =>
      String(a.periodDate).localeCompare(String(b.periodDate))
    );

    periodRows.value = loadedPeriods.map((p) => p.row);

    const latest = loadedPeriods[loadedPeriods.length - 1];

    if (latest) {
      kpis.value = latest.kpis.map((k) => ({
        label: k.label,
        value: normalizeKpiValue(k.value),
        status: k.status || "gray",
      }));

      console.log("📊 KPIs DE ESTRUCTURA FINANCIERA (MONOPERIODO):", latest.kpis);
    }
  } catch (error) {
    console.error("Error al cargar los datos de estructura financiera:", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadAiResult();
  fetchDashboardData();
});
</script>

<template>
  <div class="wrap">
    <!-- TITULO -->
    <div class="title">
      <div class="title-row">
        <h1>Estructura Financiera</h1>

        <button class="btn-learn" type="button" @click="centroDeAprendizaje">
          <span class="material-symbols-outlined">info</span>
          <span>Ir a centro de aprendizaje</span>
        </button>
      </div>

      <div class="subtitle">
        <p>Diagnóstico de la composición del capital</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">Indicadores calculados a partir del Estado de Situación Financiera</p>
      </div>
    </div>

    <div v-if="isLoading" class="loading">
      Cargando análisis de estructura financiera...
    </div>

    <template v-else>
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
                <th>Periodo</th>
                <th>Activo Total</th>
                <th>Activo Fijo</th>
                <th>Pasivo Total</th>
                <th>Pasivo Fijo LP</th>
                <th>Capital Social</th>
                <th>Capital Contable</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="r in periodRows" :key="r.period">
                <td class="strong">{{ r.period }}</td>
                <td class="muted">{{ r.activoTotal }}</td>
                <td class="muted">{{ r.activoFijo }}</td>
                <td class="muted">{{ r.pasivoTotal }}</td>
                <td class="muted">{{ r.pasivoFijo }}</td>
                <td class="muted">{{ r.capitalSocial }}</td>
                <td>
                  <span class="pill">{{ r.capitalContable }}</span>
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
          Para visualizar gráficas de evolución y comparativas detalladas, añade más periodos a tu análisis.
        </p>
      </div>

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

          <p v-if="aiBlockLoading" class="note-text">
            Generando interpretación automática...
          </p>

          <p v-else-if="aiBlockError" class="note-text">
            No se pudo cargar la interpretación automática. Se muestra una lectura base del sistema.
          </p>

          <div v-else class="ai-content">
            <h4 class="ai-title">{{ displayInterpretationTitle }}</h4>

            <p
              v-for="(paragraph, idx) in displayInterpretationParagraphs"
              :key="`paragraph-${idx}`"
              class="ai-paragraph"
            >
              {{ paragraph }}
            </p>

            <div v-if="indicatorsExplained.length" class="ai-section">
              <h4 class="ai-section-title">Indicadores explicados</h4>

              <div
                v-for="(item, idx) in indicatorsExplained"
                :key="`indicator-${idx}`"
                class="ai-finding"
              >
                <p class="ai-finding-title">
                  {{ item.label }}
                  <span v-if="item.value"> · {{ item.value }}</span>
                </p>

                <p v-if="item.reading" class="ai-finding-meta">
                  {{ item.reading }}
                </p>

                <p v-if="item.meaning" class="ai-finding-text">
                  {{ item.meaning }}
                </p>

                <p v-if="item.serviceBusinessImplication" class="ai-impact">
                  {{ item.serviceBusinessImplication }}
                </p>

                <p v-if="item.possibleImpact" class="ai-impact">
                  {{ item.possibleImpact }}
                </p>
              </div>
            </div>

            <div v-if="displayAlerts.length" class="ai-section">
              <h4 class="ai-section-title">Alertas del bloque</h4>

              <div
                v-for="(alert, idx) in displayAlerts"
                :key="`alert-${idx}`"
                class="ai-alert"
                :class="`severity-${alert.severity}`"
              >
                <p class="ai-finding-title">{{ alert.title }}</p>

                <p v-if="alert.message" class="ai-finding-text">
                  {{ alert.message }}
                </p>

                <p v-if="alert.implication" class="ai-impact">
                  {{ alert.implication }}
                </p>

                <p v-if="alert.evidence" class="ai-evidence">
                  {{ alert.evidence }}
                </p>
              </div>
            </div>
          </div>
        </article>

        <article class="note note-ok">
          <div class="note-head">
            <span class="tag tag-green">
              <span class="material-symbols-outlined">checklist</span>
            </span>
            <h3>Recomendaciones</h3>
          </div>

          <ul class="list">
            <li v-if="aiBlockLoading">
              <span class="material-symbols-outlined">hourglass_empty</span>
              <span>Generando recomendaciones...</span>
            </li>

            <li v-else v-for="(item, idx) in displayRecommendations" :key="idx">
              <span class="material-symbols-outlined">check_circle</span>

              <span class="recommendation-content">
                <strong>{{ item.title }}</strong>
                <small v-if="item.description">{{ item.description }}</small>
                <em v-if="item.reason">{{ item.reason }}</em>
              </span>
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
    </template>
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
  color: #0e161b;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
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

.loading {
  padding: 40px;
  text-align: center;
  color: #507c95;
  font-weight: 800;
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

.kpi-dot.danger,
.kpi-dot.alert,
.kpi-dot.bad {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

.kpi-dot.gray {
  background: #9ca3af;
}

.kpi-value {
  font-size: 24px;
  font-weight: 900;
  margin-top: 10px;
}

/* PANEL + TABLE */
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
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 920px;
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

/* INTERPRETACION + RECS */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  align-items: start;
}

.note {
  position: relative;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 70%);
  border: 1px solid #dbeafe;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.note-ok {
  background: #ffffff;
  border-color: #e8eff3;
  align-self: start;
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
  flex: 0 0 auto;
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

/* IA */
.ai-content {
  display: grid;
  gap: 14px;
  position: relative;
  z-index: 1;
}

.ai-title {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.ai-paragraph {
  margin: 0;
  color: #0e161b;
  font-size: 14px;
  font-weight: 650;
  line-height: 1.65;
}

.ai-section {
  display: grid;
  gap: 10px;
  margin-top: 4px;
}

.ai-section-title {
  margin: 0;
  color: #507c95;
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.ai-finding,
.ai-alert {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid #dbeafe;
}

.ai-finding-title {
  margin: 0 0 4px;
  color: #0e161b;
  font-size: 14px;
  font-weight: 900;
}

.ai-finding-meta {
  margin: 0 0 6px;
  color: #507c95;
  font-size: 12px;
  font-weight: 800;
}

.ai-finding-text,
.ai-impact,
.ai-evidence {
  margin: 0;
  color: #0e161b;
  font-size: 13px;
  font-weight: 650;
  line-height: 1.55;
}

.ai-impact {
  margin-top: 6px;
  color: #334155;
}

.ai-evidence {
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
}

.ai-alert.severity-alta {
  border-color: #fecaca;
  background: #fff7f7;
}

.ai-alert.severity-media {
  border-color: #fde68a;
  background: #fffdf2;
}

.ai-alert.severity-baja {
  border-color: #bfdbfe;
  background: #f8fbff;
}

/* LIST */
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
  flex: 0 0 auto;
}

.recommendation-content {
  display: grid;
  gap: 3px;
}

.recommendation-content strong {
  font-size: 13px;
  font-weight: 900;
  color: #0e161b;
}

.recommendation-content small {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  line-height: 1.45;
}

.recommendation-content em {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  font-style: normal;
  line-height: 1.4;
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
    grid-template-columns: repeat(4, 1fr);
  }

  .grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>