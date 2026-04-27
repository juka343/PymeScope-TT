<script setup>
import { computed, ref, onMounted } from "vue";
import { collection, getDocs } from "firebase/firestore";
import { db } from "@/firebase/config";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const projectId = route.params.id_proyecto;

const centroDeAprendizaje = () => {
  const routeData = router.resolve({ name: "teoriaLiquidez" });
  window.open(routeData.href, "_blank");
};

const loading = ref(true);
const rawPeriods = ref([]);
const metrics = ref([]);
const activeKpi = ref("razon");
const tableRows = ref([]);



// Formateadores
const currencyFmt = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Función para parsear valores que podrían venir como string o número desde el motor
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
      if (d.liquidez || d.analisis_liquidez) {
        loaded.push({
          id: docSnap.id,
          label: d.label || "Periodo",
          periodDate: d.periodDate || d.label,
          liquidez: d.liquidez || d.analisis_liquidez || { datos_crudos: {}, kpis: [], desglose_activos: [], desglose_pasivos: [] },
        });
      }
    });

    loaded.sort((a, b) => a.periodDate.localeCompare(b.periodDate));
    rawPeriods.value = loaded;
    
    if (loaded.length > 0) {
      generateDashboardData();
    }
  } catch (error) {
    console.error("Error cargando multiperiodo liquidez:", error);
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

  const getKpiStatus = (kpis, keyword) => {
    if (!kpis) return "warn";
    const item = kpis.find(k => k.label.toLowerCase().includes(keyword.toLowerCase()));
    return item ? item.status : "warn";
  };

  const dataRazon = periods.map(p => findKpi(p.liquidez.kpis, "liquidez")); 
  const dataAcida = periods.map(p => findKpi(p.liquidez.kpis, "ácido"));
  const dataCapital = periods.map(p => {
    const item = p.liquidez.kpis.find(k => k.label.toLowerCase().includes("capital"));
    return item ? parseVal(item.value) : 0;
  });

  const buildChart = (values, title, subtitle, legendLabel, isCurrency = false, backendStatus = "warn") => {
    const maxVal = Math.max(...values, isCurrency ? 1000 : 2); 
    let minVal = Math.min(...values, 0); 
    if (minVal > 0 && !isCurrency) minVal = 0; 

    const rawRange = maxVal - minVal;
    
    // Cálculo de pasos para el eje Y
    let step;
    if (isCurrency) {
        const magnitude = Math.pow(10, Math.floor(Math.log10(rawRange || 1)));
        step = Math.max(magnitude / 2, 1000);
    } else {
        step = 0.5;
        if (rawRange > 3) step = 1;
        if (rawRange > 10) step = 2;
    }

    const yMin = Math.floor(minVal / step) * step;
    const yMax = Math.ceil(maxVal / step) * step;
    const finalRange = Math.max(yMax - yMin, isCurrency ? 1000 : 0.1);

    const fmtLabel = (val) => {
      if (isCurrency) {
          if (val >= 1000000) return `$${(val/1000000).toFixed(1)}M`;
          if (val >= 1000) return `$${(val/1000).toFixed(0)}k`;
          return `$${val}`;
      }
      return val.toFixed(1);
    };

    const yAxisLabels = [
      fmtLabel(yMax),
      fmtLabel(yMax - (finalRange / 3)),
      fmtLabel(yMax - (finalRange / 3) * 2),
      fmtLabel(yMin)
    ];

    const xStep = periods.length > 1 ? 560 / (periods.length - 1) : 0;
    
    const points = values.map((val, i) => {
      const x = periods.length > 1 ? 120 + i * xStep : 400; 
      const y = 230 - ((val - yMin) / finalRange) * 180;
      return { x, y, label: labels[i], bold: i === values.length - 1, value: val, isCurrency };
    });

    const lastVal = values[values.length - 1];
    const prevVal = values.length > 1 ? values[values.length - 2] : lastVal;
    
    let delta = lastVal - prevVal;
    // === USAMOS EL STATUS QUE CALCULÓ PYTHON ===
    let status = backendStatus;

    return {
      kpiValue: isCurrency ? currencyFmt.format(lastVal) : lastVal.toFixed(2),
      status: status,
      deltaType: delta >= 0 ? "up" : "down",
      deltaValue: isCurrency ? currencyFmt.format(delta) : `${delta > 0 ? '+' : ''}${delta.toFixed(2)}`,
      deltaNote: periods.length > 1 ? `vs ${labels[labels.length - 2]}` : "Sin periodo previo",
      chartTitle: title,
      chartSubtitle: subtitle,
      legendLabel: legendLabel,
      yAxisLabels,
      points
    };
  };

  const lastP = periods[periods.length - 1];

  metrics.value = [
    { key: "razon", label: "Razón Circulante", ...buildChart(dataRazon, "Evolución Razón Circulante", "Capacidad para cubrir deudas a corto plazo", "Circulante", false, getKpiStatus(lastP.liquidez.kpis, "liquidez")) },
    { key: "acida", label: "Prueba Ácida", ...buildChart(dataAcida, "Evolución Prueba Ácida", "Liquidez inmediata sin depender de inventarios", "Ácida", false, getKpiStatus(lastP.liquidez.kpis, "ácido")) },
    { key: "capital", label: "Capital de Trabajo", ...buildChart(dataCapital, "Evolución Capital de Trabajo", "Recursos netos para la operación diaria", "Capital", true, getKpiStatus(lastP.liquidez.kpis, "capital")) }
  ];

  // Construir Tabla (Orden Ascendente)
  tableRows.value = periods.map((p, i) => {
    return {
      period: p.label,
      activo: currencyFmt.format(p.liquidez.datos_crudos?.activo_circulante || 0),
      pasivo: currencyFmt.format(p.liquidez.datos_crudos?.pasivo_circulante || 0),
      rc: dataRazon[i].toFixed(2),
      pa: dataAcida[i].toFixed(2),
      ct: currencyFmt.format(dataCapital[i]),
      highlight: i === periods.length - 1 // Resalta el más reciente
    };
  });
};

