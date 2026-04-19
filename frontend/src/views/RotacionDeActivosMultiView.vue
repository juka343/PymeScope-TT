<script setup>
import { computed, ref, onMounted } from "vue";
import { collection, getDocs } from "firebase/firestore";
import { db } from "@/firebase/config";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const projectId = route.params.id_proyecto;

const centroDeAprendizaje = () => {
  const routeData = router.resolve({ name: "teoriaRotacion" });
  window.open(routeData.href, "_blank");
};

const loading = ref(true);
const rawPeriods = ref([]);
const metrics = ref([]);
const activeKpi = ref("activosTotales");
const tableRows = ref([]);

const currencyFmt = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const parseVal = (val) => {
  if (!val) return 0;
  if (typeof val === 'number') return val;
  return parseFloat(val.toString().replace(/[^0-9.-]/g, ''));
};

const fetchPeriods = async () => {
  try {
    if (!projectId) return;

    const periodosRef = collection(db, "proyectos", projectId, "periodos");
    const snapshot = await getDocs(periodosRef);

    let loaded = [];
    snapshot.forEach((docSnap) => {
      const d = docSnap.data();
      if (d.analisis_rotacion) {
        loaded.push({
          id: docSnap.id,
          label: d.label || "Periodo",
          periodDate: d.periodDate || d.label,
          rotacion: d.analisis_rotacion || { datos_crudos: {}, kpis: [] },
          liquidez: d.analisis_liquidez || { datos_crudos: {} },
          estructura: d.analisis_estructura || { datos_crudos: {} },
        });
      }
    });

    loaded.sort((a, b) => a.periodDate.localeCompare(b.periodDate));
    rawPeriods.value = loaded;
    
    if (loaded.length > 0) {
      generateDashboardData();
    }
  } catch (error) {
    console.error("Error cargando multiperiodo rotación:", error);
  } finally {
    loading.value = false;
  }
};

