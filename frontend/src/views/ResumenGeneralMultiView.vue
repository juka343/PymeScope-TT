<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { collection, getDocs } from "firebase/firestore";
import { db } from "@/firebase/config";

const router = useRouter();
const route = useRoute();
const projectId = computed(() => route.params.id_proyecto || null);

const loading = ref(true);
const rawPeriods = ref([]);

// Textos estáticos (por ahora)
const recommendations = ref([
  "Control de costos operativos.",
  "Revisión de estrategia de precios.",
  "Optimización de procesos internos.",
]);
const interpretation = ref(
  "La empresa mantiene una tendencia en ingresos y utilidad neta durante los periodos analizados. Conviene monitorear capital de trabajo y compromisos de corto plazo."
);

// Formateadores
const currencyFmt = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", minimumFractionDigits: 0, maximumFractionDigits: 0 });
const percentFmt = new Intl.NumberFormat("es-MX", { style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 2 });

const parseVal = (val) => {
  if (!val) return 0;
  if (typeof val === "number") return val;
  return parseFloat(val.toString().replace(/[^0-9.-]/g, ""));
};

// =====================
// ESTADOS REACTIVOS
// =====================
const kpis = ref([]);
const cards = ref([]);
const chartLabels = ref([]);
const ingresosValues = ref([]);
const utilidadValues = ref([]);
const estructuraResultadoOptions = ref([]);
const selectedResultPeriod = ref("");

// Interacción de gráficas
const hoveredIngresosPoint = ref(null);
const hoveredUtilidadPoint = ref(null);

// =====================
// CARGA DE DATOS
// =====================
const fetchDashboardData = async () => {
  try {
    if (!projectId.value) return;

    const periodosRef = collection(db, "proyectos", projectId.value, "periodos");
    const snapshot = await getDocs(periodosRef);

    let loaded = [];
    snapshot.forEach((docSnap) => {
      const d = docSnap.data();
      if (d.analisis_rentabilidad || d.rentabilidad) {
        loaded.push({
          id: docSnap.id,
          label: d.label || "Periodo",
          periodDate: d.periodDate || d.label,
          resultados_url: d.resultsFile?.url || null, // Guardamos la URL del PDF
          rentabilidad: d.analisis_rentabilidad || d.rentabilidad || { datos_crudos: {}, kpis: [] },
          liquidez: d.analisis_liquidez || d.liquidez || { datos_crudos: {}, kpis: [] },
          endeudamiento: d.analisis_endeudamiento || d.endeudamiento || { datos_crudos: {}, kpis: [] },
          rotacion: d.analisis_rotacion || d.rotacion || { datos_crudos: {}, kpis: [] },
          estructura: d.analisis_estructura || d.estructura || { datos_crudos: {}, kpis: [] },
        });
      }
    });

    loaded.sort((a, b) => a.periodDate.localeCompare(b.periodDate));
    rawPeriods.value = loaded;

    if (loaded.length > 0) {
      generateDashboardData();
    }
  } catch (error) {
    console.error("Error cargando resumen multiperiodo:", error);
  } finally {
    loading.value = false;
  }
};

