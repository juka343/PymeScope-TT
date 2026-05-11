<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  collection,
  getDocs,
  doc,
  getDoc,
  setDoc,
  serverTimestamp,
} from "firebase/firestore";
import { db } from "@/firebase/config";
import { useToast } from "@/composables/useToast";

const router = useRouter();
const route = useRoute();
const projectId = computed(() => route.params.id_proyecto || null);
const { toast } = useToast();

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api";

const AI_ANALYSIS_COLLECTION = "ai_analysis";
const AI_LATEST_DOC_ID = "resumen_multiperiodo_latest";

const getAiPeriodDocId = (basePeriodDate) => {
  return `resumen_multiperiodo_${basePeriodDate || "actual"}`;
};

const loading = ref(true);
const rawPeriods = ref([]);

const aiLoading = ref(false);
const aiError = ref(null);
const aiResult = ref(null);

// =====================
// FALLBACKS
// =====================
const fallbackInterpretation =
  "La empresa mantiene una tendencia en ingresos y utilidad neta durante los periodos analizados. Conviene monitorear capital de trabajo y compromisos de corto plazo.";

const interpretation = ref(fallbackInterpretation);

const executiveSummary = ref({
  title: "Interpretación general",
  paragraphs: [fallbackInterpretation],
});

const keyImplications = ref([]);
const aiAlerts = ref([]);

const recommendations = ref([
  {
    title: "Control de costos operativos",
    description:
      "Revisar gastos recurrentes para proteger el margen de utilidad.",
    reason:
      "En empresas de servicios, una estructura de gastos pesada puede reducir rápidamente la rentabilidad aunque las ventas se mantengan.",
    priority: "media",
  },
  {
    title: "Revisión de estrategia de precios",
    description:
      "Evaluar si los precios actuales cubren costos, gastos y margen esperado.",
    reason:
      "Un precio mal calculado puede sostener ventas, pero deteriorar la utilidad neta.",
    priority: "media",
  },
  {
    title: "Optimización de procesos internos",
    description:
      "Identificar actividades que consumen tiempo o recursos sin generar valor directo.",
    reason:
      "La eficiencia operativa es clave en servicios porque el costo principal suele estar ligado a personal, tiempo y capacidad instalada.",
    priority: "media",
  },
]);

// =====================
// FORMATEADORES
// =====================
const currencyFmt = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const percentFmt = new Intl.NumberFormat("es-MX", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 2,
});

const parseVal = (val) => {
  if (!val) return 0;
  if (typeof val === "number") return val;
  return parseFloat(val.toString().replace(/[^0-9.-]/g, ""));
};

// =====================
// HELPERS IA FRONTEND
// =====================
const cleanAiText = (text) => {
  if (text === null || text === undefined) return "";

  return String(text)
    .replace(/\bok\b/gi, "nivel saludable")
    .replace(/\bwarn\b/gi, "nivel de atención")
    .replace(/\bdanger\b/gi, "riesgo elevado")
    .replace(/\bstatus\b/gi, "estado");
};

const cleanAiArray = (items) => {
  if (!Array.isArray(items)) return [];
  return items.map((item) => cleanAiText(item)).filter(Boolean);
};

const normalizeAiRecommendation = (item) => {
  if (typeof item === "string") {
    return {
      title: cleanAiText(item),
      description: "",
      reason: "",
      priority: "media",
    };
  }

  return {
    title: cleanAiText(item?.title || "Recomendación"),
    description: cleanAiText(item?.description || item?.message || ""),
    reason: cleanAiText(item?.reason || ""),
    priority: cleanAiText(item?.priority || "media"),
  };
};

const normalizeAiAlert = (alert) => {
  return {
    severity: cleanAiText(alert?.severity || "media").toLowerCase(),
    blockKey: cleanAiText(alert?.block_key || ""),
    title: cleanAiText(alert?.title || "Alerta relevante"),
    message: cleanAiText(alert?.message || ""),
    implication: cleanAiText(alert?.implication || ""),
  };
};

const severityClass = (severity) => {
  const value = String(severity || "").toLowerCase();

  if (value.includes("alta")) return "severity-alta";
  if (value.includes("media")) return "severity-media";
  return "severity-baja";
};

