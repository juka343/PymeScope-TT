<script setup>
import { ref } from "vue";

const headerInfo = ref({
  generatedPeriod: "Q4 2024",
  basePeriod: "Q3 2024",
  title: "Proyección Proforma - Balance General",
  subtitle:
    "Visualiza la estructura financiera proyectada y el impacto de los supuestos en el balance de la empresa.",
});

const sourceSummary = ref({
  periodicidad: "Trimestral",
  inflacion: "4.5%",
  utilidadProforma: "$245,000.00",
  note:
    "Cálculos automáticos aplicados para cuentas FER y Estado de Resultados Proforma vinculados.",
});

const kpis = ref([
  {
    title: "Total activos proyectados",
    value: "$1,450,000",
    delta: "+8.4%",
    note: "vs periodo base",
  },
  {
    title: "Total pasivos proyectados",
    value: "$680,000",
    delta: "+5.2%",
    note: "vs periodo base",
  },
  {
    title: "Total capital proyectado",
    value: "$770,000",
    delta: "+11.2%",
    note: "vs periodo base",
  },
  {
    title: "FER",
    value: "$0.00",
    delta: null,
    note: "Sin requerimiento externo",
// Si FER > 0:
// Financiamiento requerido
// Si FER = 0:
// Sin requerimiento externo
// Si FER < 0:
// Excedente de efectivo
  },
]);

const equation = ref({
  activos: "$1,450,000",
  pasivos: "$680,000",
  capital: "$770,000",
  status: "Balance cuadrado",
});

const activos = ref([
  {
    title: "Activo Circulante",
    tone: "primary",
    totalLabel: "Total activo circulante",
    totalValue: "$1,064,000",
    items: [
      { label: "Caja", value: "$45,000" },
      { label: "Bancos", value: "$345,000" },
      { label: "Inversiones temporales", value: "$75,000" },
      { label: "Cuentas por cobrar a clientes", value: "$155,000" },
      { label: "Otras cuentas por cobrar (deudores diversos)", value: "$28,000" },
      { label: "IVA por acreditar", value: "$12,000" },
      { label: "IVA acreditable", value: "$8,500" },
      {label: "Inventarios",value: "$280,000",},
      { label: "Anticipo a proveedores", value: "$18,000" },
      { label: "Papelería y artículos de escritorio", value: "$3,500" },
      { label: "Propaganda y publicidad", value: "$15,000" },
      { label: "Seguros y fianzas", value: "$12,000" },
      { label: "Rentas pagadas por anticipado", value: "$60,000" },
      { label: "Intereses pagados por anticipado", value: "$5,000" },
      { label: "Impuestos y derechos", value: "$2,000" },
    ],
  },
  {
    title: "Activo No Circulante",
    tone: "primary",
    totalLabel: "Total activo no circulante",
    totalValue: "$536,000",
    items: [
      { label: "Terrenos", value: "$150,000" },
      { label: "Edificios", value: "$200,000" },
      { label: "Maquinaria y equipo", value: "$85,000" },
      { label: "Equipo de transporte", value: "$45,000" },
      { label: "Mobiliario y equipo de oficina", value: "$12,000" },
      { label: "Equipo de cómputo", value: "$8,500" },
      { label: "Patentes", value: "$15,000" },
      { label: "Marcas", value: "$10,000" },
      { label: "Crédito mercantil", value: "$0" },
      { label: "Franquicias", value: "$5,000" },
      { label: "Licencias de software", value: "$3,500" },
      { label: "Depósitos en garantía", value: "$2,000" },
    ],
  },
]);

