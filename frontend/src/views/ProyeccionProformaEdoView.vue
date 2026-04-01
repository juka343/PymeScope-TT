<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const headerInfo = ref({
  generatedPeriod: "Q4 2024",
  basePeriod: "Q3 2024",
  title: "Proyección Proforma - Estado de Resultados",
  subtitle:
    "Visualiza la proyección del estado de resultados generada a partir del último periodo registrado y los supuestos definidos.",
});

const kpis = ref([
  {
    title: "Ingresos proyectados",
    value: "$4,250,000",
    delta: "+12.4%",
    note: "vs periodo base",
    featured: false,
  },
  {
    title: "Utilidad operativa",
    value: "$1,105,000",
    delta: "+8.2%",
    note: "vs periodo base",
    featured: false,
  },
  {
    title: "Utilidad neta proyectada",
    value: "$843,597",
    delta: "+15.1%",
    note: "vs periodo base",
    featured: true,
  },
  {
    title: "Margen neto proyectado",
    value: "19.8%",
    delta: "+15.1%",
    note: "vs periodo base",
    featured: false,
  },
]);

const projectionRows = ref([
  { type: "section", label: "Ingresos" },
  {
    type: "row",
    concept: "Ventas netas / Ingresos por servicios",
    conceptTone: "default",
    base: "$3,500,000",
    assumption: "+12.4%",
    assumptionTone: "primary",
    participation: "92.6%",
    proforma: "$3,934,000",
    variation: "+12.4%",
    variationTone: "up",
  },
  {
    type: "row",
    concept: "Otros ingresos",
    conceptTone: "default",
    base: "$200,000",
    assumption: "Mantener igual",
    assumptionTone: "muted",
    participation: "4.7%",
    proforma: "$200,000",
    variation: "0.0%",
    variationTone: "neutral",
  },
  {
    type: "row",
    concept: "Productos financieros",
    conceptTone: "default",
    base: "$80,000",
    assumption: "+45.0%",
    assumptionTone: "primary",
    participation: "2.7%",
    proforma: "$116,000",
    variation: "+45.0%",
    variationTone: "up",
  },
  {
    type: "subtotal",
    concept: "Total de ingresos",
    base: "$3,780,000",
    assumption: "Calculado automáticamente",
    assumptionTone: "italic",
    participation: "100.0%",
    proforma: "$4,250,000",
    variation: "+12.4%",
    variationTone: "up",
  },

  { type: "section", label: "Costos y gastos" },
  {
    type: "row",
    concept: "Costo de ventas / Costo por servicios",
    conceptTone: "muted",
    base: "($2,268,000)",
    assumption: "+12.4%",
    assumptionTone: "primary",
    participation: "60.0%",
    proforma: "($2,550,000)",
    variation: "+12.4%",
    variationTone: "down",
  },
  {
    type: "subtotal",
    concept: "Utilidad bruta",
    base: "$1,512,000",
    assumption: "Calculado automáticamente",
    assumptionTone: "italic",
    participation: "40.0%",
    proforma: "$1,700,000",
    variation: "+12.4%",
    variationTone: "up",
  },
  {
    type: "row",
    concept: "Gastos de venta",
    conceptTone: "muted",
    base: "($150,000)",
    assumption: "+8.0%",
    assumptionTone: "primary",
    participation: "3.8%",
    proforma: "($162,000)",
    variation: "+8.0%",
    variationTone: "down",
  },
  {
    type: "row",
    concept: "Gastos de administración",
    conceptTone: "muted",
    base: "($120,000)",
    assumption: "+5.0%",
    assumptionTone: "primary",
    participation: "3.0%",
    proforma: "($126,000)",
    variation: "+5.0%",
    variationTone: "down",
  },
  {
    type: "row",
    concept: "Gastos de nómina",
    conceptTone: "muted",
    base: "($221,400)",
    assumption: "+38.7%",
    assumptionTone: "primary",
    participation: "7.2%",
    proforma: "($307,000)",
    variation: "+38.7%",
    variationTone: "down",
  },
  {
    type: "row",
    concept: "Gastos financieros",
    conceptTone: "muted",
    base: "($120,000)",
    assumption: "Mantener igual",
    assumptionTone: "muted",
    participation: "2.8%",
    proforma: "($120,000)",
    variation: "0.0%",
    variationTone: "neutral",
  },
  {
    type: "row",
    concept: "Otros gastos",
    conceptTone: "muted",
    base: "$0",
    assumption: "Mantener igual",
    assumptionTone: "muted",
    participation: "0.0%",
    proforma: "$0",
    variation: "—",
    variationTone: "neutral",
  },
  {
    type: "subtotal",
    concept: "Utilidad de operación",
    base: "$900,600",
    assumption: "Calculado automáticamente",
    assumptionTone: "italic",
    participation: "23.2%",
    proforma: "$985,000",
    variation: "+9.4%",
    variationTone: "up",
    highlightValue: true,
  },
  {
    type: "subtotal",
    concept: "Utilidad antes de impuestos",
    base: "$1,020,600",
    assumption: "Calculado automáticamente",
    assumptionTone: "italic",
    participation: "26.0%",
    proforma: "$1,105,000",
    variation: "+8.2%",
    variationTone: "up",
    highlightValue: true,
  },

  { type: "section", label: "Impuestos" },
  {
    type: "row",
    concept: "ISR",
    conceptTone: "muted",
    base: "($270,180)",
    assumption: "+9.3%",
    assumptionTone: "primary",
    participation: "7.0%",
    proforma: "($295,500)",
    variation: "+9.3%",
    variationTone: "down",
  },
  {
    type: "row",
    concept: "PTU",
    conceptTone: "muted",
    base: "($17,568)",
    assumption: "+5.2%",
    assumptionTone: "primary",
    participation: "0.4%",
    proforma: "($18,482)",
    variation: "+5.2%",
    variationTone: "down",
  },
  {
    type: "final",
    concept: "Utilidad neta del ejercicio",
    base: "$732,852",
    assumption: "Calculado automáticamente",
    assumptionTone: "final-muted",
    participation: "19.8%",
    proforma: "$843,597",
    variation: "+15.1%",
    variationTone: "final-up",
  },
]);