const generateDashboardData = () => {
  const periods = rawPeriods.value;
  chartLabels.value = periods.map(p => p.label);

  const lastP = periods[periods.length - 1];
  const prevP = periods.length > 1 ? periods[periods.length - 2] : lastP;

  const getKpiValue = (kpis, keyword) => {
    if (!kpis) return 0;
    const item = kpis.find((k) => k.label.toLowerCase().includes(keyword.toLowerCase()));
    const val = item ? parseVal(item.value) : 0;
    return isNaN(val) ? 0 : val;
  };

  const getKpiStatus = (kpis, keyword) => {
    if (!kpis) return "gray";
    const item = kpis.find((k) => k.label.toLowerCase().includes(keyword.toLowerCase()));
    return item?.status === "ok" ? "ok" : "warn";
  };

  // 1. Extraer datos para gráficas y Top KPIs
  ingresosValues.value = periods.map(p => p.rentabilidad.datos_crudos?.ventas_netas || 0);
  utilidadValues.value = periods.map(p => p.rentabilidad.datos_crudos?.utilidad_neta || 0);
  
  const lastIngresos = ingresosValues.value[ingresosValues.value.length - 1];
  const prevIngresos = ingresosValues.value.length > 1 ? ingresosValues.value[ingresosValues.value.length - 2] : lastIngresos;
  const deltaIngresos = prevIngresos ? ((lastIngresos - prevIngresos) / prevIngresos) : 0;

  const lastUtilidad = utilidadValues.value[utilidadValues.value.length - 1];
  const prevUtilidad = utilidadValues.value.length > 1 ? utilidadValues.value[utilidadValues.value.length - 2] : lastUtilidad;
  const deltaUtilidad = prevUtilidad ? ((lastUtilidad - prevUtilidad) / prevUtilidad) : 0;

  const lastMargen = lastIngresos ? lastUtilidad / lastIngresos : 0;
  const prevMargen = prevIngresos ? prevUtilidad / prevIngresos : 0;
  const deltaMargen = lastMargen - prevMargen;

  const lastLiq = getKpiValue(lastP.liquidez.kpis, "Razón de Liquidez");
  const prevLiq = getKpiValue(prevP.liquidez.kpis, "Razón de Liquidez");
  const deltaLiq = lastLiq - prevLiq;

  // 2. Construir TOP KPIs
  kpis.value = [
    {
      label: "Ingresos Totales",
      value: currencyFmt.format(lastIngresos),
      status: lastIngresos > 0 ? "ok" : "warn",
      deltaType: deltaIngresos >= 0 ? "up" : "down",
      deltaValue: `${deltaIngresos > 0 ? "+" : ""}${(deltaIngresos * 100).toFixed(1)}%`,
      deltaNote: periods.length > 1 ? `vs ${prevP.label}` : "Sin periodo previo",
    },
    {
      label: "Utilidad Neta",
      value: currencyFmt.format(lastUtilidad),
      status: lastUtilidad > 0 ? "ok" : "warn",
      deltaType: deltaUtilidad >= 0 ? "up" : "down",
      deltaValue: `${deltaUtilidad > 0 ? "+" : ""}${(deltaUtilidad * 100).toFixed(1)}%`,
      deltaNote: periods.length > 1 ? `vs ${prevP.label}` : "Sin periodo previo",
    },
    {
      label: "Margen Neto",
      value: percentFmt.format(lastMargen),
      status: lastMargen > 0.1 ? "ok" : "warn",
      deltaType: deltaMargen >= 0 ? "up" : "down",
      deltaValue: `${deltaMargen > 0 ? "+" : ""}${(deltaMargen * 100).toFixed(1)} pp`,
      deltaNote: periods.length > 1 ? `vs ${prevP.label}` : "Sin periodo previo",
    },
    {
      label: "Liquidez General",
      value: lastLiq.toFixed(2),
      status: lastLiq >= 1.0 ? "ok" : "warn",
      deltaType: deltaLiq >= 0 ? "up" : "down",
      deltaValue: `${deltaLiq > 0 ? "+" : ""}${deltaLiq.toFixed(2)}`,
      deltaNote: periods.length > 1 ? `vs ${prevP.label}` : "Sin periodo previo",
    },
  ];

  // 3. Construir CARDS
  cards.value = [
    {
      title: "Rentabilidad", icon: "trending_up", detailRoute: "rentabilidadMulti",
      items: [
        { label: "ROE", target: ">10%", value: `${getKpiValue(lastP.rentabilidad.kpis, "Patrimonio").toFixed(1)}%`, dot: getKpiStatus(lastP.rentabilidad.kpis, "Patrimonio") },
        { label: "Margen Neto", target: ">10%", value: `${getKpiValue(lastP.rentabilidad.kpis, "Margen de Rentabilidad").toFixed(1)}%`, dot: getKpiStatus(lastP.rentabilidad.kpis, "Margen de Rentabilidad") },
      ],
    },
    {
      title: "Liquidez", icon: "attach_money", detailRoute: "liquidezMulti",
      items: [
        { label: "Prueba Ácida", target: ">0.8", value: getKpiValue(lastP.liquidez.kpis, "Prueba del Ácido").toFixed(2), dot: getKpiStatus(lastP.liquidez.kpis, "Prueba del Ácido") },
        { label: "Cap. Trabajo", target: "> $0", value: currencyFmt.format(getKpiValue(lastP.liquidez.kpis, "Capital de Trabajo")), dot: getKpiStatus(lastP.liquidez.kpis, "Capital de Trabajo") },
      ],
    },
    {
      title: "Endeudamiento", icon: "account_balance_wallet", detailRoute: "endeudamientoMulti",
      items: [
        { label: "Nivel Deuda", target: "<0.5", value: getKpiValue(lastP.endeudamiento.kpis, "Apalancamiento").toFixed(2), dot: getKpiStatus(lastP.endeudamiento.kpis, "Apalancamiento") },
        { label: "Cobertura Int.", target: ">1.5x", value: `${getKpiValue(lastP.endeudamiento.kpis, "Cobertura de Intereses").toFixed(1)}x`, dot: getKpiStatus(lastP.endeudamiento.kpis, "Cobertura de Intereses") },
      ],
    },
    {
      title: "Rotación de Activos", icon: "sync_alt", detailRoute: "rotacionMulti",
      items: [
        { 
          label: "Rot. Inventario", 
          target: ">4.0x", 
          // Si Python manda "N/A" (empresa de servicios sin inventario), mostramos N/A
          value: (() => {
            const raw = lastP.rotacion.kpis?.find(k => k.label.toLowerCase().includes("inventarios"));
            if (!raw || raw.value === "N/A") return "N/A";
            const num = parseVal(raw.value);
            return isNaN(num) ? "N/A" : `${num.toFixed(1)}x`;
          })(),
          dot: getKpiStatus(lastP.rotacion.kpis, "Inventarios") 
        },
        { label: "Periodo Cobro", target: "<60 días", value: `${getKpiValue(lastP.rotacion.kpis, "Recaudo").toFixed(0)} días`, dot: getKpiStatus(lastP.rotacion.kpis, "Recaudo") },
      ],
    },
    {
      title: "Estructura Financiera", icon: "layers", detailRoute: "estructuraMulti",
      items: [
        { label: "Solvencia", target: ">1.0", value: getKpiValue(lastP.estructura.kpis, "Solvencia General").toFixed(2), dot: getKpiStatus(lastP.estructura.kpis, "Solvencia General") },
        { 
          label: "Seguridad LP", 
          target: ">=1.0", 
          value: isNaN(getKpiValue(lastP.estructura.kpis, "Seguridad a largo plazo")) 
                ? "N/A" 
                : getKpiValue(lastP.estructura.kpis, "Seguridad a largo plazo").toFixed(2), 
          dot: getKpiStatus(lastP.estructura.kpis, "Seguridad a largo plazo") 
        },
      ],
    },
  ];

  // 4. Construir Tabla de Resumen por Periodo (Orden Inverso)
  const calcPct = (val, total) => total ? `${((val / total) * 100).toFixed(1)}%` : "0%";
  
  const reversedPeriods = [...periods].reverse();
  estructuraResultadoOptions.value = reversedPeriods.map((p) => {
    const rentCrudos = p.rentabilidad.datos_crudos || {};
    const rotCrudos = p.rotacion.datos_crudos || {};
    const endCrudos = p.endeudamiento.datos_crudos || {};

    const v = rentCrudos.ventas_netas || 0;
    const ut_neta = rentCrudos.utilidad_neta || 0;
    const costo = rotCrudos.costo_ventas || 0;
    const ut_op = endCrudos.utilidad_operacion || 0;
    
    const gastos = v - costo - ut_op;
    const impuestos = ut_op - ut_neta;

    return {
      period: p.label,
      pdfUrl: p.resultados_url,
      rows: [
        { concept: "Ingresos", value: currencyFmt.format(v), pct: "100%", tone: "income" },
        { concept: "Costos", value: `(${currencyFmt.format(costo)})`, pct: calcPct(costo, v), tone: "negative" },
        { concept: "Gastos", value: `(${currencyFmt.format(gastos > 0 ? gastos : 0)})`, pct: calcPct(gastos > 0 ? gastos : 0, v), tone: "negative" },
        { concept: "Impuestos y Otros", value: `(${currencyFmt.format(impuestos > 0 ? impuestos : 0)})`, pct: calcPct(impuestos > 0 ? impuestos : 0, v), tone: "negative" },
        { concept: "Total (Utilidad Neta)", value: currencyFmt.format(ut_neta), pct: calcPct(ut_neta, v), tone: "total" },
      ],
    };
  });

  // Seleccionar por defecto el periodo más reciente
  if (estructuraResultadoOptions.value.length > 0) {
    selectedResultPeriod.value = estructuraResultadoOptions.value[0].period;
  }
};