// =====================
// JSON LIMPIO PARA IA
// =====================
const AI_KPI_CATALOG = {
  "Margen de Rentabilidad": {
    key: "net_margin",
    category: "rentabilidad",
    unit: "percentage",
    higherIsBetter: true,
    threshold: { ok: ">= 10%", warn: "< 10%" },
  },
  "Rendimiento sobre Activos Totales (RAT)": {
    key: "roa",
    category: "rentabilidad",
    unit: "percentage",
    higherIsBetter: true,
    threshold: { ok: ">= 10%", warn: "< 10%" },
  },
  "Rendimiento sobre el Patrimonio": {
    key: "roe",
    category: "rentabilidad",
    unit: "percentage",
    higherIsBetter: true,
    threshold: { ok: ">= 10%", warn: "< 10%" },
  },
  "Razón de Liquidez": {
    key: "current_ratio",
    category: "liquidez",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.0", warn: "< 1.0" },
  },
  "Prueba del Ácido": {
    key: "acid_test",
    category: "liquidez",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 0.8", warn: "< 0.8" },
  },
  "Capital de Trabajo": {
    key: "working_capital",
    category: "liquidez",
    unit: "currency",
    higherIsBetter: true,
    threshold: { ok: "> 0", warn: "<= 0" },
  },
  Apalancamiento: {
    key: "debt_ratio",
    category: "endeudamiento",
    unit: "ratio",
    higherIsBetter: false,
    threshold: { ok: "<= 0.5", warn: "> 0.5" },
  },
  "Razón de Cobertura de Intereses": {
    key: "interest_coverage",
    category: "endeudamiento",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.5", warn: "< 1.5" },
  },
  "Estabilidad Financiera": {
    key: "financial_stability",
    category: "endeudamiento",
    unit: "ratio",
    higherIsBetter: false,
    threshold: { ok: "<= 1.0", warn: "> 1.0" },
  },
  "Rotación de la Cartera": {
    key: "receivables_turnover",
    category: "rotacion",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: "> 0", warn: "<= 0" },
  },
  "Periodo Promedio de Recaudo": {
    key: "average_collection_period",
    category: "rotacion",
    unit: "days",
    higherIsBetter: false,
    threshold: { ok: "<= 60 días", warn: "> 60 días" },
  },
  "Rotación de Inventarios": {
    key: "inventory_turnover",
    category: "rotacion",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: "> 0", warn: "<= 0" },
  },
  "Rotación de Activos Fijos": {
    key: "fixed_asset_turnover",
    category: "rotacion",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.0", warn: "< 1.0" },
  },
  "Rotación de Activos Totales": {
    key: "total_asset_turnover",
    category: "rotacion",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.0", warn: "< 1.0" },
  },
  "Solvencia General": {
    key: "general_solvency",
    category: "estructura",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: "> 1.0", warn: "<= 1.0" },
  },
  "Seguridad a largo plazo": {
    key: "long_term_security",
    category: "estructura",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.0", warn: "< 1.0" },
  },
  "Inmovilización de Cap. Social": {
    key: "fixed_assets_to_capital_stock",
    category: "estructura",
    unit: "ratio",
    higherIsBetter: false,
    threshold: { ok: "<= 1.0", warn: "> 1.0" },
  },
  "Inmovilización de Cap. Contable": {
    key: "fixed_assets_to_equity",
    category: "estructura",
    unit: "ratio",
    higherIsBetter: false,
    threshold: { ok: "<= 1.0", warn: "> 1.0" },
  },
};

const AI_BLOCKS = [
  "rentabilidad",
  "liquidez",
  "endeudamiento",
  "rotacion",
  "estructura",
];

const parseAiValue = (value, unit) => {
  if (value === null || value === undefined || value === "N/A") return null;

  const clean = String(value)
    .replace(/\$/g, "")
    .replace(/,/g, "")
    .replace(/%/g, "")
    .replace(/días/g, "")
    .replace(/día/g, "")
    .trim();

  const number = Number(clean);

  if (Number.isNaN(number)) return null;

  if (unit === "percentage") return number / 100;

  return number;
};

const normalizeAiKpi = (kpi, blockKey) => {
  const meta = AI_KPI_CATALOG[kpi.label];

  if (!meta) {
    return {
      key: null,
      label: kpi.label,
      category: blockKey,
      value: null,
      displayValue: kpi.value,
      unit: "unknown",
      status: kpi.status || "unknown",
      threshold: null,
      higherIsBetter: null,
      note: "KPI no encontrado en el catálogo interno",
    };
  }

  return {
    key: meta.key,
    label: kpi.label,
    category: meta.category,
    value: parseAiValue(kpi.value, meta.unit),
    displayValue: kpi.value,
    unit: meta.unit,
    status: kpi.status || "unknown",
    threshold: meta.threshold,
    higherIsBetter: meta.higherIsBetter,
  };
};

const normalizeAiRawData = (rawData = {}) => {
  return { ...rawData };
};

const normalizeAiPeriod = (period) => {
  const cleanPeriod = {
    id: period.id,
    label: period.label,
    periodDate: period.periodDate,
    financial_blocks: {},
  };

  AI_BLOCKS.forEach((blockKey) => {
    const block = period[blockKey];

    if (!block) return;

    cleanPeriod.financial_blocks[blockKey] = {
      key: blockKey,
      label: blockKey,
      raw_data: normalizeAiRawData(block.datos_crudos || {}),
      kpis: (block.kpis || []).map((kpi) => normalizeAiKpi(kpi, blockKey)),
    };
  });

  return cleanPeriod;
};

const flattenAiKpis = (period) => {
  const result = {};

  Object.values(period.financial_blocks || {}).forEach((block) => {
    (block.kpis || []).forEach((kpi) => {
      if (!kpi.key) return;

      result[kpi.key] = {
        ...kpi,
        period: period.periodDate,
      };
    });
  });

  return result;
};

const formatAiAbsoluteChange = (delta, unit) => {
  if (delta === null || delta === undefined) return null;

  if (unit === "percentage") {
    return `${(delta * 100).toFixed(2)} pp`;
  }

  if (unit === "currency") {
    return currencyFmt.format(delta);
  }

  if (unit === "days") {
    return `${delta.toFixed(0)} días`;
  }

  return delta.toFixed(2);
};

const formatAiRelativeChange = (relative) => {
  if (relative === null || relative === undefined) return null;
  return `${(relative * 100).toFixed(2)}%`;
};