const generateDashboardData = () => {
  const periods = rawPeriods.value;
  const labels = periods.map(p => p.label);

  const findKpi = (kpis, keyword) => {
    if (!kpis) return 0;
    const item = kpis.find(k => k.label.toLowerCase().includes(keyword.toLowerCase()));
    return item ? parseVal(item.value) : 0;
  };

  const dataCobrar = periods.map(p => findKpi(p.rotacion.kpis, "cartera")); // En tu backend se llama "Rotación de la Cartera"
  const dataRecaudo = periods.map(p => findKpi(p.rotacion.kpis, "recaudo"));
  const dataInventarios = periods.map(p => findKpi(p.rotacion.kpis, "inventarios"));
  const dataFijos = periods.map(p => findKpi(p.rotacion.kpis, "fijos"));
  const dataActivosTotales = periods.map(p => findKpi(p.rotacion.kpis, "totales"));

  function buildChart(values, title, subtitle, legendLabel, type = "times") {
    const maxFallback = type === "days" ? 30 : 1;
    const maxVal = Math.max(...values, maxFallback);
    let minVal = Math.min(...values, 0);

    if (minVal > 0 && type !== "days") minVal = 0;

    const rawRange = maxVal - minVal;

    let step;
    if (type === "days") {
      step = 5;
      if (rawRange > 30) step = 10;
    } else {
      step = 0.2;
      if (rawRange > 2) step = 0.5;
      if (rawRange > 5) step = 1;
      if (rawRange > 15) step = 5; // Para rotaciones muy altas
    }

    const yMin = Math.floor(minVal / step) * step;
    const yMax = Math.ceil(maxVal / step) * step;
    const finalRange = Math.max(yMax - yMin, step);

    const fmtLabel = (val) => {
      if (type === "days") return `${Math.round(val)} d`;
      return `${val.toFixed(1)}x`;
    };

    const yAxisLabels = [
      fmtLabel(yMax),
      fmtLabel(yMax - finalRange / 3),
      fmtLabel(yMax - (finalRange / 3) * 2),
      fmtLabel(yMin),
    ];

    const xStep = values.length > 1 ? 600 / (values.length - 1) : 0;

    const points = values.map((val, i) => {
      const x = values.length > 1 ? 100 + i * xStep : 400;
      const y = 230 - ((val - yMin) / finalRange) * 160;
      return { x, y, label: labels[i], bold: i === values.length - 1, value: val, type };
    });

    const lastVal = values[values.length - 1];
    const prevVal = values.length > 1 ? values[values.length - 2] : lastVal;
    const delta = lastVal - prevVal;

    // Lógica de colores (Recaudo es mejor si baja, los demás son mejores si suben)
    let isPositive = delta >= 0;
    if (type === "days") isPositive = delta <= 0; 
    
    // Status visual
    let status = "warn";
    if (legendLabel === "Rotación CxC") status = lastVal > 0 ? "ok" : "warn";
    else if (type === "days") status = (lastVal <= 60 && lastVal > 0) ? "ok" : "warn";
    else status = lastVal >= 1 ? "ok" : "warn";

    return {
      kpiValue: type === "days" ? `${Math.round(lastVal)} días` : `${lastVal.toFixed(1)}x`,
      status,
      deltaStyle: isPositive ? "positive" : "negative",
      deltaIcon: delta >= 0 ? "trending_up" : "trending_down",
      deltaValue: type === "days" ? `${delta > 0 ? "+" : ""}${Math.round(delta)} días` : `${delta > 0 ? "+" : ""}${delta.toFixed(1)}`,
      deltaNote: values.length > 1 ? `vs ${labels[labels.length - 2]}` : "Sin periodo previo",
      chartTitle: title,
      chartSubtitle: subtitle,
      legendLabel,
      yAxisLabels,
      points,
      type,
    };
  }

  metrics.value = [
    { key: "cobrar", label: "Rotación de Cuentas por Cobrar", ...buildChart(dataCobrar, "Evolución de Rotación de CxC", "Velocidad con la que la empresa recupera su cartera", "Rotación CxC", "times") },
    { key: "recaudo", label: "Periodo Promedio de Recaudo", ...buildChart(dataRecaudo, "Evolución del Periodo Promedio de Recaudo", "Tiempo promedio que tarda la empresa en cobrar", "Periodo de Cobro", "days") },
    { key: "inventarios", label: "Rotación de Inventarios", ...buildChart(dataInventarios, "Evolución de Rotación de Inventarios", "Frecuencia con la que el inventario se convierte en ventas", "Rotación Inventarios", "times") },
    { key: "fijos", label: "Rotación de Activos Fijos", ...buildChart(dataFijos, "Evolución de Rotación de Activos Fijos", "Nivel de aprovechamiento de la infraestructura productiva", "Activos Fijos", "times") },
    { key: "activosTotales", label: "Rotación de Activos Totales", ...buildChart(dataActivosTotales, "Evolución de Rotación de Activos Totales", "Tendencia de eficiencia operativa en los últimos trimestres", "Rotación Activos", "times") },
  ];

  // Construir Tabla (Orden Ascendente)
  tableRows.value = periods.map((p, i) => {
    const crudos = p.rotacion.datos_crudos || {};
    return {
      period: p.label,
      ventas: currencyFmt.format(crudos.ventas_netas || 0),
      activo: currencyFmt.format(crudos.activo_total || 0),
      rotacionActivos: `${dataActivosTotales[i].toFixed(2)}x`,
      rotacionInventarios: `${dataInventarios[i].toFixed(1)}x`,
      periodoCobro: `${Math.round(dataRecaudo[i])} días`,
      highlight: i === periods.length - 1,
    };
  });
};

const selectedKpi = computed(() => {
  if (metrics.value.length === 0) return null;
  return metrics.value.find((m) => m.key === activeKpi.value) || metrics.value[0];
});

function setActive(key) { activeKpi.value = key; }

const hoveredPoint = ref(null);
function showTooltip(point) { hoveredPoint.value = point; }
function hideTooltip() { hoveredPoint.value = null; }