// Computada para la tabla de resultados activa
const estructuraResultado = computed(() => {
  return (
    estructuraResultadoOptions.value.find(
      (item) => item.period === selectedResultPeriod.value
    ) || { rows: [], pdfUrl: null }
  );
});

// Lógica de Gráficas
const buildChartModel = (values, labels, isCurrency = false) => {
  if (values.length === 0) return { yAxisLabels: [], points: [] };
  
  const maxVal = Math.max(...values, isCurrency ? 1000 : 10);
  let minVal = Math.min(...values, 0);
  if (minVal > 0) minVal = 0;

  const rawRange = maxVal - minVal;
  let step;
  if (isCurrency) {
    const magnitude = Math.pow(10, Math.floor(Math.log10(rawRange || 1)));
    step = Math.max(magnitude / 2, 10000);
  } else {
    step = 5;
  }

  const yMin = Math.floor(minVal / step) * step;
  const yMax = Math.ceil(maxVal / step) * step;
  const finalRange = Math.max(yMax - yMin, isCurrency ? 10000 : 1);

  const fmtLabel = (val) => {
    if (!isCurrency) return `${val.toFixed(0)}`;
    if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
    return `$${val}`;
  };

  const yAxisLabels = [fmtLabel(yMax), fmtLabel(yMax - finalRange / 3), fmtLabel(yMax - (finalRange / 3) * 2), fmtLabel(yMin)];
  const xStep = labels.length > 1 ? 600 / (labels.length - 1) : 0;

  const points = values.map((val, i) => {
    const x = labels.length > 1 ? 100 + i * xStep : 400;
    const y = 230 - ((val - yMin) / finalRange) * 180;
    return { x, y, label: labels[i], bold: i === values.length - 1, value: val, isCurrency };
  });

  return { yAxisLabels, points };
};