const getAiTrendDirection = (delta, higherIsBetter) => {
  if (delta === 0) return "estable";

  if (higherIsBetter === true) {
    return delta > 0 ? "mejora" : "deterioro";
  }

  if (higherIsBetter === false) {
    return delta < 0 ? "mejora" : "deterioro";
  }

  return delta > 0 ? "aumenta" : "disminuye";
};

const buildAiComparativeKpis = (normalizedPeriods, basePeriodDate) => {
  const sorted = [...normalizedPeriods].sort((a, b) =>
    String(a.periodDate).localeCompare(String(b.periodDate))
  );

  const baseIndex = sorted.findIndex((p) => p.periodDate === basePeriodDate);

  if (baseIndex <= 0) return [];

  const previousPeriod = sorted[baseIndex - 1];
  const currentPeriod = sorted[baseIndex];

  const previousKpis = flattenAiKpis(previousPeriod);
  const currentKpis = flattenAiKpis(currentPeriod);

  const comparative = [];

  Object.keys(currentKpis).forEach((key) => {
    const current = currentKpis[key];
    const previous = previousKpis[key];

    if (!previous || previous.value === null || current.value === null) return;

    const absolute = current.value - previous.value;
    const relative =
      previous.value !== 0 ? absolute / Math.abs(previous.value) : null;

    comparative.push({
      key,
      label: current.label,
      category: current.category,
      unit: current.unit,
      threshold: current.threshold,
      higherIsBetter: current.higherIsBetter,
      previous: {
        period: previous.period,
        value: previous.value,
        displayValue: previous.displayValue,
        status: previous.status,
      },
      current: {
        period: current.period,
        value: current.value,
        displayValue: current.displayValue,
        status: current.status,
      },
      change: {
        absolute,
        displayAbsolute: formatAiAbsoluteChange(absolute, current.unit),
        relative,
        displayRelative: formatAiRelativeChange(relative),
        direction: getAiTrendDirection(absolute, current.higherIsBetter),
      },
    });
  });

  return comparative;
};

const buildAiPayload = (periods, options = {}) => {
  const basePeriodDate =
    options.basePeriodDate || periods?.[periods.length - 1]?.periodDate || null;

  const normalizedPeriods = periods.map(normalizeAiPeriod);

  const basePeriod = normalizedPeriods.find(
    (p) => p.periodDate === basePeriodDate
  );

  const analysisMode =
    normalizedPeriods.length > 1 ? "multiperiodo" : "monoperiodo";

  return {
    prompt_version: "1.2.0",
    analysis_mode: analysisMode,
    language: "es-MX",
    business_context: {
      company_type: "PyME",
      country: "México",
      sector: options.sector || "servicios",
      currency: "MXN",
      periodicity: "anual",
    },
    base_period: {
      id: basePeriod?.id || null,
      label: basePeriod?.label || null,
      periodDate: basePeriod?.periodDate || basePeriodDate,
    },
    periods: normalizedPeriods,
    comparative_kpis:
      analysisMode === "multiperiodo"
        ? buildAiComparativeKpis(normalizedPeriods, basePeriodDate)
        : [],
    instructions: {
      do_not_recalculate: true,
      do_not_invent_missing_data: true,
      use_only_provided_data: true,
      interpret_thresholds: true,
      interpret_trends: analysisMode === "multiperiodo",
      business_sector_focus: "servicios",
      explain_indicator_meaning: true,
      explain_operational_implications: true,
      avoid_internal_status_words: true,
      required_block_keys: [
        "rentabilidad",
        "liquidez",
        "endeudamiento",
        "rotacion",
        "estructura",
      ],
    },
    requested_output: {
      format: "json",
      language: "es-MX",
      style: {
        tone: "profesional, claro, directo, no alarmista",
        sector_focus: "servicios",
        avoid_internal_status_words: true,
        avoid_words: ["ok", "warn", "danger", "status"],
        paragraph_style: "párrafos breves, separados por sección",
      },
      sections: {
        executive_summary: {
          required: true,
          format: {
            title: "string",
            paragraphs: ["string", "string"],
          },
        },
        key_implications: {
          required: true,
          max_items: 4,
          item_format: {
            title: "string",
            indicator: "string",
            value: "string",
            reading: "string",
            implication: "string",
            possible_impact: "string",
          },
        },
        block_interpretations: {
          required: true,
          exact_items: 5,
          required_block_keys: [
            "rentabilidad",
            "liquidez",
            "endeudamiento",
            "rotacion",
            "estructura",
          ],
          item_format: {
            block_key: "string",
            title: "string",
            paragraphs: ["string"],
            indicators_explained: [
              {
                label: "string",
                value: "string",
                reading: "string",
                meaning: "string",
                service_business_implication: "string",
                possible_impact: "string",
              },
            ],
          },
        },
        alerts: {
          required: true,
          purpose: "Alertas generales más importantes del análisis completo",
          max_items: 5,
          item_format: {
            block_key:
              "rentabilidad | liquidez | endeudamiento | rotacion | estructura",
            severity: "baja | media | alta",
            title: "string",
            message: "string",
            implication: "string",
          },
        },
        alerts_by_block: {
          required: true,
          exact_items: 5,
          required_block_keys: [
            "rentabilidad",
            "liquidez",
            "endeudamiento",
            "rotacion",
            "estructura",
          ],
          rule:
            "Debe existir exactamente un objeto por cada block_key. Si no hay alerta relevante en un bloque, indicarlo como nivel bajo y explicar que el bloque no presenta presión significativa.",
          item_format: {
            block_key:
              "rentabilidad | liquidez | endeudamiento | rotacion | estructura",
            severity: "baja | media | alta",
            title: "string",
            message: "string",
            implication: "string",
          },
        },
        recommendations: {
          required: true,
          purpose: "Recomendaciones generales más importantes del análisis completo",
          max_general_recommendations: 5,
          item_format: {
            block_key:
              "rentabilidad | liquidez | endeudamiento | rotacion | estructura",
            title: "string",
            description: "string",
            reason: "string",
            priority: "baja | media | alta",
          },
        },
        recommendations_by_block: {
          required: true,
          exact_items: 5,
          required_block_keys: [
            "rentabilidad",
            "liquidez",
            "endeudamiento",
            "rotacion",
            "estructura",
          ],
          recommendations_per_block: 4,
          rule:
            "Debe existir exactamente un objeto por cada block_key. Cada bloque debe incluir cuatro recomendaciones accionables, incluso si sus indicadores son saludables.",
          item_format: {
            block_key:
              "rentabilidad | liquidez | endeudamiento | rotacion | estructura",
            title: "string",
            recommendations: [
              {
                title: "string",
                description: "string",
                reason: "string",
                priority: "baja | media | alta",
              },
            ],
          },
        },
      },
    },
  };
};

