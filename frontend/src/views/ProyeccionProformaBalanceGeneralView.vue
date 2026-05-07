<script setup>
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { db } from "@/firebase/config";
import { collection, query, orderBy, limit, getDocs, where } from "firebase/firestore";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

const router = useRouter();
const route = useRoute();
const getRouteName = (baseName) => route.path.includes('dashboard-multi') ? `${baseName}Multi` : baseName;
const projectId = route.params.id_proyecto;

function editProjection() {
  const isHistory = route.query.isHistory === 'true';
  const lsKeyConfig = isHistory ? 'history_balance_config' : 'current_balance_config';
  const configRaw = localStorage.getItem(lsKeyConfig);
  const config = configRaw ? JSON.parse(configRaw) : {};
  router.push({
    name: getRouteName("FormularioBalanceGeneral"),
    query: {
      periodoBaseId: config.periodoBaseId || '',
      label: config.periodoBase || '',
      periodDate: config.periodDate || '',
      modo: 'editar',
      isHistory: isHistory ? 'true' : 'false'
    }
  });
}

function regresarEstadoResultados() {
  const isHistory = route.query.isHistory === 'true';
  router.push({ 
    name: getRouteName("ProyeccionProformaEdo"),
    query: isHistory ? { isHistory: 'true' } : {}
  });
}

function finalizarProyeccion() {
  // Solo limpiamos la sesión activa si no estamos viendo el historial
  // (Aunque si estamos en historial, las variables de current_ no se ven afectadas)
  const isHistory = route.query.isHistory === 'true';
  if (!isHistory) {
    localStorage.removeItem('current_projection_result');
    localStorage.removeItem('current_projection_config');
    localStorage.removeItem('current_projection_supuestos');
    localStorage.removeItem('current_balance_result');
    localStorage.removeItem('current_balance_config');
    localStorage.removeItem('current_balance_supuestos');
  } else {
    // También limpiamos el historial para no dejar rastro innecesario
    localStorage.removeItem('history_projection_result');
    localStorage.removeItem('history_projection_config');
    localStorage.removeItem('history_projection_supuestos');
    localStorage.removeItem('history_balance_result');
    localStorage.removeItem('history_balance_config');
    localStorage.removeItem('history_balance_supuestos');
  }

  router.push({ name: getRouteName('proyecciones') });
}

const headerInfo = ref({
  generatedPeriod: "...",
  basePeriod: "...",
  title: "Proyección Proforma - Balance General",
  subtitle: "Visualiza la estructura financiera proyectada y el impacto de los supuestos en el balance de la empresa.",
});

const sourceSummary = ref({
  periodicidad: "...",
  inflacion: "0%",
  utilidadProforma: "$0",
  note: "Cálculos automáticos aplicados para cuentas FER y Estado de Resultados Proforma vinculados.",
});

const kpis = ref([
  { title: "Total activos proyectados", value: "$0", delta: "0%", note: "vs periodo base" },
  { title: "Total pasivos proyectados", value: "$0", delta: "0%", note: "vs periodo base" },
  { title: "Total capital proyectado", value: "$0", delta: "0%", note: "vs periodo base" },
  { title: "FER", value: "$0.00", delta: null, note: "Calculando..." },
]);

const equation = ref({
  activos: "$0",
  pasivos: "$0",
  capital: "$0",
  status: "Calculando...",
});

const assetsGroups = ref([]);
const liabilityEquityGroups = ref([]);
const comparativeGroups = ref([]);

const totals = ref({
  activo: 0,
  pasivo: 0,
  capital: 0,
  fer: 0
});

const isExporting = ref(false);
const pdfZone = ref(null);

// Helpers de formato
const fmt = (val) => {
  if (val === undefined || val === null) return "$0.00";
  const num = Number(val);
  const ABS = Math.abs(num).toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return num < 0 ? `-$${ABS}` : `$${ABS}`;
};

const pct = (val) => {
  const num = Number(val) || 0;
  return (num >= 0 ? "+" : "") + num.toFixed(1) + "%";
};

