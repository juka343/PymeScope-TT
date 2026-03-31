<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

function goToFormularioBalanceGeneral() {
  router.push({ name: "FormularioBalanceGeneral" });
}
const projectionMeta = ref({
  periodoProyectado: "Q4 2024",
  periodoBase: "Q3 2024",
  titulo: "Proyección Proforma - Estado de Resultados",
  descripcion:
    "Visualiza la proyección del estado de resultados generada a partir del último periodo registrado y los supuestos definidos.",
});

const kpis = ref([
  {
    title: "Ingresos proyectados",
    value: "$4,250,000",
    status: "ok",
    delta: "+12.4%",
    note: "vs periodo base",
    featured: false,
  },
  {
    title: "Utilidad operativa",
    value: "$1,105,000",
    status: "ok",
    delta: "+8.2%",
    note: "vs periodo base",
    featured: false,
  },
  {
    title: "Utilidad neta proyectada",
    value: "$843,597",
    status: "ok",
    delta: "+15.1%",
    note: "vs periodo base",
    featured: true,
  },
  {
    title: "Margen neto proyectado",
    value: "19.8%",
    status: "ok",
    delta: "",
    note: "Utilidad neta / Ingresos",
    featured: false,
    plainNote: true,
  },
]);

const statementRows = ref([
  {
    concept: "Total de ingresos",
    base: "$3,780,000",
    assumption: "Crecimiento ventas +12.4%",
    proforma: "$4,250,000",
    variation: "+12.4%",
    kind: "main",
  },
  {
    concept: "Costo de ventas",
    base: "($2,268,000)",
    assumption: "60% de los ingresos",
    proforma: "($2,550,000)",
    variation: "+12.4%",
    kind: "normal-negative",
  },
  {
    concept: "Utilidad bruta",
    base: "$1,512,000",
    assumption: "—",
    proforma: "$1,700,000",
    variation: "+12.4%",
    kind: "subtotal",
  },
  {
    concept: "Gastos de operación",
    base: "($491,400)",
    assumption: "Incremento fijo +21%",
    proforma: "($595,000)",
    variation: "+21.0%",
    kind: "normal-negative",
  },
  {
    concept: "Utilidad de operación",
    base: "$1,020,600",
    assumption: "—",
    proforma: "$1,105,000",
    variation: "+8.2%",
    kind: "featured",
  },
  {
    concept: "Gastos financieros",
    base: "($120,000)",
    assumption: "Sin cambios",
    proforma: "($120,000)",
    variation: "0.0%",
    kind: "neutral",
  },
  {
    concept: "Impuestos (30%)",
    base: "($270,180)",
    assumption: "Tasa impositiva 30%",
    proforma: "($295,500)",
    variation: "+9.3%",
    kind: "normal-negative",
  },
  {
    concept: "Utilidad neta del ejercicio",
    base: "$732,852",
    assumption: "Resultado final proyectado",
    proforma: "$843,597",
    variation: "+15.1%",
    kind: "final",
  },
]);

const interpretationPoints = ref([
  "El incremento del 12.4% en ingresos compensa el aumento en gastos operativos, resultando en una expansión del margen operativo.",
  "La optimización de la estructura de costos permite que la utilidad neta crezca a un ritmo superior (+15.1%) que las ventas.",
  "Los niveles de impuestos proyectados mantienen la proporcionalidad histórica esperada.",
]);

function exportProjection() {
  // Placeholder
}


</script>