// =====================
// IA: APLICAR, GUARDAR Y CARGAR
// =====================
const applyAiResultToView = (result) => {
  aiResult.value = result;

  const summary = result?.executive_summary || {};
  const summaryParagraphs =
    Array.isArray(summary?.paragraphs) && summary.paragraphs.length > 0
      ? summary.paragraphs
      : summary?.summary
        ? [summary.summary]
        : [fallbackInterpretation];

  executiveSummary.value = {
    title: cleanAiText(
      summary?.title || "Lectura general del desempeño financiero"
    ),
    paragraphs: cleanAiArray(summaryParagraphs),
  };

  keyImplications.value = Array.isArray(result?.key_implications)
    ? result.key_implications.slice(0, 4).map((item) => ({
        title: cleanAiText(item?.title || "Implicación relevante"),
        indicator: cleanAiText(item?.indicator || ""),
        value: cleanAiText(item?.value || ""),
        reading: cleanAiText(item?.reading || ""),
        implication: cleanAiText(item?.implication || ""),
        possible_impact: cleanAiText(item?.possible_impact || ""),
      }))
    : [];

  const preferredAlerts = Array.isArray(result?.alerts_by_block)
    ? result.alerts_by_block
    : Array.isArray(result?.alerts)
      ? result.alerts
      : [];

  aiAlerts.value = preferredAlerts.slice(0, 5).map(normalizeAiAlert);

  const aiRecommendations = Array.isArray(result?.recommendations)
    ? result.recommendations
    : [];

  recommendations.value =
    aiRecommendations.length > 0
      ? aiRecommendations.slice(0, 5).map(normalizeAiRecommendation)
      : [
          {
            title: "Sin recomendaciones automáticas",
            description:
              "No se generaron recomendaciones automáticas con la información disponible.",
            reason:
              "La información recibida no fue suficiente para priorizar acciones.",
            priority: "media",
          },
        ];

  interpretation.value = executiveSummary.value.paragraphs.join(" ");
};

const saveAiAnalysisToFirestore = async (aiPayload, apiResponse) => {
  if (!projectId.value || !apiResponse?.ai_result) return;

  const basePeriod = aiPayload?.base_period || null;
  const basePeriodDate = basePeriod?.periodDate || "actual";

  const periodsIncluded =
    aiPayload?.periods?.map((period) => ({
      id: period.id || null,
      label: period.label || null,
      periodDate: period.periodDate || null,
    })) || [];

  const docData = {
    promptVersion: aiPayload?.prompt_version || "1.2.0",
    analysisMode: aiPayload?.analysis_mode || "multiperiodo",
    basePeriod,
    periodsIncluded,
    model: apiResponse.model || null,
    status: "completed",
    result: apiResponse.ai_result,
    updatedAt: serverTimestamp(),
  };

  const latestRef = doc(
    db,
    "proyectos",
    projectId.value,
    AI_ANALYSIS_COLLECTION,
    AI_LATEST_DOC_ID
  );

  const periodRef = doc(
    db,
    "proyectos",
    projectId.value,
    AI_ANALYSIS_COLLECTION,
    getAiPeriodDocId(basePeriodDate)
  );

  await Promise.all([
    setDoc(latestRef, docData, { merge: true }),
    setDoc(periodRef, docData, { merge: true }),
  ]);

  console.log("✅ Análisis IA guardado en Firestore:", {
    latestPath: `proyectos/${projectId.value}/${AI_ANALYSIS_COLLECTION}/${AI_LATEST_DOC_ID}`,
    periodPath: `proyectos/${projectId.value}/${AI_ANALYSIS_COLLECTION}/${getAiPeriodDocId(
      basePeriodDate
    )}`,
  });
};

