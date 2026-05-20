<script setup>
import { ref, onMounted } from "vue";
import PdfLoadingModal from "@/components/app/PdfLoadingModal.vue";
import { useRouter, useRoute } from "vue-router";
import { db } from "@/firebase/config";
import { collection, query, orderBy, limit, getDocs, where } from "firebase/firestore";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

const router = useRouter();
const route = useRoute();
const getRouteName = (baseName) => route.path.includes('dashboard-multi') ? `${baseName}Multi` : baseName;
const projectId = route.params.id_proyecto;

// Navegar al formulario prellenado para editar supuestos
function editProjection() {
  const isHistory = route.query.isHistory === 'true';
  const lsKeyConfig = isHistory ? 'history_projection_config' : 'current_projection_config';
  const configRaw = localStorage.getItem(lsKeyConfig);
  const config = configRaw ? JSON.parse(configRaw) : {};
  router.push({
    name: getRouteName("FormularioEstadoDeResultados"),
    query: {
      periodoBaseId: config.periodoBaseId || '',
      label: config.periodoBase || '',
      periodDate: config.periodDate || '',
      modo: 'editar',
      isHistory: isHistory ? 'true' : 'false'
    }
  });
}

const headerInfo = ref({
  companyName: "",
  generatedPeriod: "...",
  basePeriod: "...",
  title: "Proyección Proforma - Estado de Resultados",
  subtitle: "Visualiza la proyección del estado de resultados generada a partir del último periodo registrado y los supuestos definidos.",
});

const kpis = ref([
  { title: "Ingresos proyectados", value: "$0", delta: "0%", note: "vs periodo base", featured: false },
  { title: "Utilidad operativa proyectada", value: "$0", delta: "0%", note: "vs periodo base", featured: false },
  { title: "Utilidad neta proyectada", value: "$0", delta: "0%", note: "vs periodo base", featured: true },
  { title: "Margen neto proyectado", value: "0%", delta: "0%", note: "vs periodo base", featured: false },
]);

const projectionRows = ref([]);
const esMultiperiodo = ref(false);
const periodosER = ref([]);      // [{periodo, numero, er: {tablas_proyectadas, utilidad_neta, ...}}]
const configMulti = ref({});
const tabActivoMulti = ref(0);   // tab activo en la vista multiperiodo

// Textos dinámicos
const utilidadNetaStr = ref("$0");

// PDF Export
const pdfZone = ref(null);
const isExporting = ref(false);

// Helper para formatear moneda
const fmt = (val) => {
  if (val === undefined || val === null) return "$0.00";
  const num = Number(val);
  const ABS = Math.abs(num).toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return num < 0 ? `-$${ABS}` : `$${ABS}`;
};

// Helper para porcentajes
const pct = (val) => {
  const num = Number(val) || 0;
  return (num >= 0 ? "+" : "") + num.toFixed(1) + "%";
};