const ingresosChart = computed(() => buildChartModel(ingresosValues.value, chartLabels.value, true));
const utilidadChart = computed(() => buildChartModel(utilidadValues.value, chartLabels.value, true));

const baselineY = 230;
const linePathFor = (chart) => chart?.points?.length ? chart.points.map((p, i) => (i === 0 ? `M${p.x} ${p.y}` : `L${p.x} ${p.y}`)).join(" ") : "";
const areaPathFor = (chart) => {
  const pts = chart?.points || [];
  if (!pts.length) return "";
  const first = pts[0], last = pts[pts.length - 1];
  const mid = pts.map((p) => `L${p.x} ${p.y}`).join(" ");
  return `M${first.x} ${baselineY} L${first.x} ${first.y} ${mid} L${last.x} ${baselineY} Z`;
};

// =====================
// NAVEGACIÓN Y ACCIONES
// =====================
function pushWithProject(name) {
  if (projectId.value) router.push({ name, params: { id_proyecto: projectId.value } });
}
function goDetail(routeName) { pushWithProject(routeName); }

function openPDF() {
  const url = estructuraResultado.value?.pdfUrl;
  if (url) {
    window.open(url, "_blank"); // Abre el PDF en una pestaña nueva
  } else {
    alert("No se encontró el documento PDF para este periodo.");
  }
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

        <div class="kpi-delta">
          <span class="delta-pill" :class="k.deltaType === 'up' ? 'delta-up' : 'delta-down'">
            <span class="material-symbols-outlined">
              {{ k.deltaType === "up" ? "trending_up" : "trending_down" }}
            </span>
            {{ k.deltaValue }}
          </span>
          <span class="delta-note">{{ k.deltaNote }}</span>
        </div>
      </article>
    </section>

    <!-- GRÁFICAS -->
    <section class="chart-grid">
      <article class="panel">
        <div class="panel-head">
          <div>
            <h3>Evolución de ingresos </h3>
            <p class="panel-sub">Comparativa por periodo</p>
          </div>

          <div class="legend">
            <div class="legend-item">
              <span class="legend-dot" aria-hidden="true"></span>
              <span>Ingresos</span>
            </div>
          </div>
        </div>

        <div class="chart">
          <svg class="chart-svg" fill="none" preserveAspectRatio="none" viewBox="0 0 800 300">
            <defs>
              <linearGradient id="gradient-ingresos" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#299de0" stop-opacity="0.15"></stop>
                <stop offset="100%" stop-color="#299de0" stop-opacity="0"></stop>
              </linearGradient>
            </defs>

            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

            <path :d="areaPathFor(ingresosChart)" fill="url(#gradient-ingresos)"></path>
            <path :d="linePathFor(ingresosChart)" fill="none" stroke="#299de0" stroke-linecap="round" stroke-width="3"></path>

            <circle
              v-for="(p, idx) in ingresosChart.points"
              :key="`ing-${idx}`"
              :cx="p.x"
              :cy="p.y"
              fill="white"
              :r="hoveredIngresosPoint === p ? 6 : 4"
              stroke="#299de0"
              stroke-width="2"
              style="transition: r 0.2s ease;"
            ></circle>

            <circle
              v-for="(p, idx) in ingresosChart.points"
              :key="`ing-hit-${idx}`"
              :cx="p.x"
              :cy="p.y"
              r="20"
              fill="transparent"
              style="cursor: pointer;"
              @mouseover="hoveredIngresosPoint = p"
              @mouseleave="hoveredIngresosPoint = null"
            ></circle>

            <g v-if="hoveredIngresosPoint" style="pointer-events: none;">
              <rect
                :x="hoveredIngresosPoint.x - 45"
                :y="hoveredIngresosPoint.y - 42"
                width="90"
                height="26"
                rx="6"
                fill="#0e161b"
                opacity="0.95"
              ></rect>
              <polygon
                :points="`${hoveredIngresosPoint.x - 6},${hoveredIngresosPoint.y - 16} ${hoveredIngresosPoint.x + 6},${hoveredIngresosPoint.y - 16} ${hoveredIngresosPoint.x},${hoveredIngresosPoint.y - 10}`"
                fill="#0e161b"
                opacity="0.95"
              ></polygon>
              <text
                :x="hoveredIngresosPoint.x"
                :y="hoveredIngresosPoint.y - 24"
                fill="#ffffff"
                font-size="12"
                font-weight="bold"
                font-family="Inter, sans-serif"
                text-anchor="middle"
              >
                {{ currencyFmt.format(hoveredIngresosPoint.value) }}
              </text>
            </g>

            <text
              v-for="(p, idx) in ingresosChart.points"
              :key="`ing-t-${idx}`"
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
                v-for="(lab, i) in ingresosChart.yAxisLabels"
                :key="`ing-y-${i}`"
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
      </article>

      <article class="panel">
        <div class="panel-head">
          <div>
            <h3>Utilidad neta</h3>
            <p class="panel-sub">Tendencia por periodo</p>
          </div>

          <div class="legend">
            <div class="legend-item">
              <span class="legend-dot" aria-hidden="true"></span>
              <span>Utilidad Neta</span>
            </div>
          </div>
        </div>

        <div class="chart">
          <svg class="chart-svg" fill="none" preserveAspectRatio="none" viewBox="0 0 800 300">
            <defs>
              <linearGradient id="gradient-utilidad" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#299de0" stop-opacity="0.15"></stop>
                <stop offset="100%" stop-color="#299de0" stop-opacity="0"></stop>
              </linearGradient>
            </defs>

            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

            <path :d="areaPathFor(utilidadChart)" fill="url(#gradient-utilidad)"></path>
            <path :d="linePathFor(utilidadChart)" fill="none" stroke="#299de0" stroke-linecap="round" stroke-width="3"></path>

            <circle
              v-for="(p, idx) in utilidadChart.points"
              :key="`util-${idx}`"
              :cx="p.x"
              :cy="p.y"
              fill="white"
              :r="hoveredUtilidadPoint === p ? 6 : 4"
              stroke="#299de0"
              stroke-width="2"
              style="transition: r 0.2s ease;"
            ></circle>

            <circle
              v-for="(p, idx) in utilidadChart.points"
              :key="`util-hit-${idx}`"
              :cx="p.x"
              :cy="p.y"
              r="20"
              fill="transparent"
              style="cursor: pointer;"
              @mouseover="hoveredUtilidadPoint = p"
              @mouseleave="hoveredUtilidadPoint = null"
            ></circle>

            <g v-if="hoveredUtilidadPoint" style="pointer-events: none;">
              <rect
                :x="hoveredUtilidadPoint.x - 45"
                :y="hoveredUtilidadPoint.y - 42"
                width="90"
                height="26"
                rx="6"
                fill="#0e161b"
                opacity="0.95"
              ></rect>
              <polygon
                :points="`${hoveredUtilidadPoint.x - 6},${hoveredUtilidadPoint.y - 16} ${hoveredUtilidadPoint.x + 6},${hoveredUtilidadPoint.y - 16} ${hoveredUtilidadPoint.x},${hoveredUtilidadPoint.y - 10}`"
                fill="#0e161b"
                opacity="0.95"
              ></polygon>
              <text
                :x="hoveredUtilidadPoint.x"
                :y="hoveredUtilidadPoint.y - 24"
                fill="#ffffff"
                font-size="12"
                font-weight="bold"
                font-family="Inter, sans-serif"
                text-anchor="middle"
              >
                {{ currencyFmt.format(hoveredUtilidadPoint.value) }}
              </text>
            </g>

            <text
              v-for="(p, idx) in utilidadChart.points"
              :key="`util-t-${idx}`"
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
                v-for="(lab, i) in utilidadChart.yAxisLabels"
                :key="`util-y-${i}`"
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
      </article>
    </section>

    <!-- Cards -->
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

    <!-- Resumen del resultado -->
    <section class="result-card">
      <div class="result-head">
        <div class="result-title">
          <span class="material-symbols-outlined" aria-hidden="true">receipt_long</span>
          <h4>Resumen del Resultado</h4>
        </div>

        <select v-model="selectedResultPeriod" class="result-select">
          <option
            v-for="option in estructuraResultadoOptions"
            :key="option.period"
            :value="option.period"
          >
            {{ option.period }}
          </option>
        </select>
      </div>

      <div class="result-wrap">
        <div class="result-header-row result-grid">
          <div>Concepto</div>
          <div class="center">Valor</div>
          <div class="right">% Ventas</div>
        </div>

        <div
          v-for="row in estructuraResultado.rows"
          :key="`${estructuraResultado.period}-${row.concept}`"
          class="result-row result-grid"
          :class="[
            row.tone === 'negative' ? 'result-negative' : '',
            row.tone === 'total' ? 'result-total' : ''
          ]"
        >
          <div class="result-concept">{{ row.concept }}</div>
          <div class="result-value center">{{ row.value }}</div>
          <div class="result-pct right">{{ row.pct }}</div>
        </div>
      </div>

      <div class="result-foot">
        <button 
          class="result-link" 
          type="button" 
          @click="openPDF"
          :disabled="!estructuraResultado?.pdfUrl"
        >
          <span class="material-symbols-outlined" style="vertical-align: middle; font-size: 16px; margin-right: 4px;">open_in_new</span>
          Ver estado de resultados completo
        </button>
      </div>
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
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.kpi-card:hover {
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.08);
  border-color: #b4d2e6;
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