const loadSavedAiAnalysisFromFirestore = async (aiPayload) => {
  if (!projectId.value) return false;

  const latestRef = doc(
    db,
    "proyectos",
    projectId.value,
    AI_ANALYSIS_COLLECTION,
    AI_LATEST_DOC_ID
  );

  const snap = await getDoc(latestRef);

  if (!snap.exists()) return false;

  const saved = snap.data();

  const savedBasePeriodDate = saved?.basePeriod?.periodDate;
  const currentBasePeriodDate = aiPayload?.base_period?.periodDate;

  const savedPeriodsCount = saved?.periodsIncluded?.length || 0;
  const currentPeriodsCount = aiPayload?.periods?.length || 0;

  const isSamePromptVersion = saved?.promptVersion === aiPayload?.prompt_version;

  const isSameAnalysisContext =
    isSamePromptVersion &&
    savedBasePeriodDate === currentBasePeriodDate &&
    savedPeriodsCount === currentPeriodsCount &&
    saved?.status === "completed" &&
    saved?.result;

  if (!isSameAnalysisContext) return false;

  applyAiResultToView(saved.result);

  console.log("✅ Análisis IA cargado desde Firestore:", saved);

  return true;
};

const generateAiAnalysis = async (aiPayload) => {
  try {
    aiLoading.value = true;
    aiError.value = null;

    const response = await fetch(
      `${API_BASE_URL}/documents/financial-ai-analysis`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: projectId.value,
          analysis_payload: aiPayload,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(
        errorData?.detail || "No se pudo generar el análisis con IA"
      );
    }

    const data = await response.json();

    applyAiResultToView(data.ai_result);

    await saveAiAnalysisToFirestore(aiPayload, data);

    console.log("✅ Resultado IA Gemini:", data);
  } catch (error) {
    console.error("Error generando análisis con Gemini:", error);

    aiError.value = error.message;

    toast({
      message: error.message || "No se pudo generar la interpretación con IA.",
      type: "warning",
    });
  } finally {
    aiLoading.value = false;
  }
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
      const data = docSnap.data();

      if (data.analisis_rentabilidad || data.rentabilidad) {
        loaded.push({
          id: docSnap.id,
          label: data.label || "Periodo",
          periodDate: data.periodDate || data.label,
          resultados_url: data.resultsFile?.url || null,
          rentabilidad:
            data.analisis_rentabilidad ||
            data.rentabilidad || { datos_crudos: {}, kpis: [] },
          liquidez:
            data.analisis_liquidez ||
            data.liquidez || { datos_crudos: {}, kpis: [] },
          endeudamiento:
            data.analisis_endeudamiento ||
            data.endeudamiento || { datos_crudos: {}, kpis: [] },
          rotacion:
            data.analisis_rotacion ||
            data.rotacion || { datos_crudos: {}, kpis: [] },
          estructura:
            data.analisis_estructura ||
            data.estructura || { datos_crudos: {}, kpis: [] },
        });
      }
    });

    loaded.sort((a, b) =>
      String(a.periodDate).localeCompare(String(b.periodDate))
    );

    rawPeriods.value = loaded;

    console.log(
      "📊 DATOS HISTÓRICOS COMPLETOS DE TODOS LOS MÓDULOS:",
      JSON.parse(JSON.stringify(loaded))
    );

    if (loaded.length > 0) {
      generateDashboardData();

      const aiPayload = buildAiPayload(loaded, {
        basePeriodDate: loaded[loaded.length - 1]?.periodDate,
        sector: "servicios",
      });

      console.log("🤖 JSON LIMPIO PARA IA:", JSON.parse(JSON.stringify(aiPayload)));

      const hasSavedAiAnalysis = await loadSavedAiAnalysisFromFirestore(aiPayload);

      if (!hasSavedAiAnalysis) {
        await generateAiAnalysis(aiPayload);
      }
    }
  } catch (error) {
    console.error("Error cargando resumen multiperiodo:", error);

    toast({
      message: "No se pudo cargar el resumen multiperiodo.",
      type: "warning",
    });
  } finally {
    loading.value = false;
  }
};