const selectedKpi = computed(() => {
  if (metrics.value.length === 0) return null;
  return metrics.value.find((m) => m.key === activeKpi.value) || metrics.value[0];
});

function setActive(k) {
  activeKpi.value = k;
}

// Tooltips para la gráfica
const hoveredPoint = ref(null);
function showTooltip(p) { hoveredPoint.value = p; }
function hideTooltip() { hoveredPoint.value = null; }

// Helpers SVG
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

// Composición (Donuts) - Tomamos el último periodo
const lastPeriodData = computed(() => {
  if (rawPeriods.value.length === 0) return null;
  return rawPeriods.value[rawPeriods.value.length - 1];
});

// Helper para calcular la suma de arreglos
const sumArray = (arr) => arr.reduce((acc, curr) => acc + parseVal(curr.value), 0);

// Helper para generar los stroke-dasharray de los donuts
const generateDonutSegments = (items, total) => {
    if(!items || items.length === 0 || total === 0) return [];
    let currentOffset = 0;
    const colors = ["#1e293b", "#299de0", "#507c95", "#d1dee6", "#94a3b8"];
    
    return items.map((item, index) => {
        const val = parseVal(item.value);
        const pct = (val / total) * 100;
        // La longitud de la circunferencia es 100 en nuestro SVG (r=16 -> 2*PI*16 aprox 100)
        const segment = {
            ...item,
            pct: pct.toFixed(1),
            color: colors[index % colors.length],
            dasharray: `${pct} 100`,
            dashoffset: -currentOffset
        };
        currentOffset += pct;
        return segment;
    });
};

const activosCirculantes = computed(() => {
    if(!lastPeriodData.value) return { total: 0, strTotal: "$0", segments: [] };
    
    // Intentamos buscar el desglose si en el futuro lo agregas a Python
    let items = lastPeriodData.value.liquidez.desglose_activos || [];
    
    // Si no existe, Vue lo "inventa" con los datos crudos disponibles
    if (items.length === 0) {
        const crudos = lastPeriodData.value.liquidez.datos_crudos;
        const inventario = crudos?.inventario || 0;
        const restoActivo = (crudos?.activo_circulante || 0) - inventario;
        
        items = [
            { label: "Inventarios", value: inventario },
            { label: "Resto del Activo Circulante", value: restoActivo > 0 ? restoActivo : 0 }
        ].filter(i => i.value > 0); // Filtramos los que estén en cero
    }

    const total = sumArray(items);
    return {
        total,
        strTotal: total >= 1000000 ? `$${(total/1000000).toFixed(1)}M` : currencyFmt.format(total),
        segments: generateDonutSegments(items, total)
    };
});

const pasivosCirculantes = computed(() => {
    if(!lastPeriodData.value) return { total: 0, strTotal: "$0", segments: [] };
    
    let items = lastPeriodData.value.liquidez.desglose_pasivos || [];
    
    if (items.length === 0) {
        const crudos = lastPeriodData.value.liquidez.datos_crudos;
        items = [
            { label: "Pasivo Circulante Total", value: crudos?.pasivo_circulante || 0 }
        ].filter(i => i.value > 0);
    }

    const total = sumArray(items);
    const colors = ["#e11d48", "#fb923c", "#fcd34d", "#fecdd3", "#fca5a5"];
    
    let currentOffset = 0;
    const segments = items.map((item, index) => {
        const val = parseVal(item.value);
        const pct = (val / total) * 100;
        const segment = {
            ...item,
            pct: pct.toFixed(1),
            color: colors[index % colors.length],
            dasharray: `${pct} 100`,
            dashoffset: -currentOffset
        };
        currentOffset += pct;
        return segment;
    });

    return {
        total,
        strTotal: total >= 1000000 ? `$${(total/1000000).toFixed(1)}M` : currencyFmt.format(total),
        segments
    };
});