const baselineY = 230;
const linePath = computed(() => {
  if (!selectedKpi.value) return "";
  const pts = selectedKpi.value.points;
  if (!pts.length) return "";
  return pts.map((p, i) => (i === 0 ? `M${p.x} ${p.y}` : `L${p.x} ${p.y}`)).join(" ");
});
const areaPath = computed(() => {
  if (!selectedKpi.value) return "";
  const pts = selectedKpi.value.points;
  if (!pts.length) return "";
  const first = pts[0];
  const last = pts[pts.length - 1];
  const mid = pts.map((p) => `L${p.x} ${p.y}`).join(" ");
  return `M${first.x} ${baselineY} L${first.x} ${first.y} ${mid} L${last.x} ${baselineY} Z`;
});

// --- LÓGICA DE DONUTS (Último periodo) ---
const lastPeriodData = computed(() => rawPeriods.value.length > 0 ? rawPeriods.value[rawPeriods.value.length - 1] : null);

const activoCirculante = computed(() => {
  if (!lastPeriodData.value) return { total: "$0", segments: [] };
  
  const rotCrudos = lastPeriodData.value.rotacion?.datos_crudos || {};
  const liqCrudos = lastPeriodData.value.liquidez?.datos_crudos || {};

  const aCirculanteTotal = liqCrudos.activo_circulante || 0;
  const cxc = rotCrudos.cuentas_por_cobrar || 0;
  const inventario = rotCrudos.inventario || 0;
  
  let otrosActivos = aCirculanteTotal - (cxc + inventario);
  if (otrosActivos < 0) otrosActivos = 0; 
  
  const items = [
    { label: "Cuentas por Cobrar", value: cxc, color: "#1e293b" },
    { label: "Inventarios", value: inventario, color: "#299de0" },
    { label: "Efectivo y Otros", value: otrosActivos, color: "#507c95" }
  ].filter(i => i.value > 0);

  const totalCálculo = items.reduce((acc, curr) => acc + curr.value, 0) || 1; 
  
  let currentOffset = 0;
  const segments = items.map(item => {
    const pct = (item.value / totalCálculo) * 100;
    const dasharray = `${pct} 100`;
    const dashoffset = -currentOffset;
    currentOffset += pct;
    return { ...item, pct: pct.toFixed(1), dasharray, dashoffset };
  });

  return {
    total: aCirculanteTotal >= 1000000 ? `$${(aCirculanteTotal/1000000).toFixed(1)}M` : currencyFmt.format(aCirculanteTotal),
    segments
  };
});

const activosTotales = computed(() => {
  if (!lastPeriodData.value) return { total: "$0", segments: [] };
  
  const rotCrudos = lastPeriodData.value.rotacion?.datos_crudos || {};
  const liqCrudos = lastPeriodData.value.liquidez?.datos_crudos || {};

  const activoTotal = rotCrudos.activo_total || 0;
  const activoCirculanteVal = liqCrudos.activo_circulante || 0;
  
  let activoNoCirculante = activoTotal - activoCirculanteVal;
  if (activoNoCirculante < 0) activoNoCirculante = 0;

  const items = [
    { label: "Activo Circulante", value: activoCirculanteVal, color: "#e11d48" },
    { label: "Activo No Circulante", value: activoNoCirculante, color: "#fb923c" }
  ].filter(i => i.value > 0);

  const totalCálculo = items.reduce((acc, curr) => acc + curr.value, 0) || 1;
  
  let currentOffset = 0;
  const segments = items.map(item => {
    const pct = (item.value / totalCálculo) * 100;
    const dasharray = `${pct} 100`;
    const dashoffset = -currentOffset;
    currentOffset += pct;
    return { ...item, pct: pct.toFixed(1), dasharray, dashoffset };
  });

  return {
    total: activoTotal >= 1000000 ? `$${(activoTotal/1000000).toFixed(1)}M` : currencyFmt.format(activoTotal),
    segments
  };
});