const generateDashboardData = () => {
  const periods = rawPeriods.value;
  chartLabels.value = periods.map((p) => p.label);

  const lastP = periods[periods.length - 1];
  const prevP = periods.length > 1 ? periods[periods.length - 2] : lastP;

  const getKpiValue = (kpis, keyword) => {
    if (!kpis) return 0;
    const item = kpis.find((k) =>
      k.label.toLowerCase().includes(keyword.toLowerCase())
    );
    const val = item ? parseVal(item.value) : 0;
    return isNaN(val) ? 0 : val;
  };

  const getKpiStatus = (kpis, keyword) => {
    if (!kpis) return "gray";
    const item = kpis.find((k) =>
      k.label.toLowerCase().includes(keyword.toLowerCase())
    );
    return item?.status === "ok" ? "ok" : "warn";
  };

  ingresosValues.value = periods.map(
    (p) => p.rentabilidad.datos_crudos?.ventas_netas || 0
  );

  utilidadValues.value = periods.map(
    (p) => p.rentabilidad.datos_crudos?.utilidad_neta || 0
  );

  const lastIngresos = ingresosValues.value[ingresosValues.value.length - 1];

  const prevIngresos =
    ingresosValues.value.length > 1
      ? ingresosValues.value[ingresosValues.value.length - 2]
      : lastIngresos;

  const deltaIngresos = prevIngresos
    ? (lastIngresos - prevIngresos) / prevIngresos
    : 0;

  const lastUtilidad = utilidadValues.value[utilidadValues.value.length - 1];

  const prevUtilidad =
    utilidadValues.value.length > 1
      ? utilidadValues.value[utilidadValues.value.length - 2]
      : lastUtilidad;

  const deltaUtilidad = prevUtilidad
    ? (lastUtilidad - prevUtilidad) / prevUtilidad
    : 0;

  const lastMargen = lastIngresos ? lastUtilidad / lastIngresos : 0;
  const prevMargen = prevIngresos ? prevUtilidad / prevIngresos : 0;
  const deltaMargen = lastMargen - prevMargen;

  const lastLiq = getKpiValue(lastP.liquidez.kpis, "Razón de Liquidez");
  const prevLiq = getKpiValue(prevP.liquidez.kpis, "Razón de Liquidez");
  const deltaLiq = lastLiq - prevLiq;

  kpis.value = [
    {
      label: "Ingresos Totales",
      value: currencyFmt.format(lastIngresos),
      status: lastIngresos > 0 ? "ok" : "warn",
      deltaType: deltaIngresos >= 0 ? "up" : "down",
      deltaValue: `${deltaIngresos > 0 ? "+" : ""}${(
        deltaIngresos * 100
      ).toFixed(1)}%`,
      deltaNote: periods.length > 1 ? `vs ${prevP.label}` : "Sin periodo previo",
    },
    {
      label: "Utilidad Neta",
      value: currencyFmt.format(lastUtilidad),
      status: lastUtilidad > 0 ? "ok" : "warn",
      deltaType: deltaUtilidad >= 0 ? "up" : "down",
      deltaValue: `${deltaUtilidad > 0 ? "+" : ""}${(
        deltaUtilidad * 100
      ).toFixed(1)}%`,
      deltaNote: periods.length > 1 ? `vs ${prevP.label}` : "Sin periodo previo",
    },
    {
      label: "Margen Neto",
      value: percentFmt.format(lastMargen),
      status: lastMargen > 0.1 ? "ok" : "warn",
      deltaType: deltaMargen >= 0 ? "up" : "down",
      deltaValue: `${deltaMargen > 0 ? "+" : ""}${(
        deltaMargen * 100
      ).toFixed(1)} pp`,
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

  cards.value = [
    {
      title: "Rentabilidad",
      icon: "trending_up",
      detailRoute: "rentabilidadMulti",
      items: [
        {
          label: "ROE",
          target: ">10%",
          value: `${getKpiValue(lastP.rentabilidad.kpis, "Patrimonio").toFixed(
            1
          )}%`,
          dot: getKpiStatus(lastP.rentabilidad.kpis, "Patrimonio"),
        },
        {
          label: "Margen Neto",
          target: ">10%",
          value: `${getKpiValue(
            lastP.rentabilidad.kpis,
            "Margen de Rentabilidad"
          ).toFixed(1)}%`,
          dot: getKpiStatus(
            lastP.rentabilidad.kpis,
            "Margen de Rentabilidad"
          ),
        },
      ],
    },
    {
      title: "Liquidez",
      icon: "attach_money",
      detailRoute: "liquidezMulti",
      items: [
        {
          label: "Prueba Ácida",
          target: ">0.8",
          value: getKpiValue(lastP.liquidez.kpis, "Prueba del Ácido").toFixed(2),
          dot: getKpiStatus(lastP.liquidez.kpis, "Prueba del Ácido"),
        },
        {
          label: "Cap. Trabajo",
          target: "> $0",
          value: currencyFmt.format(
            getKpiValue(lastP.liquidez.kpis, "Capital de Trabajo")
          ),
          dot: getKpiStatus(lastP.liquidez.kpis, "Capital de Trabajo"),
        },
      ],
    },
    {
      title: "Endeudamiento",
      icon: "account_balance_wallet",
      detailRoute: "endeudamientoMulti",
      items: [
        {
          label: "Nivel Deuda",
          target: "<0.5",
          value: getKpiValue(lastP.endeudamiento.kpis, "Apalancamiento").toFixed(
            2
          ),
          dot: getKpiStatus(lastP.endeudamiento.kpis, "Apalancamiento"),
        },
        {
          label: "Cobertura Int.",
          target: ">1.5x",
          value: `${getKpiValue(
            lastP.endeudamiento.kpis,
            "Cobertura de Intereses"
          ).toFixed(1)}x`,
          dot: getKpiStatus(
            lastP.endeudamiento.kpis,
            "Cobertura de Intereses"
          ),
        },
      ],
    },
    {
      title: "Rotación de Activos",
      icon: "sync_alt",
      detailRoute: "rotacionMulti",
      items: [
        {
          label: "Rot. Inventario",
          target: ">4.0x",
          value: (() => {
            const raw = lastP.rotacion.kpis?.find((k) =>
              k.label.toLowerCase().includes("inventarios")
            );
            if (!raw || raw.value === "N/A") return "N/A";
            const num = parseVal(raw.value);
            return isNaN(num) ? "N/A" : `${num.toFixed(1)}x`;
          })(),
          dot: getKpiStatus(lastP.rotacion.kpis, "Inventarios"),
        },
        {
          label: "Periodo Cobro",
          target: "<60 días",
          value: `${getKpiValue(lastP.rotacion.kpis, "Recaudo").toFixed(
            0
          )} días`,
          dot: getKpiStatus(lastP.rotacion.kpis, "Recaudo"),
        },
      ],
    },
    {
      title: "Estructura Financiera",
      icon: "layers",
      detailRoute: "estructuraMulti",
      items: [
        {
          label: "Solvencia",
          target: ">1.0",
          value: getKpiValue(
            lastP.estructura.kpis,
            "Solvencia General"
          ).toFixed(2),
          dot: getKpiStatus(lastP.estructura.kpis, "Solvencia General"),
        },
        {
          label: "Seguridad LP",
          target: ">=1.0",
          value: isNaN(
            getKpiValue(lastP.estructura.kpis, "Seguridad a largo plazo")
          )
            ? "N/A"
            : getKpiValue(
                lastP.estructura.kpis,
                "Seguridad a largo plazo"
              ).toFixed(2),
          dot: getKpiStatus(lastP.estructura.kpis, "Seguridad a largo plazo"),
        },
      ],
    },
  ];

  const calcPct = (val, total) =>
    total ? `${((val / total) * 100).toFixed(1)}%` : "0%";

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
        {
          concept: "Ingresos",
          value: currencyFmt.format(v),
          pct: "100%",
          tone: "income",
        },
        {
          concept: "Costos",
          value: `(${currencyFmt.format(costo)})`,
          pct: calcPct(costo, v),
          tone: "negative",
        },
        {
          concept: "Gastos",
          value: `(${currencyFmt.format(gastos > 0 ? gastos : 0)})`,
          pct: calcPct(gastos > 0 ? gastos : 0, v),
          tone: "negative",
        },
        {
          concept: "Impuestos y Otros",
          value: `(${currencyFmt.format(impuestos > 0 ? impuestos : 0)})`,
          pct: calcPct(impuestos > 0 ? impuestos : 0, v),
          tone: "negative",
        },
        {
          concept: "Total (Utilidad Neta)",
          value: currencyFmt.format(ut_neta),
          pct: calcPct(ut_neta, v),
          tone: "total",
        },
      ],
    };
  });

  if (estructuraResultadoOptions.value.length > 0) {
    selectedResultPeriod.value = estructuraResultadoOptions.value[0].period;
  }
};