const pasivoCapital = ref([
  {
    title: "Pasivo a Corto Plazo",
    tone: "orange",
    totalLabel: "Total pasivo a corto plazo",
    totalValue: "$330,000",
    items: [
      { label: "Cuentas por pagar a proveedores", value: "$210,000" },
      { label: "Préstamo bancario / Deuda a corto plazo", value: "$120,000" },
      { label: "Acreedores diversos", value: "$0" },
      { label: "Impuestos a la utilidad por pagar", value: "$0" },
      { label: "IVA por causar o trasladar", value: "$0" },
      { label: "IVA causado o trasladado", value: "$0" },
      { label: "Anticipo de clientes", value: "$0" },
      { label: "Rentas cobradas por anticipado", value: "$0" },
      { label: "Intereses cobrados por anticipado", value: "$0" },
    ],
  },
  {
    title: "Pasivo a Largo Plazo",
    tone: "orange",
    totalLabel: "Total pasivo a largo plazo",
    totalValue: "$350,000",
    items: [
      { label: "Acreedores diversos a largo plazo", value: "$0" },
      { label: "Cuentas por pagar a largo plazo", value: "$350,000" },
      { label: "Cobros anticipados a largo plazo", value: "$0" },
    ],
  },
  {
    title: "Capital Contribuido",
    tone: "blue",
    totalLabel: "Total capital contribuido",
    totalValue: "$500,000",
    items: [
      { label: "Capital social", value: "$500,000" },
      { label: "Aportaciones para futuros aumentos de capital", value: "$0" },
      { label: "Prima en venta de acciones", value: "$0" },
      { label: "Donaciones", value: "$0" },
    ],
  },
  {
    title: "Capital Ganado",
    tone: "blue",
    totalLabel: "Total capital ganado",
    totalValue: "$270,000",
    items: [
      {
        label: "Utilidades o pérdidas de ejercicios anteriores",
        value: "$0",
        tag: "Tomado del balance base",
        tagTone: "gray",
      },
      { label: "Reserva legal", value: "$25,000" },
      { label: "Otros resultados integrales", value: "$0" },
      {
        label: "Utilidad o pérdida del ejercicio",
        value: "$245,000",
        tag: "Tomado del Estado de Resultados Proforma",
        tagTone: "blue",
      },
    ],
  },
]);

const ferCard = ref({
  label: "Fondos Externos Requeridos (FER)",
  subtitle: "Cuenta niveladora calculada automáticamente",
  value: "$0.00",
  status: "Sin requerimiento externo",
});

const totalsRight = ref({
  pasivos: "$680,000",
  capital: "$770,000",
  total: "$1,450,000",
});