// Listas de conceptos para categorización (Basado en el formulario)
const catActivoCirculante = ["Caja", "Bancos", "Inversiones temporales", "Cuentas por cobrar a clientes", "Otras cuentas por cobrar (deudores diversos)", "IVA por acreditar", "IVA acreditable", "Inventarios", "Anticipo a proveedores", "Papelería y artículos de escritorio", "Propaganda y publicidad", "Seguros y fianzas", "Rentas pagadas por anticipado", "Intereses pagados por anticipado", "Impuestos y derechos"];
const catActivoNoCirculante = ["Terrenos", "Edificios", "Maquinaria y equipo", "Equipo de transporte", "Mobiliario y equipo de oficina", "Equipo de cómputo", "Patentes", "Marcas", "Crédito mercantil", "Franquicias", "Licencias de software", "Depósitos en garantía", "Depreciación acumulada"];
const catPasivoCorto = ["Cuentas por pagar a proveedores", "Préstamo bancario / Deuda a corto plazo", "Acreedores diversos", "Impuestos a la utilidad por pagar", "IVA por causar o trasladar", "IVA causado o trasladado", "Anticipo de clientes", "Rentas cobradas por anticipado", "Intereses cobrados por anticipado"];
const catPasivoLargo = ["Acreedores diversos a largo plazo", "Cuentas por pagar a largo plazo", "Cobros anticipados a largo plazo"];
const catCapitalContribuido = ["Capital social", "Aportaciones para futuros aumentos de capital", "Prima en venta de acciones", "Donaciones"];
const catCapitalGanado = ["Reserva legal", "Otros resultados integrales", "Utilidades de ejercicios anteriores", "Utilidad neta proforma"];