onMounted(async () => {
  window.scrollTo(0, 0);

  // ── Detectar si viene de proyección multiperiodo ──────────────────────────
  const multiResultadosRaw = localStorage.getItem("multiperiodo_er_resultados");
  const multiConfigRaw = localStorage.getItem("multiperiodo_config");

  if (multiResultadosRaw && multiConfigRaw) {
    const multiData = JSON.parse(multiResultadosRaw);
    const multiConfig = JSON.parse(multiConfigRaw);
    
    // Verificar que sea una respuesta del endpoint /multiperiodo/er
    if (multiData.periodos_er && multiData.periodos_er.length > 0) {
      // Solo activar multi si la navegación fue intencional desde generarProyeccionMulti()
      const esNavegacionMulti = sessionStorage.getItem("navegacion_multiperiodo") === "true";
      if (esNavegacionMulti) {
        sessionStorage.removeItem("navegacion_multiperiodo"); // limpiar flag inmediatamente
        esMultiperiodo.value = true;
        periodosER.value = multiData.periodos_er;
        configMulti.value = multiConfig;
        return;
      }
    }
  }
  // Si llega aquí → flujo monoperiodo normal (código existente sin cambios)

  if (projectId) {
    try {
      const { doc, getDoc } = await import("firebase/firestore");
      const projectDocRef = doc(db, "proyectos", projectId);
      const projectDocSnap = await getDoc(projectDocRef);
      if (projectDocSnap.exists()) {
        const pData = projectDocSnap.data();
        headerInfo.value.companyName = pData.empresa || pData.nombre || "";
      }
    } catch (err) {
      console.error("Error al recuperar información del proyecto:", err);
    }
  }

  const isHistory = route.query.isHistory === 'true';
  const lsKeyResult = isHistory ? 'history_projection_result' : 'current_projection_result';
  const lsKeyConfig = isHistory ? 'history_projection_config' : 'current_projection_config';

  let resultsRaw = localStorage.getItem(lsKeyResult);
  let configRaw = localStorage.getItem(lsKeyConfig);

  // Validación de integridad: Si los datos en localStorage no parecen un ER, los ignoramos y forzamos descarga
  if (resultsRaw) {
    const test = JSON.parse(resultsRaw);
    if (!test.ventas && !test.tablas_proyectadas?.some(r => r.concepto.toLowerCase().includes('ventas'))) {
      resultsRaw = null;
      configRaw = null;
    }
  }

  if (!resultsRaw) {
    console.warn("No se encontraron resultados de proyección. Regresando...");
    router.push({ name: getRouteName('proyecciones') });
    return;
  }

  const results = JSON.parse(resultsRaw);
  const config = JSON.parse(configRaw || '{}');

  // 1. Actualizar Header
  headerInfo.value.generatedPeriod = config.periodoProyectado || "Proyectado";
  headerInfo.value.basePeriod = config.periodoBase || "Base";

  // 2. Extraer Valores Base para Deltas
  const basePeriodText = `vs ${headerInfo.value.basePeriod}`;
  const rawRows = results.tablas_proyectadas || [];
  
  const ventasBaseRow = rawRows.find(f => f.concepto.toLowerCase().includes('ventas'));
  const costoBaseRow  = rawRows.find(f => f.concepto.toLowerCase().includes('costo'));
  const ventasBase = ventasBaseRow?.valor_base || 1;
  const costoBase = costoBaseRow?.valor_base || 0;
  const utilidadBrutaBase = ventasBase - costoBase;
  
  const gastosBase = rawRows
    .filter(f => f.concepto.toLowerCase().includes('gastos') && !f.concepto.toLowerCase().includes('costo'))
    .reduce((sum, f) => sum + (f.valor_base || 0), 0);
  const utilidadOperativaBase = utilidadBrutaBase - gastosBase;
  
  const otrosIngresosBase = rawRows
    .filter(f => f.concepto.toLowerCase().includes('otros ingresos') || f.concepto.toLowerCase().includes('productos financieros'))
    .reduce((sum, f) => sum + (f.valor_base || 0), 0);
  const utilidadAntesImpuestosBase = utilidadOperativaBase + otrosIngresosBase;
  const impuestosBase = config.incluirImpuestos ? (utilidadAntesImpuestosBase * 0.30) : 0; 
  const utilidadNetaBase = utilidadAntesImpuestosBase - impuestosBase;

  // 3. Calcular Deltas
  const deltaVentas = ((results.ventas / ventasBase) - 1) * 100;
  const deltaOp = utilidadOperativaBase !== 0 ? ((results.utilidad_operativa / Math.abs(utilidadOperativaBase)) - Math.sign(utilidadOperativaBase)) * 100 : 0;
  const deltaNeta = utilidadNetaBase !== 0 ? ((results.utilidad_neta / Math.abs(utilidadNetaBase)) - Math.sign(utilidadNetaBase)) * 100 : 0;

  // 4. Actualizar KPIs
  kpis.value[0].value = fmt(results.ventas);
  kpis.value[0].delta = pct(deltaVentas);
  kpis.value[0].note = basePeriodText;

  kpis.value[1].value = fmt(results.utilidad_operativa);
  kpis.value[1].delta = pct(deltaOp); 
  kpis.value[1].note = basePeriodText;
  
  kpis.value[2].value = fmt(results.utilidad_neta);
  kpis.value[2].delta = pct(deltaNeta); 
  kpis.value[2].note = basePeriodText;
  
  const margenNeto = (results.ventas !== 0) ? (results.utilidad_neta / results.ventas) * 100 : 0;
  const margenNetoBase = (ventasBase !== 0) ? (utilidadNetaBase / ventasBase) * 100 : 0;
  const deltaMargen = margenNeto - margenNetoBase;

  kpis.value[3].value = margenNeto.toFixed(1) + "%";
  kpis.value[3].delta = (deltaMargen >= 0 ? '+' : '') + deltaMargen.toFixed(1) + " pts";
  kpis.value[3].note = basePeriodText;

  // Actualizar string reactivo para el cuadro inferior
  utilidadNetaStr.value = fmt(results.utilidad_neta);

  // 4. Mapear Filas
  const rows = [];

  // --- Sección Ingresos ---
  rows.push({ type: "section", label: "Ingresos" });
  rawRows.filter(f => 
    f.concepto.toLowerCase().includes('ventas') || 
    f.concepto.toLowerCase().includes('otros ingresos') ||
    f.concepto.toLowerCase().includes('productos financieros')
  ).forEach(f => {
    rows.push({
      type: "row",
      concept: f.concepto,
      base: fmt(f.valor_base),
      assumption: pct(f.variacion_aplicada),
      participation: ((f.valor_proyectado / results.ventas) * 100).toFixed(1) + "%",
      proforma: fmt(f.valor_proyectado),
      variation: pct(f.variacion_aplicada),
      variationTone: f.variacion_aplicada >= 0 ? "up" : "down"
    });
  });

  // --- Sección Costos y Gastos ---

  rows.push({ type: "subtotal", concept: "Utilidad bruta", base: fmt(utilidadBrutaBase), proforma: fmt(results.utilidad_bruta), variation: "—" });
  rows.push({ type: "section", label: "Costos y gastos" });
  
  rawRows.filter(f => 
    f.concepto.toLowerCase().includes('gastos') &&
    !f.concepto.toLowerCase().includes('costo')
  ).forEach(f => {
    rows.push({
      type: "row",
      concept: f.concepto,
      base: fmt(f.valor_base),
      assumption: pct(f.variacion_aplicada),
      participation: ((f.valor_proyectado / results.ventas) * 100).toFixed(1) + "%",
      proforma: fmt(f.valor_proyectado),
      variation: pct(f.variacion_aplicada),
      variationTone: f.variacion_aplicada >= 0 ? "down" : "up" 
    });
  });

  rows.push({ 
    type: "subtotal", 
    concept: "Utilidad de operación", 
    base: fmt(utilidadOperativaBase),
    proforma: fmt(results.utilidad_operativa), 
    variation: "—",
    highlightValue: true 
  });
  
  rows.push({ 
    type: "subtotal", 
    concept: "Utilidad antes de impuestos", 
    base: fmt(utilidadAntesImpuestosBase),
    proforma: fmt(results.utilidad_antes_impuestos), 
    variation: "—",
    highlightValue: true 
  });

  // --- Sección Impuestos ---
  if (config.incluirImpuestos === true) {
    rows.push({ type: "section", label: "Impuestos" });
    rows.push({
      type: "row",
      concept: "Total impuestos (PTU + ISR)",
      base: "—",
      assumption: "Calculado sobre utilidad",
      participation: ((results.impuestos / results.ventas) * 100).toFixed(1) + "%",
      proforma: fmt(results.impuestos),
      variation: "—"
    });
  }

  rows.push({
    type: "final",
    concept: "Utilidad neta del ejercicio",
    base: fmt(utilidadNetaBase),
    proforma: fmt(results.utilidad_neta),
    variation: "—",
    variationTone: "final-up"
  });

  projectionRows.value = rows;

  // 5. Interpretación dinámica inteligente
  // Interpretation points removed
});

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