const estructuraResultado = computed(() => {
  return (
    estructuraResultadoOptions.value.find(
      (item) => item.period === selectedResultPeriod.value
    ) || { rows: [], pdfUrl: null }
  );
});

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

  const yAxisLabels = [
    fmtLabel(yMax),
    fmtLabel(yMax - finalRange / 3),
    fmtLabel(yMax - (finalRange / 3) * 2),
    fmtLabel(yMin),
  ];

  const xStep = labels.length > 1 ? 600 / (labels.length - 1) : 0;

  const points = values.map((val, i) => {
    const x = labels.length > 1 ? 100 + i * xStep : 400;
    const y = 230 - ((val - yMin) / finalRange) * 180;

    return {
      x,
      y,
      label: labels[i],
      bold: i === values.length - 1,
      value: val,
      isCurrency,
    };
  });

  return { yAxisLabels, points };
};

const ingresosChart = computed(() =>
  buildChartModel(ingresosValues.value, chartLabels.value, true)
);

const utilidadChart = computed(() =>
  buildChartModel(utilidadValues.value, chartLabels.value, true)
);

const baselineY = 230;

const linePathFor = (chart) =>
  chart?.points?.length
    ? chart.points
        .map((p, i) => (i === 0 ? `M${p.x} ${p.y}` : `L${p.x} ${p.y}`))
        .join(" ")
    : "";

const areaPathFor = (chart) => {
  const pts = chart?.points || [];
  if (!pts.length) return "";

  const first = pts[0];
  const last = pts[pts.length - 1];
  const mid = pts.map((p) => `L${p.x} ${p.y}`).join(" ");

  return `M${first.x} ${baselineY} L${first.x} ${first.y} ${mid} L${last.x} ${baselineY} Z`;
};

// =====================
// NAVEGACIÓN Y ACCIONES
// =====================
function pushWithProject(name) {
  if (projectId.value) {
    router.push({ name, params: { id_proyecto: projectId.value } });
  }
}

function goDetail(routeName) {
  pushWithProject(routeName);
}