onMounted(async () => {
  window.scrollTo(0, 0);

  if (projectId) {
    try {
      const { doc, getDoc } = await import("firebase/firestore");
      const projectDocRef = doc(db, "proyectos", projectId);
      const projectDocSnap = await getDoc(projectDocRef);
      if (projectDocSnap.exists()) {
        sourceSummary.value.periodicidad = projectDocSnap.data().periodicidad || "mensual";
      }
    } catch (err) {
      console.error("Error al recuperar periodicidad:", err);
    }
  }

  const isHistory = route.query.isHistory === 'true';
  const lsKeyResult = isHistory ? 'history_balance_result' : 'current_balance_result';
  const lsKeyConfig = isHistory ? 'history_balance_config' : 'current_balance_config';

  let resultsRaw = localStorage.getItem(lsKeyResult);
  let configRaw = localStorage.getItem(lsKeyConfig);

  if (!resultsRaw) {
    console.warn("No se encontraron resultados de balance para mostrar.");
    router.push({ name: getRouteName('proyecciones') });
    return;
  }

  const res = JSON.parse(resultsRaw);
  const conf = JSON.parse(configRaw || '{}');

  // Header e info general
  headerInfo.value.generatedPeriod = conf.periodoProyectado || "Proyectado";
  headerInfo.value.basePeriod = conf.periodoBase || "Base";
  sourceSummary.value.inflacion = (conf.inflacion || 0) + "%";
  
  // Buscar utilidad en los resultados o en la tabla (Fallback robusto)
  const utilityRow = res.tablas_proyectadas?.find(f => f.concepto === "Utilidad neta proforma");
  const valUtilidad = res.utilidad_neta_proforma || (utilityRow ? utilityRow.valor_proyectado : 0);
  sourceSummary.value.utilidadProforma = fmt(valUtilidad);

  // Totales
  totals.value.activo = res.total_activo || 0;
  totals.value.pasivo = res.total_pasivo || 0;
  totals.value.capital = res.total_capital || 0;
  totals.value.fer = res.fer || 0;

  // Calculando variaciones globales para KPIs
  const totalActivoBase = res.tablas_proyectadas.filter(f => catActivoCirculante.includes(f.concepto) || catActivoNoCirculante.includes(f.concepto)).reduce((sum, f) => sum + (f.valor_base || 0), 0);
  const totalPasivoBase = res.tablas_proyectadas.filter(f => catPasivoCorto.includes(f.concepto) || catPasivoLargo.includes(f.concepto)).reduce((sum, f) => sum + (f.valor_base || 0), 0);
  const totalCapitalBase = res.tablas_proyectadas.filter(f => catCapitalContribuido.includes(f.concepto) || catCapitalGanado.includes(f.concepto)).reduce((sum, f) => sum + (f.valor_base || 0), 0);

  const deltaActivo = totalActivoBase !== 0 ? (((res.total_activo / Math.abs(totalActivoBase)) - Math.sign(totalActivoBase)) * 100) : 0;
  const deltaPasivo = totalPasivoBase !== 0 ? (((res.total_pasivo / Math.abs(totalPasivoBase)) - Math.sign(totalPasivoBase)) * 100) : 0;
  const deltaCapital = totalCapitalBase !== 0 ? (((res.total_capital / Math.abs(totalCapitalBase)) - Math.sign(totalCapitalBase)) * 100) : 0;

  const basePeriodText = `vs ${headerInfo.value.basePeriod}`;

  kpis.value[0].value = fmt(res.total_activo);
  kpis.value[0].delta = pct(deltaActivo);
  kpis.value[0].note = basePeriodText;
  
  kpis.value[1].value = fmt(res.total_pasivo);
  kpis.value[1].delta = pct(deltaPasivo);
  kpis.value[1].note = basePeriodText;
  
  kpis.value[2].value = fmt(res.total_capital);
  kpis.value[2].delta = pct(deltaCapital);
  kpis.value[2].note = basePeriodText;
  
  kpis.value[3].value = fmt(res.fer);
  kpis.value[3].note = res.fer > 0.01 ? "Financiamiento requerido" : (res.fer < -0.01 ? "Excedente de recursos" : "Sin requerimiento externo");

  equation.value.activos = fmt(res.total_activo);
  equation.value.pasivos = fmt(res.total_pasivo);
  equation.value.capital = fmt(res.total_capital);
  equation.value.status = Math.abs(res.total_activo - (res.total_pasivo + res.total_capital + res.fer)) < 1 ? "Balance cuadrado" : "Descuadre detectado";

  // Categorización para tablas de Balance
  const categorize = (names) => {
    return res.tablas_proyectadas
      .filter(f => names.includes(f.concepto))
      .map(f => ({
        label: f.concepto,
        value: fmt(f.valor_proyectado),
        baseValue: fmt(f.valor_base),
        variation: pct(f.variacion_aplicada),
        variationTone: f.variacion_aplicada > 0 ? "up" : (f.variacion_aplicada < 0 ? "down" : "neutral")
      }));
  };

  const groupAC = categorize(catActivoCirculante);
  const groupANC = categorize(catActivoNoCirculante);
  const groupPC = categorize(catPasivoCorto);
  const groupPL = categorize(catPasivoLargo);
  const groupCC = categorize(catCapitalContribuido);
  const groupCG = categorize(catCapitalGanado);

  assetsGroups.value = [
    { title: "Activo Circulante", tone: "primary", items: groupAC, totalLabel: "Total Activo Circulante", totalValue: fmt(groupAC.reduce((s, i) => s + (res.tablas_proyectadas.find(f => f.concepto === i.label)?.valor_proyectado || 0), 0)) },
    { title: "Activo No Circulante", tone: "primary", items: groupANC, totalLabel: "Total Activo No Circulante", totalValue: fmt(groupANC.reduce((s, i) => s + (res.tablas_proyectadas.find(f => f.concepto === i.label)?.valor_proyectado || 0), 0)) }
  ];

  liabilityEquityGroups.value = [
    { title: "Pasivo a Corto Plazo", tone: "orange", items: groupPC, totalLabel: "Total Pasivo a Corto Plazo", totalValue: fmt(groupPC.reduce((s, i) => s + (res.tablas_proyectadas.find(f => f.concepto === i.label)?.valor_proyectado || 0), 0)) },
    { title: "Pasivo a Largo Plazo", tone: "orange", items: groupPL, totalLabel: "Total Pasivo a Largo Plazo", totalValue: fmt(groupPL.reduce((s, i) => s + (res.tablas_proyectadas.find(f => f.concepto === i.label)?.valor_proyectado || 0), 0)) },
    { title: "Capital Contribuido", tone: "blue", items: groupCC, totalLabel: "Total Capital Contribuido", totalValue: fmt(groupCC.reduce((s, i) => s + (res.tablas_proyectadas.find(f => f.concepto === i.label)?.valor_proyectado || 0), 0)) },
    { title: "Capital Ganado", tone: "blue", items: groupCG, totalLabel: "Total Capital Ganado", totalValue: fmt(groupCG.reduce((s, i) => s + (res.tablas_proyectadas.find(f => f.concepto === i.label)?.valor_proyectado || 0), 0)) }
  ];

  // Detalle comparativo
  comparativeGroups.value = [
    { title: "ACTIVO CIRCULANTE", rows: groupAC.map(i => ({ ...i, proforma: i.value, base: i.baseValue, total: false })) },
    { title: "ACTIVO NO CIRCULANTE", rows: groupANC.map(i => ({ ...i, proforma: i.value, base: i.baseValue, total: false })) },
    { title: "PASIVO A CORTO PLAZO", rows: groupPC.map(i => ({ ...i, proforma: i.value, base: i.baseValue, total: false })) },
    { title: "PASIVO A LARGO PLAZO", rows: groupPL.map(i => ({ ...i, proforma: i.value, base: i.baseValue, total: false })) },
    { title: "CAPITAL CONTRIBUIDO", rows: groupCC.map(i => ({ ...i, proforma: i.value, base: i.baseValue, total: false })) },
    { title: "CAPITAL GANADO", rows: groupCG.map(i => ({ ...i, proforma: i.value, base: i.baseValue, total: false })) }
  ];
});