const comparativeGroups = ref([
  {
    title: "ACTIVO CIRCULANTE",
    rows: [
      { label: "Caja", base: "$41,000", proforma: "$45,000", variation: "+9.8%", variationTone: "up" },
      { label: "Bancos", base: "$320,000", proforma: "$345,000", variation: "+7.8%", variationTone: "up" },
      { label: "Inversiones temporales", base: "$70,000", proforma: "$75,000", variation: "+7.1%", variationTone: "up" },
      { label: "Cuentas por cobrar a clientes", base: "$125,000", proforma: "$155,000", variation: "+24.0%", variationTone: "up" },
      { label: "Otras cuentas por cobrar (deudores diversos)", base: "$28,000", proforma: "$28,000", variation: "0.0%", variationTone: "neutral" },
      { label: "IVA por acreditar", base: "$10,000", proforma: "$12,000", variation: "+20.0%", variationTone: "up" },
      { label: "IVA acreditable", base: "$8,500", proforma: "$8,500", variation: "0.0%", variationTone: "neutral" },
      { label: "Inventarios", base: "$280,000", proforma: "$280,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Anticipo a proveedores", base: "$15,000", proforma: "$18,000", variation: "+20.0%", variationTone: "up" },
      { label: "Papelería y artículos de escritorio", base: "$3,500", proforma: "$3,500", variation: "0.0%", variationTone: "neutral" },
      { label: "Propaganda y publicidad", base: "$12,000", proforma: "$15,000", variation: "+25.0%", variationTone: "up" },
      { label: "Seguros y fianzas", base: "$12,000", proforma: "$12,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Rentas pagadas por anticipado", base: "$50,000", proforma: "$60,000", variation: "+20.0%", variationTone: "up" },
      { label: "Intereses pagados por anticipado", base: "$5,000", proforma: "$5,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Impuestos y derechos", base: "$2,000", proforma: "$2,000", variation: "0.0%", variationTone: "neutral" },
      {
        label: "Total Activo Circulante",
        base: "$982,000",
        proforma: "$1,064,000",
        variation: "+8.3%",
        variationTone: "up",
        total: true,
      },
    ],
  },
  {
    title: "ACTIVO NO CIRCULANTE",
    rows: [
      { label: "Terrenos", base: "$150,000", proforma: "$150,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Edificios", base: "$200,000", proforma: "$200,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Maquinaria y equipo", base: "$85,000", proforma: "$85,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Equipo de transporte", base: "$45,000", proforma: "$45,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Mobiliario y equipo de oficina", base: "$12,000", proforma: "$12,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Equipo de cómputo", base: "$8,500", proforma: "$8,500", variation: "0.0%", variationTone: "neutral" },
      { label: "Patentes", base: "$15,000", proforma: "$15,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Marcas", base: "$10,000", proforma: "$10,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Crédito mercantil", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "Franquicias", base: "$5,000", proforma: "$5,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Licencias de software", base: "$3,500", proforma: "$3,500", variation: "0.0%", variationTone: "neutral" },
      { label: "Depósitos en garantía", base: "$2,000", proforma: "$2,000", variation: "0.0%", variationTone: "neutral" },
      {
        label: "Total Activo No Circulante",
        base: "$536,000",
        proforma: "$536,000",
        variation: "0.0%",
        variationTone: "neutral",
        total: true,
      },
    ],
  },
  {
    title: "PASIVO A CORTO PLAZO",
    rows: [
      { label: "Cuentas por pagar a proveedores", base: "$195,000", proforma: "$210,000", variation: "+7.7%", variationTone: "up" },
      { label: "Préstamo bancario / Deuda a corto plazo", base: "$110,000", proforma: "$120,000", variation: "+9.1%", variationTone: "up" },
      { label: "Acreedores diversos", base: "$10,000", proforma: "$0", variation: "-100.0%", variationTone: "down" },
      { label: "Impuestos a la utilidad por pagar", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "IVA por causar o trasladar", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "IVA causado o trasladado", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "Anticipo de clientes", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "Rentas cobradas por anticipado", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "Intereses cobrados por anticipado", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      {
        label: "Total Pasivo a Corto Plazo",
        base: "$315,000",
        proforma: "$330,000",
        variation: "+4.8%",
        variationTone: "up",
        total: true,
      },
    ],
  },
  {
    title: "PASIVO A LARGO PLAZO",
    rows: [
      { label: "Acreedores diversos a largo plazo", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "Cuentas por pagar a largo plazo", base: "$330,000", proforma: "$350,000", variation: "+6.1%", variationTone: "up" },
      { label: "Cobros anticipados a largo plazo", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      {
        label: "Total Pasivo a Largo Plazo",
        base: "$330,000",
        proforma: "$350,000",
        variation: "+6.1%",
        variationTone: "up",
        total: true,
      },
    ],
  },
  {
    title: "CAPITAL CONTRIBUIDO",
    rows: [
      { label: "Capital social", base: "$500,000", proforma: "$500,000", variation: "0.0%", variationTone: "neutral" },
      { label: "Aportaciones para futuros aumentos de capital", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "Prima en venta de acciones", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      { label: "Donaciones", base: "$0", proforma: "$0", variation: "0.0%", variationTone: "neutral" },
      {
        label: "Total Capital Contribuido",
        base: "$500,000",
        proforma: "$500,000",
        variation: "0.0%",
        variationTone: "neutral",
        total: true,
      },
    ],
  },
  {
    title: "CAPITAL GANADO",
    rows: [
      {
        label: "Utilidades o pérdidas de ejercicios anteriores",
        base: "$0",
        proforma: "$0",
        variation: "0.0%",
        variationTone: "neutral",
      },
      {
        label: "Reserva legal",
        base: "$20,000",
        proforma: "$25,000",
        variation: "+25.0%",
        variationTone: "up",
      },
      {
        label: "Otros resultados integrales",
        base: "$0",
        proforma: "$0",
        variation: "0.0%",
        variationTone: "neutral",
      },
      {
        label: "Utilidad o pérdida del ejercicio",
        base: "$170,000",
        proforma: "$245,000",
        variation: "+44.1%",
        variationTone: "up",
      },
      {
        label: "Total Capital Ganado",
        base: "$190,000",
        proforma: "$270,000",
        variation: "+42.1%",
        variationTone: "up",
        total: true,
      },
    ],
  },
  {
    title: "FER",
    rows: [
      {
        label: "Fondos Externos Requeridos (FER)",
        base: "$0.00",
        proforma: "$0.00",
        variation: "0.0%",
        variationTone: "neutral",
      },
      {
        label: "Total FER",
        base: "$0.00",
        proforma: "$0.00",
        variation: "0.0%",
        variationTone: "neutral",
        total: true,
      },
    ],
  },
]);

function exportProjection() {
  // Placeholder
}
</script>

<template>
  <div class="wrap">
    <div class="page-head">
      <div class="page-badges">
        <span class="mini-badge mini-badge-blue">PROYECCIÓN GENERADA: {{ headerInfo.generatedPeriod }}</span>
        <span class="mini-badge mini-badge-gray">PERIODO BASE: {{ headerInfo.basePeriod }}</span>
      </div>

      <h1>{{ headerInfo.title }}</h1>
      <p class="page-description">{{ headerInfo.subtitle }}</p>
    </div>

    <section class="source-card">
      <div class="source-head">
        <span class="material-symbols-outlined">source</span>
        <span>Fuente de datos de la proyección</span>
      </div>

      <div class="source-grid">
        <div class="source-item">
          <p class="source-label">Periodicidad</p>
          <p class="source-value">{{ sourceSummary.periodicidad }}</p>
        </div>

        <div class="source-item">
          <p class="source-label">Inflación proyectada</p>
          <p class="source-value">{{ sourceSummary.inflacion }}</p>
        </div>

        <div class="source-item">
          <p class="source-label">Utilidad Proforma</p>
          <p class="source-value source-value-primary">{{ sourceSummary.utilidadProforma }}</p>
        </div>

        <div class="source-note">
          <span class="material-symbols-outlined">info</span>
          <p>{{ sourceSummary.note }}</p>
        </div>
      </div>
    </section>

    <section class="kpis">
      <article v-for="(kpi, idx) in kpis" :key="idx" class="kpi-card">
        <div class="kpi-top">
          <p class="kpi-title">{{ kpi.title }}</p>
        </div>

        <p class="kpi-value">{{ kpi.value }}</p>

        <div class="kpi-bottom">
          <template v-if="kpi.delta">
            <span class="kpi-chip">
              <span class="material-symbols-outlined">trending_up</span>
              {{ kpi.delta }}
            </span>
            <span class="kpi-note">{{ kpi.note }}</span>
          </template>

          <template v-else>
            <span class="kpi-note kpi-note-italic">{{ kpi.note }}</span>
          </template>
        </div>
      </article>
    </section>

    <section class="equation-bar">
      <div class="equation-side">
        <span class="equation-amount">{{ equation.activos }}</span>
        <span class="equation-text">Activos proyectados</span>
      </div>

      <span class="equation-equals">=</span>

      <div class="equation-center">
        <span class="equation-amount">{{ equation.pasivos }}</span>
        <span class="equation-text">Pasivos</span>
        <span class="equation-plus">+</span>
        <span class="equation-amount">{{ equation.capital }}</span>
        <span class="equation-text">Capital</span>
      </div>

      <span class="equation-status">{{ equation.status }}</span>
    </section>

    <section class="main-grid">
      <article class="balance-card">
        <div class="balance-card-head">
          <h3>
            <span class="material-symbols-outlined text-primary">account_balance_wallet</span>
            Activos
          </h3>
        </div>

        <div class="balance-card-body">
          <section
            v-for="(section, idx) in activos"
            :key="`asset-section-${idx}`"
            class="group-section"
          >
            <h4 class="group-kicker group-kicker-primary">{{ section.title }}</h4>

            <div class="rows">
              <div
                v-for="(item, rowIdx) in section.items"
                :key="`asset-row-${idx}-${rowIdx}`"
                class="row"
              >
                <div class="row-label-wrap">
                  <span class="row-label">{{ item.label }}</span>
                  <span
                    v-if="item.tag"
                    class="row-tag"
                    :class="item.tagTone === 'blue' ? 'row-tag-blue' : 'row-tag-gray'"
                  >
                    {{ item.tag }}
                  </span>
                </div>

                <span class="row-value">{{ item.value }}</span>
              </div>

              <div class="subtotal subtotal-primary">
                <span>{{ section.totalLabel }}</span>
                <span>{{ section.totalValue }}</span>
              </div>
            </div>
          </section>
        </div>

        <div class="card-total card-total-primary">
          <span>Total Activos</span>
          <span>$1,450,000</span>
        </div>
      </article>

      <article class="balance-card">
        <div class="balance-card-head">
          <h3>
            <span class="material-symbols-outlined text-orange">account_balance</span>
            Pasivo y Capital
          </h3>
        </div>

        <div class="balance-card-body">
          <section
            v-for="(section, idx) in pasivoCapital"
            :key="`pc-section-${idx}`"
            class="group-section"
          >
            <h4
              class="group-kicker"
              :class="section.tone === 'orange' ? 'group-kicker-orange' : 'group-kicker-blue'"
            >
              {{ section.title }}
            </h4>

            <div class="rows">
              <div
                v-for="(item, rowIdx) in section.items"
                :key="`pc-row-${idx}-${rowIdx}`"
                class="row"
              >
                <div class="row-label-wrap">
                  <span class="row-label">{{ item.label }}</span>
                  <span
                    v-if="item.tag"
                    class="row-tag"
                    :class="item.tagTone === 'blue' ? 'row-tag-blue' : 'row-tag-gray'"
                  >
                    {{ item.tag }}
                  </span>
                </div>

                <span class="row-value">{{ item.value }}</span>
              </div>

              <div
                class="subtotal"
                :class="section.tone === 'orange' ? 'subtotal-orange' : 'subtotal-blue'"
              >
                <span>{{ section.totalLabel }}</span>
                <span>{{ section.totalValue }}</span>
              </div>
            </div>
          </section>

          <div class="fer-card">
            <div class="fer-left">
              <span class="material-symbols-outlined">analytics</span>
              <div>
                <p class="fer-title">{{ ferCard.label }}</p>
                <p class="fer-subtitle">{{ ferCard.subtitle }}</p>
              </div>
            </div>

            <div class="fer-right">
              <p class="fer-value">{{ ferCard.value }}</p>
              <span class="fer-badge">{{ ferCard.status }}</span>
            </div>
          </div>

          <div class="totals-summary">
            <div class="totals-line">
              <span>Total Pasivos</span>
              <span>{{ totalsRight.pasivos }}</span>
            </div>
            <div class="totals-line">
              <span>Total Capital</span>
              <span>{{ totalsRight.capital }}</span>
            </div>
          </div>
        </div>

        <div class="card-total card-total-dark">
          <span>Total Pasivo + Capital</span>
          <span>{{ totalsRight.total }}</span>
        </div>
      </article>
    </section>

    <div class="actions">
      <button class="btn-secondary" type="button" @click="exportProjection">
        <span class="material-symbols-outlined">download</span>
        <span>Exportar proyección</span>
      </button>
    </div>

    <details class="details-panel">
      <summary class="details-summary">
        <div class="details-left">
          <span class="material-symbols-outlined summary-icon">expand_more</span>
          <h3>Detalle comparativo por cuenta</h3>
        </div>

        <span class="details-badge">Ver desglose</span>
      </summary>

      <div class="details-table-wrap">
        <table class="details-table">
          <thead>
            <tr>
              <th>Concepto</th>
              <th class="right">Periodo Base (Q3)</th>
              <th class="right">Proforma (Q4)</th>
              <th class="right">Variación (%)</th>
            </tr>
          </thead>

          <tbody>
            <template v-for="(group, idx) in comparativeGroups" :key="`group-${idx}`">
              <tr class="section-row">
                <td colspan="4">{{ group.title }}</td>
              </tr>

              <tr
                v-for="(row, rowIdx) in group.rows"
                :key="`row-${idx}-${rowIdx}`"
                :class="{ 'total-row': row.total }"
              >
                <td>{{ row.label }}</td>
                <td class="right">{{ row.base }}</td>
                <td class="right strong">{{ row.proforma }}</td>
                <td
                  class="right"
                  :class="
                    row.variationTone === 'up'
                      ? 'tone-up'
                      : row.variationTone === 'down'
                      ? 'tone-down'
                      : 'tone-neutral'
                  "
                >
                  {{ row.variation }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </details>
  </div>
</template>

<style scoped>
.wrap {
  width: min(1200px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 22px;
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

/* Source summary */
.source-card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.source-head {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  color: #0e161b;
  font-size: 14px;
  font-weight: 900;
}

.source-head .material-symbols-outlined {
  color: #299de0;
  font-size: 18px;
}

.source-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
}

.source-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-label {
  margin: 0;
  color: #507c95;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.source-value {
  margin: 0;
  color: #0e161b;
  font-size: 20px;
  font-weight: 900;
}

.source-value-primary {
  color: #299de0;
}

.source-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: rgba(239, 246, 255, 0.6);
  border: 1px solid #dbeafe;
  border-radius: 10px;
}

.source-note .material-symbols-outlined {
  color: #299de0;
  font-size: 16px;
  margin-top: 1px;
  flex-shrink: 0;
}

.source-note p {
  margin: 0;
  color: #507c95;
  font-size: 10px;
  line-height: 1.45;
  font-weight: 700;
}

/* KPIs */
.kpis {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.kpi-card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.kpi-card:hover {
  border-color: rgba(41, 157, 224, 0.35);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.kpi-title {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  font-weight: 700;
}

.kpi-value {
  margin: 10px 0 0;
  color: #0e161b;
  font-size: 28px;
  font-weight: 900;
  line-height: 1.1;
}

.kpi-bottom {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.kpi-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 10px;
  font-weight: 900;
}

.kpi-chip .material-symbols-outlined {
  font-size: 12px;
}

.kpi-note {
  color: #507c95;
  font-size: 10px;
  font-weight: 700;
}

.kpi-note-italic {
  font-style: italic;
}

/* Equation */
.equation-bar {
  background: rgba(243, 244, 246, 0.55);
  border: 1px solid #e8eff3;
  border-radius: 999px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.equation-side,
.equation-center {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.equation-amount {
  color: #0e161b;
  font-size: 15px;
  font-weight: 900;
}

.equation-text {
  color: #507c95;
  font-size: 13px;
  font-weight: 600;
}

.equation-equals,
.equation-plus {
  color: #299de0;
  font-size: 22px;
  font-weight: 900;
}

.equation-status {
  display: inline-flex;
  align-self: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  background: #16a34a;
  color: #ffffff;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Main balance cards */
.main-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
  align-items: start;
}

.balance-card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.balance-card-head {
  padding: 18px 20px;
  border-bottom: 1px solid #e8eff3;
  background: rgba(249, 250, 251, 0.7);
}

.balance-card-head h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0e161b;
  font-size: 16px;
  font-weight: 900;
}

.text-primary {
  color: #299de0;
}

.text-orange {
  color: #f97316;
}

.balance-card-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.group-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.group-kicker {
  margin: 0;
  padding-bottom: 6px;
  border-bottom: 1px solid;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

.group-kicker-primary {
  color: #299de0;
  border-color: rgba(41, 157, 224, 0.12);
}

.group-kicker-orange {
  color: #ea580c;
  border-color: rgba(249, 115, 22, 0.15);
}

.group-kicker-blue {
  color: #2563eb;
  border-color: rgba(37, 99, 235, 0.15);
}

.rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0;
  border-bottom: 1px solid #f9fafb;
}

.row-label-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.row-label {
  color: #507c95;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
}

.row-value {
  color: #0e161b;
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
}

.row-tag {
  width: fit-content;
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 9px;
  font-weight: 800;
}

.row-tag-gray {
  background: #f3f4f6;
  color: #6b7280;
}

.row-tag-blue {
  background: #eff6ff;
  color: #1d4ed8;
}

.subtotal {
  margin-top: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid;
}

.subtotal span:first-child {
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.subtotal span:last-child {
  font-size: 18px;
  font-weight: 900;
}

.subtotal-primary {
  background: rgba(239, 246, 255, 0.6);
  border-color: #dbeafe;
  color: #299de0;
}

.subtotal-orange {
  background: rgba(255, 247, 237, 0.7);
  border-color: #fed7aa;
  color: #c2410c;
}

.subtotal-blue {
  background: rgba(239, 246, 255, 0.6);
  border-color: #dbeafe;
  color: #1d4ed8;
}

.fer-card {
  margin-top: 4px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(239, 246, 255, 0.55);
  border: 1px solid #bfdbfe;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.fer-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.fer-left .material-symbols-outlined {
  color: #299de0;
}

.fer-title {
  margin: 0;
  color: #0e161b;
  font-size: 14px;
  font-weight: 900;
}

.fer-subtitle {
  margin: 2px 0 0;
  color: #507c95;
  font-size: 11px;
  font-weight: 600;
}

.fer-right {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.fer-value {
  margin: 0;
  color: #299de0;
  font-size: 24px;
  font-weight: 900;
}

.fer-badge {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 999px;
  background: #dcfce7;
  color: #15803d;
  font-size: 9px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.totals-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 4px;
}

.totals-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 2px;
}

.totals-line span:first-child {
  color: #507c95;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
}

.totals-line span:last-child {
  color: #0e161b;
  font-size: 14px;
  font-weight: 900;
}

.card-total {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-total span:first-child {
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.15em;
}

.card-total span:last-child {
  font-size: 30px;
  font-weight: 900;
}

.card-total-primary {
  background: rgba(37, 99, 235, 0.08);
  border-top: 1px solid rgba(59, 130, 246, 0.18);
  color: #299de0;
}

.card-total-dark {
  background: #2563eb;
  color: #ffffff;
}

/* Actions */
.actions {
  display: flex;
  justify-content: flex-end;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #d1dee6;
  color: #0e161b;
  font-size: 14px;
  font-weight: 700;
  padding: 10px 18px;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.btn-secondary:hover {
  background: #f8fafb;
  border-color: #bfd6e3;
}

.btn-secondary .material-symbols-outlined {
  font-size: 18px;
}

/* Details panel */
.details-panel {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.details-summary {
  list-style: none;
  cursor: pointer;
  padding: 18px 20px;
  background: rgba(249, 250, 251, 0.7);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.details-summary::-webkit-details-marker {
  display: none;
}

.details-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.details-left h3 {
  margin: 0;
  color: #0e161b;
  font-size: 16px;
  font-weight: 900;
}

.summary-icon {
  color: #507c95;
  font-size: 22px;
  transition: transform 0.2s ease;
}

.details-panel[open] .summary-icon {
  transform: rotate(180deg);
}

.details-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e8eff3;
  color: #507c95;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.details-table-wrap {
  overflow-x: auto;
  border-top: 1px solid #e8eff3;
}

.details-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 900px;
}

.details-table thead th {
  background: #f9fafb;
  color: #507c95;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  padding: 16px 20px;
  border-bottom: 1px solid #e8eff3;
  text-align: left;
}

.details-table td {
  padding: 12px 20px;
  border-bottom: 1px solid #e8eff3;
  color: #0e161b;
  font-size: 14px;
}

.details-table tbody tr:hover {
  background: rgba(249, 250, 251, 0.45);
}

.details-table .right {
  text-align: right;
}

.section-row td {
  background: rgba(249, 250, 251, 0.85);
  color: #0e161b;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 10px 20px;
}

.strong {
  font-weight: 800;
}

.tone-up {
  color: #16a34a;
  font-weight: 800;
}

.tone-down {
  color: #dc2626;
  font-weight: 800;
}

.tone-neutral {
  color: #507c95;
  font-weight: 700;
}

.total-row td {
  background: rgba(239, 246, 255, 0.45);
  border-top: 1px solid #dbeafe;
  font-weight: 900;
}

.total-row td:first-child {
  color: #299de0;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.total-row .tone-up {
  color: #16a34a;
}

.total-row .tone-neutral {
  color: #299de0;
  font-weight: 900;
}

/* Responsive */
@media (min-width: 768px) {
  .source-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .kpis {
    grid-template-columns: repeat(2, 1fr);
  }

  .equation-bar {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
  }

  .fer-card {
    flex-direction: row;
    align-items: flex-start;
    justify-content: space-between;
  }

  .fer-right {
    align-items: flex-end;
  }
}

@media (min-width: 1024px) {
  .source-grid {
    grid-template-columns: repeat(4, 1fr);
    align-items: stretch;
  }

  .kpis {
    grid-template-columns: repeat(4, 1fr);
  }

  .main-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>