function openPDF() {
  const url = estructuraResultado.value?.pdfUrl;

  if (url) {
    window.open(url, "_blank");
  } else {
    toast({
      message: "No se encontró el documento PDF para este periodo.",
      type: "warning",
    });
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
          <span
            class="delta-pill"
            :class="k.deltaType === 'up' ? 'delta-up' : 'delta-down'"
          >
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
            <h3>Evolución de ingresos</h3>
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
          <svg
            class="chart-svg"
            fill="none"
            preserveAspectRatio="none"
            viewBox="0 0 800 300"
          >
            <defs>
              <linearGradient id="gradient-ingresos" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#299de0" stop-opacity="0.15" />
                <stop offset="100%" stop-color="#299de0" stop-opacity="0" />
              </linearGradient>
            </defs>

            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50" />
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110" />
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170" />
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230" />

            <path :d="areaPathFor(ingresosChart)" fill="url(#gradient-ingresos)" />
            <path
              :d="linePathFor(ingresosChart)"
              fill="none"
              stroke="#299de0"
              stroke-linecap="round"
              stroke-width="3"
            />

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
            />

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
            />

            <g v-if="hoveredIngresosPoint" style="pointer-events: none;">
              <rect
                :x="hoveredIngresosPoint.x - 45"
                :y="hoveredIngresosPoint.y - 42"
                width="90"
                height="26"
                rx="6"
                fill="#0e161b"
                opacity="0.95"
              />
              <polygon
                :points="`${hoveredIngresosPoint.x - 6},${hoveredIngresosPoint.y - 16} ${hoveredIngresosPoint.x + 6},${hoveredIngresosPoint.y - 16} ${hoveredIngresosPoint.x},${hoveredIngresosPoint.y - 10}`"
                fill="#0e161b"
                opacity="0.95"
              />
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
          <svg
            class="chart-svg"
            fill="none"
            preserveAspectRatio="none"
            viewBox="0 0 800 300"
          >
            <defs>
              <linearGradient id="gradient-utilidad" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#299de0" stop-opacity="0.15" />
                <stop offset="100%" stop-color="#299de0" stop-opacity="0" />
              </linearGradient>
            </defs>

            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="50" y2="50" />
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="110" y2="110" />
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="170" y2="170" />
            <line stroke="#f1f5f9" stroke-width="1" x1="50" x2="750" y1="230" y2="230" />

            <path :d="areaPathFor(utilidadChart)" fill="url(#gradient-utilidad)" />
            <path
              :d="linePathFor(utilidadChart)"
              fill="none"
              stroke="#299de0"
              stroke-linecap="round"
              stroke-width="3"
            />

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
            />

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
            />

            <g v-if="hoveredUtilidadPoint" style="pointer-events: none;">
              <rect
                :x="hoveredUtilidadPoint.x - 45"
                :y="hoveredUtilidadPoint.y - 42"
                width="90"
                height="26"
                rx="6"
                fill="#0e161b"
                opacity="0.95"
              />
              <polygon
                :points="`${hoveredUtilidadPoint.x - 6},${hoveredUtilidadPoint.y - 16} ${hoveredUtilidadPoint.x + 6},${hoveredUtilidadPoint.y - 16} ${hoveredUtilidadPoint.x},${hoveredUtilidadPoint.y - 10}`"
                fill="#0e161b"
                opacity="0.95"
              />
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
          <span class="material-symbols-outlined card-ico" aria-hidden="true">
            {{ c.icon }}
          </span>
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
          <button class="link-btn" type="button" @click="goDetail(c.detailRoute)">
            Ver detalle
          </button>
        </div>
      </article>
    </section>

    <!-- Resumen del resultado -->
    <section class="result-card">
      <div class="result-head">
        <div class="result-title">
          <span class="material-symbols-outlined" aria-hidden="true">
            receipt_long
          </span>
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
          <span
            class="material-symbols-outlined"
            style="vertical-align: middle; font-size: 16px; margin-right: 4px;"
          >
            open_in_new
          </span>
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

        <p v-if="aiLoading" class="note-text">
          Generando interpretación automática...
        </p>

        <p v-else-if="aiError" class="note-text">
          No se pudo generar la interpretación automática. Se muestra información base del sistema.
        </p>

        <div v-else class="ai-content">
          <h4 class="ai-title">{{ executiveSummary.title }}</h4>

          <p
            v-for="(paragraph, idx) in executiveSummary.paragraphs"
            :key="`summary-${idx}`"
            class="ai-paragraph"
          >
            {{ paragraph }}
          </p>

          <div v-if="keyImplications.length" class="ai-section">
            <h4 class="ai-section-title">Implicaciones principales</h4>

            <div
              v-for="(item, idx) in keyImplications"
              :key="`implication-${idx}`"
              class="ai-finding"
            >
              <p class="ai-finding-title">{{ item.title }}</p>

              <p v-if="item.indicator || item.value || item.reading" class="ai-finding-meta">
                <span v-if="item.indicator">{{ item.indicator }}</span>
                <span v-if="item.value"> · {{ item.value }}</span>
                <span v-if="item.reading"> · {{ item.reading }}</span>
              </p>

              <p v-if="item.implication" class="ai-finding-text">
                {{ item.implication }}
              </p>

              <p v-if="item.possible_impact" class="ai-impact">
                {{ item.possible_impact }}
              </p>
            </div>
          </div>

          <div v-if="aiAlerts.length" class="ai-section">
            <h4 class="ai-section-title">Alertas por bloque</h4>

            <div
              v-for="(alert, idx) in aiAlerts"
              :key="`alert-${idx}`"
              class="ai-alert"
              :class="severityClass(alert.severity)"
            >
              <p class="ai-finding-title">{{ alert.title }}</p>

              <p v-if="alert.message" class="ai-finding-text">
                {{ alert.message }}
              </p>

              <p v-if="alert.implication" class="ai-impact">
                {{ alert.implication }}
              </p>
            </div>
          </div>
        </div>
      </article>

      <article class="note note-white">
        <div class="note-head">
          <div class="tag tag-green">
            <span class="material-symbols-outlined">checklist</span>
          </div>
          <h3>Recomendaciones</h3>
        </div>

        <ul class="list">
          <li v-if="aiLoading">
            <span class="material-symbols-outlined">hourglass_empty</span>
            <span>Generando recomendaciones...</span>
          </li>

          <li v-else v-for="(item, idx) in recommendations" :key="idx">
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
  padding: 20px;
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
  background: rgba(255, 255, 255, 0.72);
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
.ai-impact {
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