.kpi-dot.alert {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

.kpi-dot.gray {
  background: #9ca3af;
}

.kpi-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 900;
  color: #0e161b;
}

.kpi-delta {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
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

/* ===== CHART PANELS ===== */
.chart-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

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

/* ===== Cards grid ===== */
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
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
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

.mini-dot.ok {
  background: #22c55e;
}

.mini-dot.warn {
  background: #facc15;
}

.mini-dot.alert {
  background: #ef4444;
}

.mini-dot.gray {
  background: #9ca3af;
}

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

/* ===== Resumen del resultado ===== */
.result-card {
  background: #fff;
  border: 1px solid #e8eff3;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.result-head {
  padding: 14px 16px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.result-title .material-symbols-outlined {
  color: #299de0;
  font-size: 22px;
}

.result-title h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 900;
}

.result-select {
  min-width: 140px;
  border: 1px solid #d1dee6;
  background: #f3f4f6;
  color: #507c95;
  border-radius: 10px;
  padding: 8px 36px 8px 14px;
  font-size: 12px;
  font-weight: 900;
  outline: none;
  cursor: pointer;
}

.result-select:focus {
  border-color: #299de0;
  box-shadow: 0 0 0 3px rgba(41, 157, 224, 0.12);
}

.result-wrap {
  overflow-x: auto;
}

.result-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.3fr) minmax(180px, 1fr) minmax(140px, 0.7fr);
  min-width: 640px;
}