// --- IA LOCAL DE INTERPRETACIÓN ---
const analysisText = computed(() => {
  if (!selectedKpi.value) return "";
  const val = parseVal(selectedKpi.value.kpiValue);
  const deltaStr = selectedKpi.value.deltaValue;
  const isWorsening = deltaStr.includes("+") && selectedKpi.value.key === "recaudo" || deltaStr.includes("-") && selectedKpi.value.key !== "recaudo";

  if (selectedKpi.value.key === "cobrar") {
    return isWorsening 
        ? "La rotación de cuentas por cobrar muestra una desaceleración. La empresa está tardando más en convertir sus ventas a crédito en efectivo, tensionando el flujo operativo."
        : "La recuperación de cartera es eficiente. La empresa convierte rápidamente sus ventas a crédito en liquidez real.";
  }

  if (selectedKpi.value.key === "recaudo") {
    return val > 60 
        ? `Alerta: El periodo promedio de recaudo es de ${val} días. La empresa está tardando demasiado en recuperar su dinero, lo que afecta la liquidez inmediata.`
        : `Saludable: La empresa cobra en promedio cada ${val} días, lo cual es un periodo de recaudo eficiente.`;
  }

  if (selectedKpi.value.key === "inventarios") {
    return isWorsening
        ? "La rotación de inventarios ha disminuido. Riesgo de sobre stock, obsolescencia o ventas más lentas de lo proyectado."
        : "Buena gestión de inventarios. La mercancía entra y sale con rapidez, evitando capital estancado en el almacén.";
  }

  if (selectedKpi.value.key === "fijos") {
    return val < 1.0 
        ? "Baja eficiencia en activos fijos. La infraestructura actual (maquinaria, edificios) no está generando las ventas esperadas."
        : "Excelente aprovechamiento de la infraestructura productiva. Los activos a largo plazo están generando un alto volumen de ventas.";
  }

  return val >= 1.0 
    ? "Alta eficiencia operativa global. La empresa genera más en ventas de lo que tiene invertido en activos totales."
    : "Baja rotación de activos totales. Se requiere mayor volumen de ventas para justificar la inversión total en la empresa.";
});

const recommendationList = computed(() => {
  if (!selectedKpi.value) return [];
  const val = parseVal(selectedKpi.value.kpiValue);

  if (selectedKpi.value.key === "cobrar" || selectedKpi.value.key === "recaudo") {
    return val > 60 || selectedKpi.value.key === "cobrar" ? [
      "Revisar y endurecer las políticas de crédito otorgadas a clientes.",
      "Implementar recordatorios de pago automáticos antes del vencimiento.",
      "Ofrecer descuentos por pronto pago para acelerar la entrada de efectivo.",
    ] : [
      "Mantener las actuales políticas de crédito que están dando buenos resultados.",
      "Considerar ampliar líneas de crédito a clientes VIP para fomentar más ventas."
    ];
  }

  if (selectedKpi.value.key === "inventarios") {
    return [
      "Cruzar datos de inventario con ventas para identificar productos estrella y rezagados.",
      "Negociar entregas fraccionadas (Just-in-Time) con proveedores para no saturar almacenes.",
      "Liquidar stock obsoleto mediante promociones para liberar capital."
    ];
  }

  if (selectedKpi.value.key === "fijos") {
    return val < 1.0 ? [
      "Evaluar la venta de maquinaria o vehículos ociosos.",
      "Frenar la adquisición de nuevos activos fijos hasta aumentar las ventas.",
    ] : [
      "Planificar mantenimientos preventivos para no detener la alta producción.",
      "Evaluar si la alta rotación amerita expandir la capacidad instalada."
    ];
  }

  return [
    "Monitorear qué activos (circulantes o fijos) están frenando la rotación global.",
    "Enfocar los esfuerzos comerciales en desplazar inventario más rápido.",
  ];
});



onMounted(() => {
  fetchPeriods();
});
</script>