const interpretationPoints = ref([
  "El incremento del 12.4% en ingresos compensa el aumento en gastos operativos, resultando en una expansión del margen operativo.",
  "La optimización de la estructura de costos permite que la utilidad neta crezca a un ritmo superior (+15.1%) que las ventas.",
  "Los niveles de impuestos proyectados mantienen la proporcionalidad histórica esperada.",
]);

function assumptionClass(tone) {
  return {
    "assumption-primary": tone === "primary",
    "assumption-muted": tone === "muted",
    "assumption-italic": tone === "italic",
    "assumption-final-muted": tone === "final-muted",
  };
}

function conceptClass(tone) {
  return {
    "concept-default": tone === "default",
    "concept-muted": tone === "muted",
  };
}

function variationClass(tone) {
  return {
    "variation-up-span": tone === "up",
    "variation-down-span": tone === "down",
    "variation-neutral-span": tone === "neutral",
    "variation-final-up-span": tone === "final-up",
  };
}

function exportProjection() {
  // Placeholder
}

function continueToBalance() {
  router.push({ name: "FormularioBalanceGeneral" });
}
</script>

<template>
  <div class="wrap">
    <section class="page-head">
      <div class="page-badges">
        <span class="mini-badge mini-badge-blue">
          PROYECCIÓN GENERADA: {{ headerInfo.generatedPeriod }}
        </span>
        <span class="mini-badge mini-badge-gray">
          PERIOD BASE: {{ headerInfo.basePeriod }}
        </span>
      </div>

      <h1>{{ headerInfo.title }}</h1>
      <p class="page-description">{{ headerInfo.subtitle }}</p>
    </section>

    <section class="kpis">
      <article
        v-for="(kpi, idx) in kpis"
        :key="idx"
        class="kpi-card"
        :class="{ featured: kpi.featured }"
      >
        <div class="kpi-top">
          <p class="kpi-title" :class="{ 'kpi-title-featured': kpi.featured }">
            {{ kpi.title }}
          </p>
        </div>

        <div class="kpi-value-row">
          <p class="kpi-value">{{ kpi.value }}</p>
        </div>

        <div class="kpi-bottom">
          <template v-if="kpi.delta">
            <span class="kpi-chip">
              <span class="material-symbols-outlined">trending_up</span>
              {{ kpi.delta }}
            </span>
            <span class="kpi-note">{{ kpi.note }}</span>
          </template>

          <template v-else>
            <span class="kpi-chip">
              <span class="material-symbols-outlined">trending_up</span>
              {{ kpi.delta }}
            </span>
            <span v-if="kpi.noteSecondary" class="kpi-note">{{ kpi.noteSecondary }}</span>
          </template>
        </div>
      </article>
    </section>

    <section class="table-card">
      <div class="table-head">
        <h3>Estado de Resultados Proforma</h3>
        
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Concepto</th>
              <th class="right">Periodo base (Q3)</th>
              <th>Supuesto aplicado</th>
              <th class="right">Participación %</th>
              <th class="right">Proyección proforma</th>
              <th class="right">Variación</th>
            </tr>
          </thead>

          <tbody>
            <template v-for="(row, idx) in projectionRows" :key="idx">
              <tr v-if="row.type === 'section'" class="section-row">
                <td colspan="6">{{ row.label }}</td>
              </tr>

              <tr
                v-else
                :class="{
                  'subtotal-row': row.type === 'subtotal',
                  'final-row': row.type === 'final',
                }"
              >
                <td :class="conceptClass(row.conceptTone)">{{ row.concept }}</td>
                <td class="right" :class="{ strong: row.type !== 'row' }">{{ row.base }}</td>
                <td :class="assumptionClass(row.assumptionTone)">{{ row.assumption }}</td>
                <td class="right" :class="{ strong: row.type !== 'row' || row.highlightValue }">
                  {{ row.participation }}
                </td>
                <td
                  class="right"
                  :class="{
                    strong: row.type !== 'row' || row.highlightValue,
                    'proforma-highlight': row.highlightValue && row.type === 'subtotal',
                  }"
                >
                  {{ row.proforma }}
                </td>
                <td class="right">
                  <span :class="variationClass(row.variationTone)">
                    {{ row.variation }}
                  </span>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid-2">
      <article class="info-card">
        <div class="info-head">
          <div class="info-icon">
            <span class="material-symbols-outlined">info</span>
          </div>
          <h4>Interpretación de la proyección</h4>
        </div>

        <ul class="info-list">
          <li v-for="(item, idx) in interpretationPoints" :key="idx">
            <span class="bullet">•</span>
            <span>{{ item }}</span>
          </li>
        </ul>

        <span class="info-bg material-symbols-outlined">lightbulb</span>
      </article>

      <article class="next-card">
        <div class="next-head">
          <div class="next-icon">
            <span class="material-symbols-outlined">arrow_forward</span>
          </div>
          <h4>Siguiente paso: Balance General Proforma</h4>
        </div>

        <p>
          La <strong>Utilidad neta proyectada de $843,597</strong> se integrará
          automáticamente en la sección de Capital Contable del Balance General
          Proforma.
        </p>

        <div class="next-status">
          <span>Listo para procesar</span>
          <div class="pulse-dot"></div>
        </div>
      </article>
    </section>

    <section class="actions">
      <div class="actions-spacer"></div>

      <div class="actions-buttons">
        <button class="btn-secondary" type="button" @click="exportProjection">
          Exportar proyección
        </button>
        <button class="btn-primary" type="button" @click="continueToBalance">
          Continuar al Balance
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.wrap {
  width: min(1200px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Header */
.page-head {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 22px;
  border-bottom: 1px solid #e8eff3;
}

.page-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.mini-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.mini-badge-blue {
  background: #eff6ff;
  color: #299de0;
  border: 1px solid #dbeafe;
}

.mini-badge-gray {
  background: #f3f4f6;
  color: #507c95;
}

.page-head h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
}

.page-description {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

/* KPIs */
.kpis {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.kpi-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.kpi-card:hover {
  border-color: rgba(41, 157, 224, 0.35);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.kpi-card.featured {
  border: 2px solid #299de0;
  background: rgba(239, 246, 255, 0.75);
  box-shadow: 0 8px 18px rgba(41, 157, 224, 0.1);
}

.kpi-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.kpi-title {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  font-weight: 700;
}

.kpi-title-featured {
  color: #299de0;
  font-weight: 900;
}

.kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 2px;
}

.kpi-value {
  margin: 0;
  font-size: 30px;
  font-weight: 900;
  line-height: 1.1;
  color: #0e161b;
}

.kpi-bottom {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.kpi-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 8px;
  background: #dcfce7;
  color: #078836;
  font-size: 12px;
  font-weight: 900;
}

.kpi-chip .material-symbols-outlined {
  font-size: 14px;
}

.kpi-note {
  color: #507c95;
  font-size: 12px;
  font-weight: 700;
}

.kpi-note-italic {
  font-style: italic;
  font-weight: 600;
}

/* Table card */
.table-card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 20px;
  background: rgba(249, 250, 251, 0.7);
  border-bottom: 1px solid #e8eff3;
}

.table-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.table-export {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  color: #299de0;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.table-export:hover {
  color: #1a8ac7;
}

.table-export .material-symbols-outlined {
  font-size: 16px;
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  min-width: 1100px;
  border-collapse: collapse;
}

.table thead th {
  padding: 14px 20px;
  border-bottom: 1px solid #e8eff3;
  background: #f9fafb;
  color: #507c95;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  text-align: left;
}

.table td {
  padding: 14px 20px;
  border-bottom: 1px solid #e8eff3;
  font-size: 14px;
  color: #0e161b;
  vertical-align: middle;
}

.table .right {
  text-align: right;
}

.table tbody tr:hover {
  background: rgba(249, 250, 251, 0.35);
}

.section-row td {
  padding: 10px 20px;
  background: rgba(249, 250, 251, 0.6);
  color: #299de0;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.concept-default {
  color: #0e161b;
}

.concept-muted {
  color: #507c95;
}

.assumption-primary {
  color: #299de0;
  font-weight: 700;
}

.assumption-muted {
  color: #6b7280;
}

.assumption-italic {
  color: #6b7280;
  font-style: italic;
}

.assumption-final-muted {
  color: #9ca3af;
  font-style: italic;
}

.strong {
  font-weight: 900;
}

.proforma-highlight {
  color: #299de0;
}

.subtotal-row td {
  background: rgba(239, 246, 255, 0.65);
  font-weight: 800;
}

.subtotal-row td:first-child {
  font-style: italic;
  color: #0e161b;
}

.final-row td {
  background: #111827;
  color: #ffffff;
  border-bottom: none;
  font-weight: 800;
}

.final-row td:first-child {
  text-transform: uppercase;
  letter-spacing: 0.03em;
  font-weight: 900;
}

/* Variations */
.variation-up-span {
  color: #059669;
  font-weight: 800;
}

.variation-down-span {
  color: #ef4444;
  font-weight: 800;
}

.variation-neutral-span {
  color: #9ca3af;
  font-weight: 700;
}

.variation-final-up-span {
  color: #34d399;
  font-weight: 900;
}

.final-row .variation-up-span,
.final-row .variation-down-span,
.final-row .variation-neutral-span {
  color: #34d399;
  font-weight: 900;
}

/* Bottom cards */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
}

.info-card,
.next-card {
  position: relative;
  border-radius: 14px;
  padding: 22px;
  overflow: hidden;
}

.info-card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.next-card {
  background: rgba(239, 246, 255, 0.55);
  border: 2px dashed #299de0;
}

.info-head,
.next-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.info-head h4,
.next-head h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.info-icon,
.next-icon {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.info-icon {
  background: #eff6ff;
  color: #299de0;
}

.next-icon {
  background: #299de0;
  color: #ffffff;
}

.info-icon .material-symbols-outlined,
.next-icon .material-symbols-outlined {
  font-size: 16px;
}

.info-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 12px;
}

.info-list li {
  display: flex;
  gap: 10px;
  color: #507c95;
  font-size: 14px;
  line-height: 1.6;
}

.bullet {
  color: #299de0;
  font-size: 14px;
  font-weight: 900;
  margin-top: 2px;
}

.info-bg {
  position: absolute;
  right: -10px;
  bottom: -12px;
  font-size: 82px;
  opacity: 0.05;
  color: #299de0;
}

.next-card p {
  margin: 0;
  color: #507c95;
  font-size: 14px;
  line-height: 1.65;
}

.next-status {
  margin-top: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #299de0;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #299de0;
  animation: pulse 1.4s infinite;
}

/* Actions */
.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 20px;
}

.actions-spacer {
  min-height: 1px;
}

.actions-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-secondary,
.btn-primary {
  border-radius: 10px;
  font-size: 14px;
  font-weight: 800;
  padding: 12px 18px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.05s ease;
}

.btn-secondary {
  border: 1px solid #d1dee6;
  background: #ffffff;
  color: #0e161b;
}

.btn-secondary:hover {
  background: #f8fafb;
}

.btn-primary {
  border: 1px solid #299de0;
  background: #299de0;
  color: #ffffff;
  letter-spacing: 0.05em;
  box-shadow: 0 6px 14px rgba(41, 157, 224, 0.24);
}

.btn-primary:hover {
  background: #1a8ac7;
  border-color: #1a8ac7;
}

.btn-primary:active,
.btn-secondary:active {
  transform: translateY(1px);
}

/* Responsive */
@media (min-width: 768px) {
  .kpis {
    grid-template-columns: repeat(2, 1fr);
  }

  .actions {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .actions-buttons {
    flex-direction: row;
    width: auto;
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

@keyframes pulse {
  0% {
    opacity: 0.35;
    transform: scale(0.9);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
  100% {
    opacity: 0.35;
    transform: scale(0.9);
  }
}
</style>