<template>
  <div class="wrap">
    <div class="page-head">
      <div class="badge-row">
        <span class="badge badge-blue">
          PROYECCIÓN GENERADA: {{ projectionMeta.periodoProyectado }}
        </span>
        <span class="badge badge-gray">
          PERIOD BASE: {{ projectionMeta.periodoBase }}
        </span>
      </div>

      <h1>{{ projectionMeta.titulo }}</h1>
      <p class="page-description">{{ projectionMeta.descripcion }}</p>
    </div>

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
          <span class="kpi-dot ok" aria-hidden="true"></span>
        </div>

        <div class="kpi-value">{{ kpi.value }}</div>

        <div class="kpi-bottom">
          <template v-if="!kpi.plainNote">
            <span class="delta-pill delta-up">
              <span class="material-symbols-outlined">trending_up</span>
              {{ kpi.delta }}
            </span>
            <span class="delta-note">{{ kpi.note }}</span>
          </template>

          <template v-else>
            <span class="plain-note">{{ kpi.note }}</span>
          </template>
        </div>
      </article>
    </section>

    <section class="statement-card">
      <div class="statement-head">
        <h3>Estado de Resultados Proforma</h3>
        <button class="link-btn" type="button" @click="exportProjection">
          <span class="material-symbols-outlined">download</span>
          <span>Exportar</span>
        </button>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Concepto</th>
              <th class="right">Periodo base (Q3)</th>
              <th>Supuesto aplicado</th>
              <th class="right">Proyección proforma</th>
              <th class="right">Variación</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="(row, idx) in statementRows"
              :key="idx"
              :class="{
                'row-main': row.kind === 'main',
                'row-subtotal': row.kind === 'subtotal',
                'row-featured': row.kind === 'featured',
                'row-final': row.kind === 'final'
              }"
            >
              <td
                :class="[
                  'concept-cell',
                  {
                    italic: row.kind === 'main' || row.kind === 'subtotal',
                    strong: row.kind === 'subtotal' || row.kind === 'featured' || row.kind === 'final',
                    muted: row.kind === 'normal-negative' || row.kind === 'neutral',
                    'final-cell': row.kind === 'final'
                  }
                ]"
              >
                {{ row.concept }}
              </td>

              <td
                class="right"
                :class="[
                  {
                    strong: row.kind === 'final',
                    'final-cell': row.kind === 'final'
                  }
                ]"
              >
                {{ row.base }}
              </td>

              <td
                :class="[
                  'assumption',
                  {
                    italic: row.kind === 'final',
                    'final-cell': row.kind === 'final',
                    'final-assumption': row.kind === 'final'
                  }
                ]"
              >
                {{ row.assumption }}
              </td>

              <td
                class="right"
                :class="[
                  {
                    strong: row.kind === 'main' || row.kind === 'subtotal' || row.kind === 'featured' || row.kind === 'final',
                    primary: row.kind === 'featured',
                    finalValue: row.kind === 'final',
                    'final-cell': row.kind === 'final'
                  }
                ]"
              >
                {{ row.proforma }}
              </td>

              <td
                class="right"
                :class="[
                  {
                    positive: row.variation.startsWith('+') && row.kind !== 'normal-negative' && row.kind !== 'final',
                    negative: row.kind === 'normal-negative',
                    neutralText: row.kind === 'neutral',
                    finalPositive: row.kind === 'final',
                    'final-cell': row.kind === 'final'
                  }
                ]"
              >
                {{ row.variation }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid-2">
      <article class="note note-info">
        <div class="note-head">
          <div class="icon-circle icon-blue">
            <span class="material-symbols-outlined">info</span>
          </div>
          <h4>Interpretación de la proyección</h4>
        </div>

        <ul class="bullet-list">
          <li v-for="(item, idx) in interpretationPoints" :key="idx">
            <span class="bullet">•</span>
            <span>{{ item }}</span>
          </li>
        </ul>

        <span class="note-bg-icon material-symbols-outlined">lightbulb</span>
      </article>

      <article class="note note-next">
        <div class="note-head">
          <div class="icon-circle icon-primary-fill">
            <span class="material-symbols-outlined">arrow_forward</span>
          </div>
          <h4>Siguiente paso: Balance General Proforma</h4>
        </div>

        <p class="next-text">
          La <strong>Utilidad neta proyectada de $843,597</strong> se integrará automáticamente en la sección de Capital Contable del Balance General Proforma.
        </p>

        <div class="status-inline">
          <span>Listo para procesar</span>
          <span class="pulse-dot" aria-hidden="true"></span>
        </div>
      </article>
    </section>

    <div class="actions">
      <button class="btn-secondary" type="button" @click="exportProjection">
        Exportar proyección
      </button>

      <button class="btn-primary" type="button" @click="goToFormularioBalanceGeneral">
        Continuar al Balance
      </button>
    </div>
  </div>
</template>

<style scoped>
.wrap {
  width: min(1200px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-bottom: 28px;
}

/* Head */
.page-head {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8eff3;
}

.badge-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 2px;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.badge-blue {
  background: #eff6ff;
  color: #299de0;
  border: 1px solid #dbeafe;
}

.badge-gray {
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

/* KPI cards */
.kpis {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.kpi-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.kpi-card:hover {
  border-color: rgba(41, 157, 224, 0.5);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.kpi-card.featured {
  border: 2px solid #299de0;
  background: rgba(41, 157, 224, 0.08);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.kpi-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
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

.kpi-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-top: 3px;
  flex-shrink: 0;
}

.kpi-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}

.kpi-value {
  margin-top: 2px;
  color: #0e161b;
  font-size: 26px;
  font-weight: 900;
  line-height: 1.2;
}

.kpi-bottom {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.delta-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 8px;
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

.delta-note {
  color: #507c95;
  font-size: 12px;
  font-weight: 700;
}

.plain-note {
  color: #507c95;
  font-size: 12px;
  font-style: italic;
  font-weight: 700;
}

/* Statement card */
.statement-card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.statement-head {
  padding: 16px 18px;
  border-bottom: 1px solid #e8eff3;
  background: rgba(248, 250, 251, 0.5);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
}

.statement-head h3 {
  margin: 0;
  color: #0e161b;
  font-size: 16px;
  font-weight: 900;
}

.link-btn {
  border: none;
  background: transparent;
  color: #299de0;
  font-size: 13px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.link-btn:hover {
  color: #1a8ac7;
}

.link-btn .material-symbols-outlined {
  font-size: 16px;
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
}

.table thead th {
  background: #f9fafb;
  color: #507c95;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 1px solid #e8eff3;
  padding: 14px 16px;
  text-align: left;
}

.table tbody td {
  padding: 14px 16px;
  border-bottom: 1px solid #e8eff3;
  color: #0e161b;
  font-size: 13px;
  background: #ffffff;
}

.table tbody tr:hover td {
  background: rgba(249, 250, 251, 0.65);
}

.table tbody tr.row-final:hover td {
  background: #111827 !important;
}

.right {
  text-align: right;
}

.italic {
  font-style: italic;
}

.strong {
  font-weight: 900;
}

.primary {
  color: #299de0;
}

.assumption {
  color: #6b7280;
}

.row-main td {
  background: #ffffff;
}

.row-subtotal td {
  background: rgba(239, 246, 255, 0.6);
}

.row-featured td {
  background: rgba(239, 246, 255, 0.7);
}

.muted {
  color: #507c95;
}

.positive {
  color: #059669;
  font-weight: 700;
}

.negative {
  color: #ef4444;
}

.neutralText {
  color: #9ca3af;
}

/* Final row fix, because CSS likes drama */
.table tbody tr.row-final,
.table tbody tr.row-final:hover {
  background: #111827 !important;
}

.table tbody tr.row-final > td,
.final-cell {
  background: #111827 !important;
  color: #ffffff !important;
  border-bottom: none !important;
  border-top: 2px solid #111827 !important;
  padding-top: 18px;
  padding-bottom: 18px;
}

.table tbody tr.row-final > td.assumption,
.final-cell.final-assumption {
  color: #9ca3af !important;
}

.table tbody tr.row-final > td.finalPositive,
.final-cell.finalPositive {
  color: #34d399 !important;
  font-weight: 900;
}

.table tbody tr.row-final > td.neutralText,
.final-cell.neutralText {
  color: #d1d5db !important;
}

.table tbody tr.row-final > td * ,
.final-cell * {
  color: inherit !important;
}

.finalValue {
  font-size: 20px;
  font-weight: 900;
}

/* Lower cards */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.note {
  position: relative;
  border-radius: 14px;
  padding: 18px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.note-info {
  background: #ffffff;
  border: 1px solid #e8eff3;
}

.note-next {
  background: rgba(239, 246, 255, 0.55);
  border: 2px dashed #299de0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.note-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.note-head h4 {
  margin: 0;
  color: #0e161b;
  font-size: 16px;
  font-weight: 900;
}

.icon-circle {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.icon-circle .material-symbols-outlined {
  font-size: 16px;
}

.icon-blue {
  background: #eff6ff;
  color: #299de0;
}

.icon-primary-fill {
  background: #299de0;
  color: #ffffff;
}

.bullet-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.bullet-list li {
  display: flex;
  gap: 10px;
  color: #507c95;
  font-size: 14px;
  line-height: 1.6;
}

.bullet {
  color: #299de0;
  font-size: 13px;
  margin-top: 3px;
}

.note-bg-icon {
  position: absolute;
  right: -8px;
  bottom: -8px;
  opacity: 0.05;
  font-size: 72px;
  color: #299de0;
}

.next-text {
  margin: 0;
  color: #507c95;
  font-size: 14px;
  line-height: 1.7;
}

.status-inline {
  margin-top: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #299de0;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #299de0;
  animation: pulse 1.4s infinite ease-in-out;
}

/* Actions */
.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.btn-secondary,
.btn-primary {
  width: 100%;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  padding: 12px 18px;
  transition: background 0.15s ease, transform 0.05s ease, border-color 0.15s ease;
  cursor: pointer;
}

.btn-secondary {
  background: #ffffff;
  color: #0e161b;
  border: 1px solid #d1dee6;
}

.btn-secondary:hover {
  background: #f8fafb;
}

.btn-primary {
  background: #299de0;
  color: #ffffff;
  border: none;
  box-shadow: 0 4px 10px rgba(41, 157, 224, 0.2);
  letter-spacing: 0.04em;
  font-weight: 900;
}

.btn-primary:hover {
  background: #1a8ac7;
}

.btn-secondary:active,
.btn-primary:active {
  transform: translateY(1px);
}

/* Responsive */
@media (min-width: 768px) {
  .kpis {
    grid-template-columns: repeat(2, 1fr);
  }

  .actions {
    flex-direction: row;
    justify-content: flex-end;
    align-items: center;
  }

  .btn-secondary,
  .btn-primary {
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
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.25);
    opacity: 0.55;
  }
}
</style>