.result-header-row {
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
  color: #507c95;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 900;
}

.result-header-row > div,
.result-row > div {
  padding: 16px;
}

.result-row {
  border-bottom: 1px solid #f1f5f9;
  background: #fff;
}

.result-row:hover {
  background: rgba(248, 250, 252, 0.6);
}

.result-concept {
  font-size: 13px;
  font-weight: 800;
  color: #0e161b;
}

.result-value,
.result-pct {
  font-size: 13px;
  font-weight: 800;
  color: #507c95;
}

.result-row.result-negative .result-value {
  color: #ef4444;
  font-weight: 900;
}

.result-row.result-negative .result-pct {
  color: #507c95;
}

.result-row.result-total .result-concept,
.result-row.result-total .result-value,
.result-row.result-total .result-pct {
  color: #0e161b;
  font-weight: 900;
  font-size: 14px;
}

.result-foot {
  padding: 14px 16px 18px;
  text-align: center;
  background: #fff;
}

.result-link {
  background: transparent;
  border: none;
  color: #299de0;
  font-weight: 900;
  font-size: 13px;
  cursor: pointer;
}

.result-link:hover {
  text-decoration: underline;
}

.center {
  text-align: center;
}

.right {
  text-align: right;
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
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.note-white {
  border-color: #e8eff3;
  background: #fff;
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

.tag-blue {
  background: #dbeafe;
  color: #299de0;
}

.tag-green {
  background: #dcfce7;
  color: #15803d;
}

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

/* ===== Botones ===== */
.link-btn {
  color: #299de0;
  font-weight: 900;
  font-size: 12px;
  background: transparent;
  border: none;
  cursor: pointer;
}

.link-btn:hover {
  text-decoration: underline;
}

/* ===== Footer ===== */
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

/* ===== Responsive ===== */
@media (min-width: 640px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 768px) {
  .cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .notes-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .kpi-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .chart-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .cards-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>