<template>
  <div class="wrap">
    <div class="title">
      <div class="title-row">
        <h1>Rotación de Activos</h1>
        <button class="btn-learn" type="button" @click="centroDeAprendizaje">
          <span class="material-symbols-outlined">info</span>
          <span>Ir a centro de aprendizaje</span>
        </button>
      </div>

      <div class="subtitle">
        <p>Análisis de eficiencia operativa y administración de activos</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">Indicadores calculados a partir del Balance General y del Estado de Resultados</p>
      </div>
    </div>

    <section class="kpis">
      <button
        v-for="k in metrics"
        :key="k.key"
        type="button"
        class="kpi"
        :class="{ selected: activeKpi === k.key }"
        @click="setActive(k.key)"
      >
        <div class="kpi-top">
          <p class="kpi-label" :class="{ 'kpi-label-selected': activeKpi === k.key }">
            {{ k.label }}
          </p>
          <span class="kpi-dot" :class="k.status" aria-hidden="true"></span>
        </div>

        <div class="kpi-value">{{ k.kpiValue }}</div>

        <div class="kpi-delta">
          <span
            class="delta-pill"
            :class="k.deltaStyle === 'positive' ? 'delta-up' : 'delta-down'"
          >
            <span class="material-symbols-outlined">{{ k.deltaIcon }}</span>
            {{ k.deltaValue }}
          </span>
          <span class="delta-note">{{ k.deltaNote }}</span>
        </div>
      </button>
    </section>

    <section class="panel" v-if="selectedKpi">
      <div class="panel-head">
        <div>
          <h3>{{ selectedKpi.chartTitle }}</h3>
          <p class="panel-sub">{{ selectedKpi.chartSubtitle }}</p>
        </div>

        <div class="legend">
          <div class="legend-item">
            <span class="legend-dot" aria-hidden="true"></span>
            <span>{{ selectedKpi.legendLabel }}</span>
          </div>
        </div>
      </div>

      <div class="chart">
        <svg class="chart-svg" fill="none" preserveAspectRatio="none" viewBox="0 0 800 300">
          <defs>
            <linearGradient id="gradient-ra" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#299de0" stop-opacity="0.15"></stop>
              <stop offset="100%" stop-color="#299de0" stop-opacity="0"></stop>
            </linearGradient>
          </defs>

          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

          <path :d="areaPath" fill="url(#gradient-ra)"></path>
          <path :d="linePath" fill="none" stroke="#299de0" stroke-linecap="round" stroke-width="3"></path>

          <circle
            v-for="(p, idx) in selectedKpi.points"
            :key="idx"
            :cx="p.x"
            :cy="p.y"
            fill="white"
            :r="hoveredPoint === p ? 6 : 5"
            stroke="#299de0"
            stroke-width="2.5"
            style="transition: r 0.2s ease;"
          ></circle>

          <circle
            v-for="(p, idx) in selectedKpi.points"
            :key="`hit-${idx}`"
            :cx="p.x"
            :cy="p.y"
            r="20"
            fill="transparent"
            style="cursor: pointer;"
            @mouseover="showTooltip(p)"
            @mouseleave="hideTooltip"
          ></circle>

          <g v-if="hoveredPoint" style="pointer-events: none;">
            <rect
              :x="hoveredPoint.x - 30"
              :y="hoveredPoint.y - 42"
              width="60"
              height="26"
              rx="6"
              fill="#0e161b"
              opacity="0.95"
            ></rect>
            <polygon
              :points="`${hoveredPoint.x - 6},${hoveredPoint.y - 16} ${hoveredPoint.x + 6},${hoveredPoint.y - 16} ${hoveredPoint.x},${hoveredPoint.y - 10}`"
              fill="#0e161b"
              opacity="0.95"
            ></polygon>
            <text
              :x="hoveredPoint.x"
              :y="hoveredPoint.y - 24"
              fill="#ffffff"
              font-size="12"
              font-weight="bold"
              font-family="Inter, sans-serif"
              text-anchor="middle"
            >
              {{
                hoveredPoint.type === "days"
                  ? `${Math.round(hoveredPoint.value)} días`
                  : `${hoveredPoint.value.toFixed(1)}x`
              }}
            </text>
          </g>

          <text
            v-for="(p, idx) in selectedKpi.points"
            :key="`t-${idx}`"
            :x="p.x"
            y="260"
            text-anchor="middle"
            font-family="Inter, sans-serif"
            font-size="12"
            :font-weight="p.bold ? 'bold' : 'normal'"
            :fill="p.bold ? '#0e161b' : '#507c95'"
          >
            {{ p.label }}
          </text>

          <g>
            <text
              v-for="(lab, i) in selectedKpi.yAxisLabels"
              :key="`yl-${i}`"
              x="45"
              :y="55 + i * 60"
              text-anchor="end"
              fill="#507c95"
              font-family="Inter"
              font-size="11"
              font-weight="600"
            >
              {{ lab }}
            </text>
          </g>
        </svg>
      </div>
    </section>

    <section class="grid-2">
      <article class="card">
        <h3>Composición de Activo Circulante</h3>
        <p class="card-sub">Desglose de activos de corto plazo ({{ lastPeriodData?.label }})</p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle
                v-for="(seg, idx) in activoCirculante.segments"
                :key="idx"
                cx="18"
                cy="18"
                fill="none"
                r="16"
                :stroke="seg.color"
                :stroke-dasharray="seg.dasharray"
                :stroke-dashoffset="seg.dashoffset"
                stroke-width="4"
              ></circle>
            </svg>
            <div class="donut-center">
              <span class="donut-kicker">Total C.</span>
              <span class="donut-total">{{ activoCirculante.total }}</span>
            </div>
          </div>
        </div>

        <div class="legend-grid two-cols">
          <div class="legend-row" v-for="(seg, idx) in activoCirculante.segments" :key="`leg-a-${idx}`">
            <span class="dot" :style="{ background: seg.color }" aria-hidden="true"></span>
            <span class="truncate">{{ seg.label }} ({{ seg.pct }}%)</span>
          </div>
        </div>
      </article>

      <article class="card">
        <h3>Distribución de Activos Totales</h3>
        <p class="card-sub">Relación entre Activos Circulantes y No Circulantes ({{ lastPeriodData?.label }})</p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle
                v-for="(seg, idx) in activosTotales.segments"
                :key="idx"
                cx="18"
                cy="18"
                fill="none"
                r="16"
                :stroke="seg.color"
                :stroke-dasharray="seg.dasharray"
                :stroke-dashoffset="seg.dashoffset"
                stroke-width="4"
              ></circle>
            </svg>
            <div class="donut-center">
              <span class="donut-kicker">Activo</span>
              <span class="donut-total">{{ activosTotales.total }}</span>
            </div>
          </div>
        </div>

        <div class="legend-grid">
          <div class="legend-row" v-for="(seg, idx) in activosTotales.segments" :key="`leg-t-${idx}`">
            <span class="dot" :style="{ background: seg.color }" aria-hidden="true"></span>
            <span class="truncate">{{ seg.label }} ({{ seg.pct }}%)</span>
          </div>
        </div>
      </article>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h3>Comparativa por periodo</h3>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Periodo</th>
              <th class="right">Ventas Netas</th>
              <th class="right">Activo Total</th>
              <th class="right">Rotación Activos</th>
              <th class="right">Rotación Inventarios</th>
              <th class="right">Periodo Cobro</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in tableRows" :key="r.period" :class="{ highlight: r.highlight }">
              <td class="strong" :class="{ primary: r.highlight }">{{ r.period }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.ventas }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.activo }}</td>
              <td class="right" :class="{ strong: r.highlight }">
                <span v-if="r.highlight" class="table-badge">{{ r.rotacionActivos }}</span>
                <span v-else>{{ r.rotacionActivos }}</span>
              </td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.rotacionInventarios }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.periodoCobro }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid-2">
      <article class="note note-warn">
        <div class="note-bg" aria-hidden="true">
          <span class="material-symbols-outlined">insights</span>
        </div>

        <div class="note-mini">
          <span class="material-symbols-outlined">info</span>
          <span>Interpretación Automática</span>
        </div>

        <h3>Análisis de tendencia</h3>
        <p>{{ analysisText }}</p>
      </article>

      <article class="note note-ok">
        <div class="note-head">
          <span class="tag-green">
            <span class="material-symbols-outlined">rocket_launch</span>
          </span>
          <h3>Recomendaciones</h3>
        </div>

        <ul class="list">
          <li v-for="(item, idx) in recommendationList" :key="idx">
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
.truncate {
  line-height: 1.3;
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
  width: 100%;
  text-align: left;
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.05s ease;
  cursor: pointer;
}