async function exportProjection() {
  if (isExporting.value) return;
  isExporting.value = true;
  await new Promise(r => setTimeout(r, 100));

  try {
    const el = pdfZone.value;
    const canvas = await html2canvas(el, {
      scale: 2,
      useCORS: true,
      backgroundColor: "#f8fafb",
      logging: false,
    });

    const imgData = canvas.toDataURL("image/png");
    const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

    const pageW = pdf.internal.pageSize.getWidth();
    const pageH = pdf.internal.pageSize.getHeight();
    const margin = 10;
    const contentW = pageW - margin * 2;
    const contentH = (canvas.height * contentW) / canvas.width;

    let posY = margin;
    let remaining = contentH;

    while (remaining > 0) {
      pdf.addImage(imgData, "PNG", margin, posY, contentW, contentH);
      remaining -= (pageH - margin * 2);
      if (remaining > 0) {
        pdf.addPage();
        posY = margin - (pageH - margin * 2);
      }
    }

    const config = JSON.parse(localStorage.getItem('current_balance_config') || '{}');
    const periodo = (config.periodoProyectado || 'Proyeccion-Balance').replace(/\s+/g, '-');
    pdf.save(`balance-proforma-${periodo}.pdf`);
  } catch (err) {
    console.error("Error generando PDF:", err);
    alert("No se pudo generar el PDF.");
  } finally {
    isExporting.value = false;
  }
}
</script>