onMounted(() => {
  fetchPeriods();
});
</script>

<template>
  <div class="wrap" v-if="!loading && metrics.length > 0">
    <div class="title">
      <div class="title-row">
        <h1>Liquidez</h1>
        <button class="btn-learn" type="button" @click="centroDeAprendizaje">
          <span class="material-symbols-outlined">info</span>
          <span>Ir a centro de aprendizaje</span>
        </button>
      </div>
      <div class="subtitle">
        <p>Capacidad de la empresa para cumplir con sus obligaciones a corto plazo</p>
        <span class="dot" aria-hidden="true">•</span>
        <p class="small">Indicadores calculados a partir del Balance General</p>
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
          <p class="kpi-label" :class="{ 'kpi-label-selected': activeKpi === k.key }">{{ k.label }}</p>
          <span class="kpi-dot" :class="k.status" aria-hidden="true"></span>
        </div>
        <div class="kpi-value">{{ k.kpiValue }}</div>
        <div class="kpi-delta">
          <span class="delta-pill" :class="k.deltaType === 'up' ? 'delta-up' : 'delta-down'">
            <span class="material-symbols-outlined">
              {{ k.deltaType === "up" ? "trending_up" : "trending_down" }}
            </span>
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
            <linearGradient id="gradient-rc" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#299de0" stop-opacity="0.15"></stop>
              <stop offset="100%" stop-color="#299de0" stop-opacity="0"></stop>
            </linearGradient>
          </defs>

          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170"></line>
          <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230"></line>

          <path :d="areaPath" fill="url(#gradient-rc)"></path>
          <path :d="linePath" fill="none" stroke="#299de0" stroke-linecap="round" stroke-width="3"></path>

          <circle
              v-for="(p, idx) in selectedKpi.points"
              :key="idx"
              :cx="p.x"
              :cy="p.y"
              fill="white"
              :r="hoveredPoint === p ? 6 : 4" 
              stroke="#299de0"
              stroke-width="2"
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
              :x="hoveredPoint.x - 40"
              :y="hoveredPoint.y - 42"
              width="80"
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
              {{ hoveredPoint.isCurrency ? currencyFmt.format(hoveredPoint.value) : hoveredPoint.value.toFixed(2) }}
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
            <text v-for="(lab, i) in selectedKpi.yAxisLabels" :key="`yl-${i}`" x="45" :y="55 + (i * 60)" text-anchor="end" fill="#507c95" font-family="Inter" font-size="11" font-weight="600">{{ lab }}</text>
          </g>
        </svg>
      </div>
    </section>

    <section class="grid-2">
      <article class="card">
        <h3>Composición Activo Circulante</h3>
        <p class="card-sub">Desglose del periodo base ({{ lastPeriodData?.label }})</p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle v-for="(seg, idx) in activosCirculantes.segments" :key="idx"
                cx="18" cy="18" fill="none" r="16" :stroke="seg.color" 
                :stroke-dasharray="seg.dasharray" :stroke-dashoffset="seg.dashoffset" stroke-width="4"
                style="transition: stroke-dasharray 1s ease-out, stroke-dashoffset 1s ease-out;">
                <title>{{ seg.label }}: {{ currencyFmt.format(parseVal(seg.value)) }}</title>
              </circle>
            </svg>
            <div class="donut-center">
              <span class="donut-kicker">Total</span>
              <span class="donut-total">{{ activosCirculantes.strTotal }}</span>
            </div>
          </div>
        </div>

        <div class="legend-grid">
          <div class="legend-row" v-for="(seg, idx) in activosCirculantes.segments" :key="`leg-a-${idx}`">
            <span class="dot" :style="{ background: seg.color }" aria-hidden="true"></span>
            <span class="truncate" :title="seg.label">{{ seg.label }} ({{ seg.pct }}%)</span>
          </div>
        </div>
      </article>

      <article class="card">
        <h3>Composición Pasivo Circulante</h3>
        <p class="card-sub">Desglose del periodo base ({{ lastPeriodData?.label }})</p>

        <div class="donut-wrap">
          <div class="donut">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle cx="18" cy="18" fill="none" r="16" stroke="#e8eff3" stroke-width="4"></circle>
              <circle v-for="(seg, idx) in pasivosCirculantes.segments" :key="idx"
                cx="18" cy="18" fill="none" r="16" :stroke="seg.color" 
                :stroke-dasharray="seg.dasharray" :stroke-dashoffset="seg.dashoffset" stroke-width="4"
                style="transition: stroke-dasharray 1s ease-out, stroke-dashoffset 1s ease-out;">
                <title>{{ seg.label }}: {{ currencyFmt.format(parseVal(seg.value)) }}</title>
              </circle>
            </svg>
            <div class="donut-center">
              <span class="donut-kicker">Total</span>
              <span class="donut-total">{{ pasivosCirculantes.strTotal }}</span>
            </div>
          </div>
        </div>

        <div class="legend-grid">
          <div class="legend-row" v-for="(seg, idx) in pasivosCirculantes.segments" :key="`leg-p-${idx}`">
            <span class="dot" :style="{ background: seg.color }" aria-hidden="true"></span>
            <span class="truncate" :title="seg.label">{{ seg.label }} ({{ seg.pct }}%)</span>
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
              <th class="right">Activo Circulante</th>
              <th class="right">Pasivo Circulante</th>
              <th class="center" style="text-align: center;">Razón Circulante</th>
              <th class="center" style="text-align: center;">Prueba Ácida</th>
              <th class="right">Capital de Trabajo</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in tableRows"
              :key="r.period"
              :class="{ highlight: r.highlight }"
            >
              <td class="strong" :class="{ primary: r.highlight }">{{ r.period }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.activo }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.pasivo }}</td>
              <td class="center" style="text-align: center;" :class="{ strong: r.highlight }">{{ r.rc }}</td>
              <td class="center" style="text-align: center;" :class="{ strong: r.highlight }">{{ r.pa }}</td>
              <td class="right" :class="{ strong: r.highlight }">{{ r.ct }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid-2">
      <article class="note note-warn">
        <div class="note-bg" aria-hidden="true">
          <span class="material-symbols-outlined">warning</span>
        </div>
        <div class="note-mini">
          <span class="material-symbols-outlined">info</span>
          <span>Interpretación Automática</span>
        </div>
        <h3>Análisis de tendencia</h3>
        <p v-if="metrics[0].status === 'warn'">
          El periodo más reciente indica que la Razón Circulante se encuentra por debajo de los niveles óptimos (menor a 1.5). Existe un riesgo operativo si las deudas a corto plazo vencen simultáneamente.
        </p>
        <p v-else>
          La empresa mantiene una liquidez sana en su último periodo. Su Capital de Trabajo de {{ metrics[2].kpiValue }} le permite operar sin contratiempos inmediatos.
        </p>
      </article>

      <article class="note note-ok">
        <div class="note-head">
          <span class="tag-green">
            <span class="material-symbols-outlined">rocket_launch</span>
          </span>
          <h3>Recomendaciones</h3>
        </div>
        <ul class="list">
          <li><span class="material-symbols-outlined">check_circle</span><span>Vigilar el periodo medio de cobro para acelerar el flujo de efectivo.</span></li>
          <li><span class="material-symbols-outlined">check_circle</span><span>Renegociar pagos con proveedores si la Prueba Ácida es menor a 1.</span></li>
          <li><span class="material-symbols-outlined">check_circle</span><span>Evitar el exceso de inventarios estancados.</span></li>
        </ul>
      </article>
    </section>

    <footer class="foot">
      <p>Todos los datos son confidenciales.<br />Este reporte es para fines informativos.</p>
    </footer>
  </div>
  <div v-else-if="loading" style="padding: 40px; text-align: center; color: var(--muted);">
      Cargando análisis multiperiodo de liquidez...
  </div>
</template>

<style scoped>
/* Pega aquí todo tu CSS intacto original, con esta pequeña adición para que las leyendas de los donuts no rompan el diseño si son muy largas */
.truncate {
  line-height: 1.3;
  /* Eliminamos el white-space: nowrap y el max-width para que el texto fluya libremente */
}

/* --- TU CSS ORIGINAL ABAJO --- */
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
}

.kpi-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34,197,94,0.4);
}

.kpi-dot.warn {
  background: #facc15;
  box-shadow: 0 0 8px rgba(250,204,21,0.4);
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
  /* Cambiamos de 1fr 1fr a 1fr para que ocupe todo el ancho de la tarjeta */
  grid-template-columns: 1fr; 
  gap: 10px 12px;
  margin-top: 8px;
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
  opacity: 0.06;
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

@media (min-width: 1024px) {
  .grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>