.kpi:hover {
  border-color: #b4d2e6;
  box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}

.kpi:active {
  transform: translateY(1px);
}

.kpi.selected {
  border: 2px solid #299de0;
  background: #f0f8fd;
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

.kpi-label-selected {
  color: #299de0;
  font-weight: 900;
}

.kpi-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-top: 4px;
  flex-shrink: 0;
}

.kpi-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34,197,94,0.4);
}

.kpi-dot.warn {
  background: #e11d48;
  box-shadow: 0 0 8px rgba(225,29,72,0.35);
}

.kpi-value {
  margin-top: 10px;
  font-size: 24px;
  font-weight: 900;
  color: #0e161b;
}

.kpi-delta {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.delta-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 8px;
  padding: 4px 8px;
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

.delta-down {
  background: #fee2e2;
  color: #e73508;
}

.delta-note {
  color: #507c95;
  font-size: 12px;
  font-weight: 700;
}

/* Panels */
.panel {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}

.panel-head {
  padding: 14px 18px;
  border-bottom: 1px solid #e8eff3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.panel-sub {
  margin: 4px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.legend {
  display: flex;
  align-items: center;
  gap: 14px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  color: #0e161b;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: #299de0;
}

.chart {
  padding: 16px 18px 18px;
  position: relative;
}

.chart-svg {
  width: 100%;
  height: 280px;
  display: block;
}

/* Donut cards */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.card-sub {
  margin: -6px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.donut-wrap {
  display: grid;
  place-items: center;
  padding: 10px 0;
}

.donut {
  position: relative;
  width: 160px;
  height: 160px;
}

.donut-svg {
  width: 100%;
  height: 100%;
}

.donut-center {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
}

.donut-kicker {
  font-size: 11px;
  font-weight: 900;
  color: #507c95;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.donut-total {
  font-size: 20px;
  font-weight: 900;
  color: #0e161b;
}

.legend-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px 12px;
  margin-top: 8px;
}

.legend-grid.two-cols {
  grid-template-columns: repeat(2, 1fr);
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  flex-shrink: 0;
}

/* Table */
.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 900px;
}

.table thead th {
  text-align: left;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #507c95;
  background: #f8fafb;
  border-bottom: 1px solid #e8eff3;
  padding: 12px 16px;
  font-weight: 900;
}

.table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid #e8eff3;
  font-size: 13px;
  color: #0e161b;
}