<template>
  <div class="page-container">
    <div class="wrap" :class="{ 'is-exporting': isExporting }" ref="pdfZone">
      <div class="pdf-brand">
        <div class="pdf-brand-left">
          <div class="pdf-logo">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M42.1739 20.1739L27.8261 5.82609C29.1366 7.13663 28.3989 10.1876 26.2002 13.7654C24.8538 15.9564 22.9595 18.3449 20.6522 20.6522C18.3449 22.9595 15.9564 24.8538 13.7654 26.2002C10.1876 28.3989 7.13663 29.1366 5.82609 27.8261L20.1739 42.1739C21.4845 43.4845 24.5355 42.7467 28.1133 40.548C30.3042 39.2016 32.6927 37.3073 35 35C37.3073 32.6927 39.2016 30.3042 40.548 28.1133C42.7467 24.5355 43.4845 21.4845 42.1739 20.1739Z" fill="#299de0"/>
              <path fill-rule="evenodd" clip-rule="evenodd" d="M7.24189 26.4066C7.31369 26.4411 7.64204 26.5637 8.52504 26.3738C9.59462 26.1438 11.0343 25.5311 12.7183 24.4963C14.7583 23.2426 17.0256 21.4503 19.238 19.238C21.4503 17.0256 23.2426 14.7583 24.4963 12.7183C25.5311 11.0343 26.1438 9.59463 26.3738 8.52504C26.5637 7.64204 26.4411 7.31369 26.4066 7.24189C26.345 7.21246 26.143 7.14535 25.6664 7.1918C24.9745 7.25925 23.9954 7.5498 22.7699 8.14278C20.3369 9.32007 17.3369 11.4915 14.4142 14.4142C11.4915 17.3369 9.32007 20.3369 8.14278 22.7699C7.5498 23.9954 7.25925 24.9745 7.1918 25.6664C7.14534 26.143 7.21246 26.345 7.24189 26.4066ZM29.9001 10.7285C29.4519 12.0322 28.7617 13.4172 27.9042 14.8126C26.465 17.1544 24.4686 19.6641 22.0664 22.0664C19.6641 24.4686 17.1544 26.465 14.8126 27.9042C13.4172 28.7617 12.0322 29.4519 10.7285 29.9001L21.5754 40.747C21.6001 40.7606 21.8995 40.931 22.8729 40.7217C23.9424 40.4916 25.3821 39.879 27.0661 38.8441C29.1062 37.5904 31.3734 35.7982 33.5858 33.5858C35.7982 31.3734 37.5904 29.1062 38.8441 27.0661C39.879 25.3821 40.4916 23.9425 40.7216 22.8729C40.931 21.8995 40.7606 21.6001 40.747 21.5754L29.9001 10.7285ZM29.2403 4.41187L43.5881 18.7597C44.9757 20.1473 44.9743 22.1235 44.6322 23.7139C44.2714 25.3919 43.4158 27.2666 42.252 29.1604C40.8128 31.5022 38.8165 34.012 36.4142 36.4142C34.012 38.8165 31.5022 40.8128 29.1604 42.252C27.2666 43.4158 25.3919 44.2714 23.7139 44.6322C22.1235 44.9743 20.1473 44.9757 18.7597 43.5881L4.41187 29.2403C3.29027 28.1187 3.08209 26.5973 3.21067 25.2783C3.34099 23.9415 3.8369 22.4852 4.54214 21.0277C5.96129 18.0948 8.43335 14.7382 11.5858 11.5858C14.7382 8.43335 18.0948 5.9613 21.0277 4.54214C22.4852 3.8369 23.9415 3.34099 25.2783 3.21067C26.5973 3.08209 28.1187 3.29028 29.2403 4.41187Z" fill="#299de0"/>
            </svg>
          </div>
          <span class="pdf-brand-name">PymeScope</span>
        </div>
        <div class="pdf-brand-right">
          <span class="pdf-doc-title">Balance General Proforma</span>
          <span class="pdf-doc-meta">{{ headerInfo.generatedPeriod }} &nbsp;|&nbsp; Base: {{ headerInfo.basePeriod }}</span>
        </div>
        <div class="pdf-brand-divider"></div>
      </div>

      <div class="page-head">
        <div class="page-head-top">
          <div class="page-badges">
            <span class="mini-badge mini-badge-blue">PROYECCIÓN GENERADA: {{ headerInfo.generatedPeriod }}</span>
            <span class="mini-badge mini-badge-gray">PERIODO BASE: {{ headerInfo.basePeriod }}</span>
          </div>

          <button class="btn-edit" type="button" @click="editProjection">
            <span class="material-symbols-outlined">edit</span>
            <span>Editar supuestos</span>
          </button>
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
        <article v-for="(kpi, idx) in kpis" :key="idx" class="kpi-card" :class="{
          'fer-featured-red': kpi.title === 'FER' && totals.fer > 1,
          'fer-featured-green': kpi.title === 'FER' && totals.fer < -1
        }">
          <div class="kpi-top">
            <p class="kpi-title">{{ kpi.title }}</p>
            <div class="kpi-info-wrapper" v-if="kpi.title === 'FER'">
              <span class="material-symbols-outlined kpi-info-icon">info</span>
              <div class="kpi-tooltip">
                <p><strong>Fondos Externos Requeridos (FER)</strong></p>
                <p>Es la cuenta que nivela el balance general.</p>
                <ul>
                  <li><span class="text-red">Rojo:</span> Faltan fondos (se requiere financiamiento).</li>
                  <li><span class="text-green">Verde:</span> Sobran fondos (hay excedente).</li>
                </ul>
              </div>
            </div>
          </div>

          <p class="kpi-value">{{ kpi.value }}</p>

          <div class="kpi-bottom">
            <template v-if="kpi.delta">
              <span class="kpi-chip" :class="kpi.delta.startsWith('+') ? 'chip-up' : 'chip-down'">
                <span class="material-symbols-outlined">{{ kpi.delta.startsWith('+') ? 'trending_up' : 'trending_down' }}</span>
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
          <template v-if="Math.abs(totals.fer) > 1">
            <span class="equation-plus">+</span>
            <span class="equation-amount">{{ fmt(totals.fer) }}</span>
            <span class="equation-text">FER</span>
          </template>
        </div>

        <span class="equation-status" :class="{'status-ok': equation.status === 'Balance cuadrado'}">{{ equation.status }}</span>
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
              v-for="(section, idx) in assetsGroups"
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
            <span>{{ fmt(totals.activo) }}</span>
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
              v-for="(section, idx) in liabilityEquityGroups"
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

            <div class="fer-card" :class="totals.fer > 0 ? 'fer-positive' : 'fer-negative'">
              <div class="fer-left">
                <span class="material-symbols-outlined">analytics</span>
                <div>
                  <p class="fer-title">Fondos Externos Requeridos (FER)</p>
                  <p class="fer-subtitle">Cuenta niveladora del balance</p>
                </div>
              </div>

              <div class="fer-right">
                <p class="fer-value">{{ fmt(totals.fer) }}</p>
                <span class="fer-badge">{{ totals.fer > 0.01 ? "Financiamiento" : (totals.fer < -0.01 ? "Excedente" : "Equilibrado") }}</span>
              </div>
            </div>

            <div class="totals-summary">
              <div class="totals-line">
                <span>Total Pasivos</span>
                <span>{{ fmt(totals.pasivo) }}</span>
              </div>
              <div class="totals-line">
                <span>Total Capital</span>
                <span>{{ fmt(totals.capital) }}</span>
              </div>
            </div>
          </div>

          <div class="card-total card-total-dark">
            <span>Total Pasivo + Capital + FER</span>
            <span>{{ fmt(totals.pasivo + totals.capital + totals.fer) }}</span>
          </div>
        </article>
      </section>

      <div class="actions">
        <button class="btn-secondary" type="button" @click="regresarEstadoResultados">
          <span class="material-symbols-outlined">arrow_back</span>
          <span>Regresar al Estado de Resultados</span>
        </button>

        <button class="btn-secondary" type="button" @click="exportProjection" :disabled="isExporting">
          <span class="material-symbols-outlined" v-if="!isExporting">download</span>
          <span class="material-symbols-outlined" v-else>sync</span>
          <span>{{ isExporting ? 'Exportando...' : 'Exportar proyección' }}</span>
        </button>

        <button class="btn-primary" type="button" @click="finalizarProyeccion">
          Finalizar
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
                <th class="right">Periodo Base ({{ headerInfo.basePeriod }})</th>
                <th class="right">Proforma ({{ headerInfo.generatedPeriod }})</th>
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