async function exportProjection() {
  if (isExporting.value) return;
  isExporting.value = true;
  await new Promise(r => setTimeout(r, 100));

  try {
    const el = pdfZone.value;
    const canvas = await html2canvas(el, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
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

    const config = JSON.parse(localStorage.getItem('current_projection_config') || '{}');
    const periodo = (config.periodoProyectado || 'Proyeccion').replace(/\s+/g, '-');
    pdf.save(`proyeccion-proforma-${periodo}.pdf`);
  } catch (err) {
    console.error("Error generando PDF:", err);
    alert("No se pudo generar el PDF. Intenta de nuevo.");
  } finally {
    isExporting.value = false;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

async function continueToBalance() {
  const isHistory = route.query.isHistory === 'true';
  const lsKeyConfig = isHistory ? 'history_projection_config' : 'current_projection_config';
  const lsKeyResultBG = isHistory ? 'history_balance_result' : 'current_balance_result';
  
  const configRaw = localStorage.getItem(lsKeyConfig);
  const config = configRaw ? JSON.parse(configRaw) : {};
  const periodoBaseId = config.periodoBaseId || '';

  console.log("[continueToBalance] projectId:", projectId, "periodoBaseId:", periodoBaseId, "isHistory:", isHistory);

  if (isHistory) {
    // 1. Prioridad: Revisar si ya tenemos el resultado en localStorage (ya fue cargado por ProyeccionesView)
    const existingBG = localStorage.getItem(lsKeyResultBG);
    if (existingBG) {
      console.log("[continueToBalance] Resultado encontrado en localStorage. Navegando...");
      router.push({ 
        name: getRouteName("ProyeccionProformaBalanceGeneral"),
        query: { isHistory: 'true' }
      });
      return;
    }

    // 2. Si no está en LS, intentar buscarlo en Firestore para reconstruir la sesión
    if (projectId && periodoBaseId) {
      try {
        const proyeccionesBGRef = collection(db, "proyectos", projectId, "proyecciones_bg");
        let bgSnapshot;
        
        // Intento A: Por er_id exacto
        if (config.erId) {
          const qBGExact = query(proyeccionesBGRef, where("er_id", "==", config.erId), limit(1));
          bgSnapshot = await getDocs(qBGExact);
        }

        // Intento B: Fallback por periodo_base_id (proyecciones antiguas)
        if ((!bgSnapshot || bgSnapshot.empty) && periodoBaseId) {
          const qBGFallback = query(
            proyeccionesBGRef, 
            where("periodo_base_id", "==", periodoBaseId), 
            orderBy("created_at", "desc"),
            limit(1)
          );
          bgSnapshot = await getDocs(qBGFallback);
        }

        if (bgSnapshot && !bgSnapshot.empty) {
          const bgDoc = bgSnapshot.docs[0];
          const bgData = bgDoc.data();
          console.log("[continueToBalance] BG encontrado en Firestore. Reconstruyendo localStorage...");

          localStorage.setItem("history_balance_result", JSON.stringify(bgData.resultados));
          localStorage.setItem("history_balance_config", JSON.stringify({
            periodoBase: config.periodoBase || "",
            periodoProyectado: bgData.periodo_proyectado || "",
            inflacion: bgData.inflacion_esperada || 0,
            periodoBaseId: bgData.periodo_base_id || periodoBaseId,
            periodDate: config.periodDate || "",
            bgId: bgDoc.id,
            erId: config.erId || null,
          }));
          if (bgData.supuestos) {
            localStorage.setItem("history_balance_supuestos", JSON.stringify(bgData.supuestos));
          }
          router.push({ 
            name: getRouteName("ProyeccionProformaBalanceGeneral"),
            query: { isHistory: 'true' }
          });
          return;
        }
      } catch (err) {
        console.error("[continueToBalance] Error al consultar Firestore:", err);
      }
    }
  } else {
    // Proyección activa (nueva): Revisar si el usuario ya calculó el BG en esta sesión actual
    const currentBgResult = localStorage.getItem('current_balance_result');
    if (currentBgResult) {
      router.push({ name: getRouteName("ProyeccionProformaBalanceGeneral") });
      return;
    }
  }

  // No existe BG en la sesión activa o no se encontró en historial → ir al formulario
  console.log("[continueToBalance] No se encontró BG previo. Redirigiendo al formulario...");
  router.push({ 
    name: getRouteName("FormularioBalanceGeneral"),
    query: {
      periodoBaseId: periodoBaseId,
      label: config.periodoBase || '',
      periodDate: config.periodDate || '',
      isHistory: isHistory ? 'true' : 'false',
      erId: config.erId || ''
    }
  });
}

function continueToBalanceMulti() {
  // Verificar si ya existe BG multiperiodo calculado
  const bgExistente = localStorage.getItem("multiperiodo_bg_resultados");
  if (bgExistente) {
    router.push({
      name: "ProyeccionProformaBalanceGeneralMulti",
      params: { id_proyecto: projectId }
    });
    return;
  }
  
  sessionStorage.setItem("navegacion_multiperiodo_bg", "true");
  // Navegar al formulario BG multiperiodo
  router.push({
    name: "FormularioBalanceGeneralMulti",
    params: { id_proyecto: projectId },
    query: {
      periodoBaseId: configMulti.value.periodoBaseId || "",
      label: configMulti.value.periodoBase || "",
      periodDate: configMulti.value.periodDate || "",
    }
  });
}

</script>

<template>
  <PdfLoadingModal :isOpen="isExporting" documentName="tu Estado de Resultados Proforma" />
  <!-- Sección mono — solo cuando NO es multiperiodo -->
  <div v-if="!esMultiperiodo" class="page-container">
    <div class="wrap" :class="{ 'is-exporting': isExporting }" ref="pdfZone">
      <div class="pdf-brand">
        <div class="pdf-brand-left">
          <div class="pdf-logo">
            <img src="/logo.png" alt="Logo PymeScope" style="width: 100%;" />
          </div>
          <span class="pdf-brand-name">PymeScope</span>
        </div>
        <div class="pdf-brand-right">
          <span class="pdf-doc-title">Estado de Resultados Proforma</span>
          <span class="pdf-doc-meta">{{ headerInfo.generatedPeriod }} &nbsp;|&nbsp; Base: {{ headerInfo.basePeriod }}</span>
        </div>
        <div class="pdf-brand-divider"></div>
      </div>

      <section class="page-head">
        <div class="page-head-top">
          <div class="page-badges">
            <span class="mini-badge mini-badge-blue">
              PROYECCIÓN GENERADA: {{ headerInfo.generatedPeriod }}
            </span>
            <span class="mini-badge mini-badge-gray">
              PERIOD BASE: {{ headerInfo.basePeriod }}
            </span>
          </div>

          <button class="btn-edit no-print" type="button" @click="editProjection" data-html2canvas-ignore="true">
            <span class="material-symbols-outlined">edit</span>
            <span>Editar supuestos</span>
          </button>
        </div>

        <h1 class="page-title">
          <span v-if="headerInfo.companyName" class="company-name-inline">
            <span class="material-symbols-outlined company-icon">apartment</span>
            {{ headerInfo.companyName }} 
            <span class="title-separator">|</span>
          </span>
          {{ headerInfo.title }}
        </h1>
        <p class="page-description">{{ headerInfo.subtitle }}</p>
      </section>

      <section class="kpis">
        <article v-for="(kpi, idx) in kpis" :key="idx" class="kpi-card" :class="{ featured: kpi.featured }">
          <div class="kpi-top">
            <p class="kpi-title" :class="{ 'kpi-title-featured': kpi.featured }">{{ kpi.title }}</p>
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
              <span v-if="kpi.note" class="kpi-note">{{ kpi.note }}</span>
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
                <th class="right">Periodo base ({{ headerInfo.basePeriod }})</th>
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
                <tr v-else :class="{'subtotal-row': row.type === 'subtotal', 'final-row': row.type === 'final'}">
                  <td :class="conceptClass(row.conceptTone)">{{ row.concept }}</td>
                  <td class="right" :class="{ strong: row.type !== 'row' }">{{ row.base }}</td>
                  <td :class="assumptionClass(row.assumptionTone)">{{ row.assumption }}</td>
                  <td class="right" :class="{ strong: row.type !== 'row' || row.highlightValue }">{{ row.participation }}</td>
                  <td class="right" :class="{ strong: row.type !== 'row' || row.highlightValue, 'proforma-highlight': row.highlightValue && row.type === 'subtotal' }">{{ row.proforma }}</td>
                  <td class="right">
                    <span :class="variationClass(row.variationTone)">{{ row.variation }}</span>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </section>

      <section class="next-step-section">
        <article class="next-card">
          <div class="next-head">
            <div class="next-icon"><span class="material-symbols-outlined">arrow_forward</span></div>
            <h4>Siguiente paso: Balance General Proforma</h4>
          </div>
          <p>
            La <strong>Utilidad neta proyectada de {{ utilidadNetaStr }}</strong> se integrará automáticamente en la sección de Capital Contable del Balance General Proforma a realizarse como paso siguiente.
          </p>
          <div class="next-status">
            <span>Listo para procesar</span>
            <div class="pulse-dot"></div>
          </div>
        </article>
      </section>
    </div>

    <section class="actions">
      <div class="actions-spacer"></div>
      <div class="actions-buttons">
        <button class="btn-secondary" type="button" @click="exportProjection" :disabled="isExporting">
          <span class="material-symbols-outlined" v-if="!isExporting">download</span>
          <span class="material-symbols-outlined" v-else>sync</span>
          <span>{{ isExporting ? 'Exportando...' : 'Exportar proyección' }}</span>
        </button>
        <button class="btn-primary" type="button" @click="continueToBalance">
          Continuar al Balance
        </button>
      </div>
    </section>
  </div>

  <!-- ── VISTA MULTIPERIODO ── -->
  <div v-if="esMultiperiodo" class="multi-results-wrap">
    
    <!-- Header -->
    <div class="multi-results-header">
      <div>
        <h2>Estado de Resultados Proforma — Multiperiodo</h2>
        <p class="multi-subtitle">
          Base: <strong>{{ configMulti.periodoBase }}</strong> · 
          {{ periodosER.length }} periodos proyectados · 
          {{ configMulti.periodicidad }}
        </p>
      </div>
      <button class="btn-primary" type="button" @click="continueToBalanceMulti">
        <span>Continuar al Balance General</span>
        <span class="material-symbols-outlined">arrow_forward</span>
      </button>
    </div>

    <!-- Tabs de periodos -->
    <div class="multi-tabs">
      <button
        v-for="(p, idx) in periodosER"
        :key="p.periodo"
        class="multi-tab"
        :class="{ active: tabActivoMulti === idx }"
        type="button"
        @click="tabActivoMulti = idx"
      >
        {{ p.periodo }}
      </button>
    </div>

    <!-- Resultados del periodo activo -->
    <div v-for="(periodoData, idx) in periodosER" :key="`res-${idx}`" v-show="tabActivoMulti === idx">
      <div class="multi-kpis">
        <div class="kpi-card">
          <span class="kpi-label">Ventas</span>
          <span class="kpi-value">${{ periodoData.er.ventas?.toLocaleString('es-MX', {minimumFractionDigits: 2}) }}</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Utilidad Bruta</span>
          <span class="kpi-value">${{ periodoData.er.utilidad_bruta?.toLocaleString('es-MX', {minimumFractionDigits: 2}) }}</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Utilidad Operativa</span>
          <span class="kpi-value">${{ periodoData.er.utilidad_operativa?.toLocaleString('es-MX', {minimumFractionDigits: 2}) }}</span>
        </div>
        <div class="kpi-card" :class="{ negative: periodoData.er.utilidad_neta < 0 }">
          <span class="kpi-label">Utilidad Neta</span>
          <span class="kpi-value">${{ periodoData.er.utilidad_neta?.toLocaleString('es-MX', {minimumFractionDigits: 2}) }}</span>
        </div>
      </div>

      <!-- Tabla de resultados -->
      <div class="multi-tabla-card">
        <table class="multi-tabla">
          <thead>
            <tr>
              <th>Concepto</th>
              <th>Base</th>
              <th>Var %</th>
              <th>Proyectado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fila in periodoData.er.tablas_proyectadas" :key="fila.concepto">
              <td>{{ fila.concepto }}</td>
              <td>${{ fila.valor_base?.toLocaleString('es-MX', {minimumFractionDigits: 2}) }}</td>
              <td>{{ fila.variacion_aplicada?.toFixed(1) }}%</td>
              <td :class="{ negative: fila.valor_proyectado < 0 }">
                ${{ fila.valor_proyectado?.toLocaleString('es-MX', {minimumFractionDigits: 2}) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

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

.page-container {
  display: flex;
  flex-direction: column;
  gap: 0;
}

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

.page-head h1.page-title {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.company-name-inline {
  color: #299de0;
  font-weight: 900;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.company-icon {
  font-size: 28px;
  font-weight: 300;
  margin-bottom: 2px;
}

.title-separator {
  color: #cbd5e1;
  font-weight: 300;
  margin: 0 6px;
}

.page-description {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

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

.next-card {
  position: relative;
  border-radius: 14px;
  padding: 22px;
  overflow: hidden;
  background: rgba(239, 246, 255, 0.55);
  border: 2px dashed #299de0;
}

.next-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.next-head h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.next-icon {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: #299de0;
  color: #ffffff;
}

.next-icon .material-symbols-outlined {
  font-size: 16px;
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

.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 20px;
  margin-top: 24px;
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

.btn-primary:active,
.btn-secondary:active {
  transform: translateY(1px);
}

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
}

@keyframes pulse {
  0% { opacity: 0.35; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.15); }
  100% { opacity: 0.35; transform: scale(0.9); }
}

.pdf-brand {
  display: none;
  flex-direction: column;
  gap: 0;
  margin-bottom: 20px;
}

.is-exporting .pdf-brand {
  display: flex;
}

.pdf-brand-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pdf-logo {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.pdf-logo svg {
  width: 100%;
  height: 100%;
}

.pdf-brand-name {
  font-size: 22px;
  font-weight: 900;
  color: #0e161b;
  letter-spacing: -0.02em;
}

.pdf-brand-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-left: auto;
  gap: 2px;
}

.pdf-doc-title {
  font-size: 14px;
  font-weight: 800;
  color: #0e161b;
}

.pdf-doc-meta {
  font-size: 11px;
  font-weight: 600;
  color: #507c95;
}

.pdf-brand-divider {
  margin-top: 12px;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, #299de0 0%, #e8eff3 100%);
  border-radius: 2px;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.multi-results-wrap { display: flex; flex-direction: column; gap: 16px; padding: 24px; max-width: 1100px; margin: 0 auto; }
.multi-results-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; }
.multi-results-header h2 { margin: 0 0 6px; font-size: 22px; font-weight: 900; color: #0e161b; }
.multi-subtitle { margin: 0; font-size: 13px; color: #507c95; font-weight: 600; }
.multi-tabs { display: flex; gap: 8px; flex-wrap: wrap; border-bottom: 2px solid #e8eff3; padding-bottom: 0; }
.multi-tab { padding: 10px 18px; border: none; background: none; font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.15s; }
.multi-tab.active { color: #0e161b; border-bottom-color: #299de0; }
.multi-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.kpi-card { background: white; border: 1px solid #e8eff3; border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 6px; }
.kpi-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-value { font-size: 20px; font-weight: 900; color: #0e161b; }
.kpi-card.negative .kpi-value { color: #dc2626; }
.multi-tabla-card { background: white; border: 1px solid #e8eff3; border-radius: 12px; overflow: hidden; }
.multi-tabla { width: 100%; border-collapse: collapse; font-size: 13px; }
.multi-tabla th { text-align: left; padding: 10px 16px; background: #f8fafc; font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #e8eff3; }
.multi-tabla th:not(:first-child) { text-align: right; }
.multi-tabla td { padding: 10px 16px; border-bottom: 1px solid #f1f5f9; color: #0e161b; }
.multi-tabla td:not(:first-child) { text-align: right; font-variant-numeric: tabular-nums; }
.multi-tabla tr:last-child td { border-bottom: none; }
.multi-tabla td.negative { color: #dc2626; }
.btn-primary { display: flex; align-items: center; gap: 8px; padding: 10px 20px; background: #0e161b; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; }
</style>