.table tbody tr:hover {
  background: #f9fafb;
}

.table .right {
  text-align: right;
}

.strong {
  font-weight: 900;
}

.primary {
  color: #299de0;
}

.highlight {
  background: rgba(41, 157, 224, 0.08);
}

.table-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 5px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 900;
}

/* Notes */
.note {
  position: relative;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  overflow: hidden;
}

.note-warn {
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 70%);
  border: 1px solid #dbeafe;
}

.note-ok {
  background: #ffffff;
  border: 1px solid #e8eff3;
}

.note-bg {
  position: absolute;
  right: 10px;
  top: 6px;
  opacity: 0.05;
}

.note-bg .material-symbols-outlined {
  font-size: 100px;
  color: #299de0;
}

.note-mini {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #299de0;
}

.note-mini .material-symbols-outlined {
  font-size: 18px;
}

.note h3 {
  margin: 10px 0 10px;
  font-size: 18px;
  font-weight: 900;
  color: #0e161b;
}

.note p {
  margin: 0;
  color: #0e161b;
  font-weight: 700;
  font-size: 14px;
  line-height: 1.55;
  position: relative;
  z-index: 1;
}

.note-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tag-green {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #dcfce7;
  color: #15803d;
  display: grid;
  place-items: center;
}

.tag-green .material-symbols-outlined {
  font-size: 20px;
}

.list {
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 12px;
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
  flex-shrink: 0;
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

@media (min-width: 900px) {
  .kpis {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1200px) {
  .kpis {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>