.is-exporting {
  padding: 40px;
  background: #f8fafb;
}

.page-container {
  padding: 20px 0;
}

/* Header */
.page-head {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 22px;
  border-bottom: 1px solid #e8eff3;
}

.page-head-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.btn-edit {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  border: 1.5px solid #299de0;
  background: transparent;
  color: #299de0;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.btn-edit:hover {
  background: #299de0;
  color: white;
}

.btn-edit .material-symbols-outlined {
  font-size: 17px;
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

.mini-badge-blue { background: #eff6ff; color: #299de0; border: 1px solid #dbeafe; }
.mini-badge-gray { background: #f3f4f6; color: #507c95; }

.page-head h1 { margin: 0; font-size: 26px; font-weight: 900; color: #0e161b; }
.page-description { margin: 0; color: #507c95; font-size: 13px; font-weight: 700; line-height: 1.6; }

/* Source summary */
.source-card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.source-head { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 20px; color: #0e161b; font-size: 14px; font-weight: 900; }
.source-head .material-symbols-outlined { color: #299de0; font-size: 18px; }
.source-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 18px; }
.source-item { display: flex; flex-direction: column; gap: 4px; }
.source-label { margin: 0; color: #507c95; font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.12em; }
.source-value { margin: 0; color: #0e161b; font-size: 20px; font-weight: 900; }
.source-value-primary { color: #299de0; }
.source-note { grid-column: 1 / -1; display: flex; align-items: flex-start; gap: 8px; padding: 12px; background: rgba(239, 246, 255, 0.6); border: 1px solid #dbeafe; border-radius: 10px; }
.source-note .material-symbols-outlined { color: #299de0; font-size: 16px; margin-top: 1px; flex-shrink: 0; }
.source-note p { margin: 0; color: #507c95; font-size: 10px; line-height: 1.45; font-weight: 700; }

/* KPIs */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.kpi-card { background: #ffffff; border: 1px solid #e8eff3; border-radius: 14px; padding: 18px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04); transition: all 0.2s; }
.kpi-card:hover { border-color: #299de0; box-shadow: 0 8px 20px rgba(41, 157, 224, 0.1); }
.fer-featured-red { border: 2px solid #ef4444; background: #fef2f2; }
.fer-featured-red:hover { border-color: #dc2626; box-shadow: 0 8px 20px rgba(239, 68, 68, 0.15); }
.fer-featured-red .kpi-title { color: #b91c1c; }
.fer-featured-red .kpi-value { color: #991b1b; }

.fer-featured-green { border: 2px solid #22c55e; background: #f0fdf4; }
.fer-featured-green:hover { border-color: #16a34a; box-shadow: 0 8px 20px rgba(34, 197, 94, 0.15); }
.fer-featured-green .kpi-title { color: #15803d; }
.fer-featured-green .kpi-value { color: #166534; }
.kpi-top { display: flex; justify-content: space-between; align-items: flex-start; }
.kpi-title { margin: 0; color: #507c95; font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.05em; }

/* Tooltip styles */
.kpi-info-wrapper { position: relative; display: inline-flex; cursor: help; }
.kpi-info-icon { font-size: 16px; color: #94a3b8; transition: color 0.2s; }
.kpi-info-wrapper:hover .kpi-info-icon { color: #0e161b; }

.kpi-tooltip {
  position: absolute;
  bottom: 100%;
  right: -10px;
  margin-bottom: 12px;
  width: 250px;
  background: #ffffff;
  color: #507c95;
  border: 1px solid #e8eff3;
  padding: 16px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
  box-shadow: 0 8px 25px rgba(0,0,0,0.06);
  opacity: 0;
  visibility: hidden;
  transform: translateY(8px);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 100;
  text-transform: none;
  letter-spacing: normal;
}

.kpi-tooltip::after {
  content: '';
  position: absolute;
  bottom: -6px;
  right: 14px;
  width: 10px;
  height: 10px;
  background: #ffffff;
  border-right: 1px solid #e8eff3;
  border-bottom: 1px solid #e8eff3;
  transform: rotate(45deg);
}

.kpi-info-wrapper:hover .kpi-tooltip { opacity: 1; visibility: visible; transform: translateY(0); }
.kpi-tooltip strong { color: #0e161b; font-weight: 900; }
.kpi-tooltip p { margin: 0 0 8px 0; }
.kpi-tooltip p:last-child { margin: 0; }
.kpi-tooltip ul { margin: 0; padding-left: 16px; }
.kpi-tooltip li { margin-bottom: 6px; }
.kpi-tooltip li:last-child { margin-bottom: 0; }
.text-red { color: #dc2626; font-weight: 800; }
.text-green { color: #16a34a; font-weight: 800; }

.kpi-value { margin: 6px 0; font-size: 28px; font-weight: 900; color: #0e161b; }
.kpi-bottom { display: flex; align-items: center; gap: 8px; }
.kpi-chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 900; }
.chip-up { background: #dcfce7; color: #059669; }
.chip-down { background: #fee2e2; color: #dc2626; }
.kpi-note { color: #64748b; font-size: 11px; font-weight: 700; }

/* Equation Bar */
.equation-bar { display: flex; align-items: center; justify-content: center; gap: 24px; padding: 20px; background: #fff; border: 1px solid #e8eff3; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.equation-side, .equation-center { display: flex; flex-direction: column; align-items: center; }
.equation-amount { font-size: 20px; font-weight: 900; color: #0e161b; }
.equation-text { font-size: 10px; font-weight: 900; color: #94a3b8; text-transform: uppercase; }
.equation-equals, .equation-plus { font-size: 24px; font-weight: 300; color: #cbd5e1; }
.status-ok { background: #dcfce7; color: #059669; padding: 4px 12px; border-radius: 99px; font-weight: 900; font-size: 12px; }

/* Main Grid Balance */
.main-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 24px; }
.balance-card { background: #fff; border: 1px solid #e8eff3; border-radius: 18px; display: flex; flex-direction: column; box-shadow: 0 4px 15px rgba(0,0,0,0.03); overflow: hidden; }
.balance-card-head { padding: 18px 24px; border-bottom: 1px solid #f1f5f9; background: #fcfdfe; }
.balance-card-head h3 { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 900; }
.balance-card-body { padding: 24px; flex-grow: 1; display: flex; flex-direction: column; gap: 24px; }
.group-section { display: flex; flex-direction: column; gap: 12px; }
.group-kicker { margin: 0; font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 1px solid; padding-bottom: 6px; width: fit-content; }
.group-kicker-primary { color: #299de0; border-color: rgba(41, 157, 224, 0.2); }
.group-kicker-orange { color: #f59e0b; border-color: rgba(245, 158, 11, 0.2); }
.group-kicker-blue { color: #4f46e5; border-color: rgba(79, 70, 229, 0.2); }

.rows { display: flex; flex-direction: column; gap: 8px; }
.row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid #f8fafc; }
.row-label { font-size: 14px; font-weight: 700; color: #334155; }
.row-value { font-size: 14px; font-weight: 800; color: #0e161b; }
.subtotal { display: flex; justify-content: space-between; padding: 10px 12px; border-radius: 8px; font-size: 13px; font-weight: 900; margin-top: 4px; }
.subtotal-primary { background: #eff6ff; color: #1e40af; }
.subtotal-orange { background: #fffbeb; color: #92400e; }
.subtotal-blue { background: #f5f3ff; color: #3730a3; }

.card-total { padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; font-size: 18px; font-weight: 900; }
.card-total-primary { background: #299de0; color: #fff; }
.card-total-dark { background: #1e293b; color: #fff; }

.fer-card { display: flex; justify-content: space-between; align-items: center; padding: 16px; border-radius: 12px; border: 2px dashed; }
.fer-positive { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
.fer-negative { background: #f0fdf4; border-color: #bbf7d0; color: #166534; }
.fer-left { display: flex; align-items: center; gap: 12px; }
.fer-title { margin: 0; font-size: 14px; font-weight: 900; }
.fer-subtitle { margin: 0; font-size: 11px; font-weight: 700; opacity: 0.8; }
.fer-value { margin: 0; font-size: 18px; font-weight: 900; }
.fer-badge { font-size: 10px; padding: 2px 8px; border-radius: 99px; background: rgba(0,0,0,0.1); font-weight: 900; text-transform: uppercase; }

.totals-summary { display: flex; flex-direction: column; gap: 6px; padding-top: 10px; border-top: 1px solid #e2e8f0; }
.totals-line { display: flex; justify-content: space-between; font-size: 14px; font-weight: 900; color: #64748b; }

/* Actions */
.actions { display: flex; justify-content: flex-end; align-items: center; gap: 12px; padding-top: 10px; }

.btn-secondary,
.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 800;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary {
  border: 1px solid #e8eff3;
  background: #ffffff;
  color: #0e161b;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.btn-secondary:hover {
  background: #ffffff;
  border-color: #299de0;
  color: #299de0;
  box-shadow: 0 6px 15px rgba(41, 157, 224, 0.1);
}

.btn-primary {
  border: 1px solid #299de0;
  background: #299de0;
  color: #ffffff;
  letter-spacing: 0.05em;
  box-shadow: 0 4px 14px rgba(41, 157, 224, 0.2);
}

.btn-primary:hover {
  background: #1a8ac7;
  border-color: #1a8ac7;
  box-shadow: 0 6px 20px rgba(41, 157, 224, 0.3);
}

.btn-primary:active {
  transform: translateY(1px);
}

/* Details Panel */
.details-panel { background: #fff; border: 1px solid #e8eff3; border-radius: 16px; overflow: hidden; }
.details-summary { padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; list-style: none; user-select: none; }
.details-left { display: flex; align-items: center; gap: 12px; }
.details-left h3 { margin: 0; font-size: 16px; font-weight: 900; color: #0e161b; }
.summary-icon { transition: transform 0.2s; }
.details-panel[open] .summary-icon { transform: rotate(180deg); }
.details-badge { font-size: 11px; font-weight: 900; color: #299de0; text-transform: uppercase; letter-spacing: 0.1em; }
.details-table-wrap { overflow-x: auto; padding: 0 24px 24px; }
.details-table { width: 100%; min-width: 800px; border-collapse: collapse; }
.details-table th { padding: 12px; text-align: left; font-size: 10px; font-weight: 900; color: #94a3b8; text-transform: uppercase; border-bottom: 2px solid #f1f5f9; }
.details-table td { padding: 14px 12px; font-size: 14px; border-bottom: 1px solid #f8fafc; }
.details-table .right { text-align: right; }
.section-row td { background: #f8fafc; color: #64748b; font-weight: 900; font-size: 11px; }
.total-row td { font-weight: 900; background: #f1f5f9; }
.tone-up { color: #059669; font-weight: 800; }
.tone-down { color: #dc2626; font-weight: 800; }
.tone-neutral { color: #64748b; }

.pdf-brand { display: none; }
.is-exporting .pdf-brand { display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #299de0; }
</style>