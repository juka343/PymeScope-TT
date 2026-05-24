<script setup>
import { ref, onMounted } from "vue";
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
const { toast } = useToast();

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api";

const AI_ANALYSIS_COLLECTION = "ai_analysis";
const AI_LATEST_DOC_ID = "resumen_monoperiodo_latest";
const AI_PROMPT_VERSION = "1.2.1";

const getAiPeriodDocId = (basePeriodDate) => {
  return `resumen_monoperiodo_${basePeriodDate || "actual"}`;
};

const loading = ref(true);
const projectId = ref(null);
const rawPeriod = ref(null);

const aiLoading = ref(false);
const aiError = ref(null);
const aiResult = ref(null);

const fallbackInterpretation =
  "La empresa presenta información financiera suficiente para generar una lectura general del periodo. Conviene revisar la rentabilidad, liquidez, endeudamiento, rotación de activos y estructura financiera de forma conjunta.";

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

// Formateadores
const currencyFmt = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const percentFmt = new Intl.NumberFormat("es-MX", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 2,
});

// ===== ESTADO REACTIVO =====
const kpis = ref([
  { label: "Ingresos Totales", value: "$0", status: "gray" },
  { label: "Utilidad Neta", value: "$0", status: "gray" },
  { label: "Margen Neto", value: "0%", status: "gray" },
  { label: "Liquidez General", value: "0.0", status: "gray" },
]);

const cards = ref([
  {
    title: "Rentabilidad",
    icon: "trending_up",
    detailRoute: "rentabilidad",
    items: [],
  },
  {
    title: "Liquidez",
    icon: "attach_money",
    detailRoute: "liquidez",
    items: [],
  },
  {
    title: "Endeudamiento",
    icon: "account_balance_wallet",
    detailRoute: "endeudamiento",
    items: [],
  },
  {
    title: "Rotación de Activos",
    icon: "sync_alt",
    detailRoute: "rotacion",
    items: [],
  },
  {
    title: "Estructura Financiera",
    icon: "layers",
    detailRoute: "estructura",
    items: [],
  },
]);

const periodLabel = ref("");
const resultadosPdfUrl = ref(null);

// ===== ESTRUCTURA DEL RESULTADO =====
const estructuraResultado = ref({
  period: "",
  rows: [],
});

// =====================
// HELPERS IA
// =====================
const BLOCK_LABELS = {
  rentabilidad: "Rentabilidad",
  liquidez: "Liquidez",
  endeudamiento: "Endeudamiento",
  rotacion: "Rotación de activos",
  estructura: "Estructura financiera",
};

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

const normalizeSeverityKey = (value) => {
  const text = cleanAiText(value).toLowerCase();

  if (text.includes("alta")) return "alta";
  if (text.includes("baja")) return "baja";
  return "media";
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
    block_key: item?.block_key || null,
    title: cleanAiText(item?.title || "Recomendación"),
    description: cleanAiText(item?.description || item?.message || ""),
    reason: cleanAiText(item?.reason || ""),
    priority: cleanAiText(item?.priority || "media"),
  };
};

const parseAiValue = (value, unit) => {
  if (
    value === null ||
    value === undefined ||
    value === "N/A" ||
    value === "Sin Inventario" ||
    value === "Sin Deuda LP"
  ) {
    return null;
  }

  const clean = String(value)
    .replace(/\$/g, "")
    .replace(/,/g, "")
    .replace(/%/g, "")
    .replace(/días/g, "")
    .replace(/día/g, "")
    .trim();

  if (!clean) return null;

  const number = Number(clean);

  if (Number.isNaN(number)) return null;

  if (unit === "percentage") return number / 100;

  return number;
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
    threshold: { ok: ">= 10%", warn: ">= 0% y < 10%", danger: "< 0%" },
  },
  "Rendimiento sobre Activos Totales (RAT)": {
    key: "roa",
    category: "rentabilidad",
    unit: "percentage",
    higherIsBetter: true,
    threshold: { ok: ">= 5%", warn: ">= 0% y < 5%", danger: "< 0%" },
  },
  "Rendimiento sobre el Patrimonio": {
    key: "roe",
    category: "rentabilidad",
    unit: "percentage",
    higherIsBetter: true,
    threshold: { ok: ">= 10%", warn: ">= 0% y < 10%", danger: "< 0%" },
  },
  "Razón de Liquidez": {
    key: "current_ratio",
    category: "liquidez",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.0", warn: ">= 0.8 y < 1.0", danger: "< 0.8" },
  },
  "Prueba del Ácido": {
    key: "acid_test",
    category: "liquidez",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 0.8", warn: ">= 0.5 y < 0.8", danger: "< 0.5" },
  },
  "Capital de Trabajo": {
    key: "working_capital",
    category: "liquidez",
    unit: "currency",
    higherIsBetter: true,
    threshold: { ok: "> $0", warn: "$0", danger: "< $0" },
  },
  Apalancamiento: {
    key: "debt_ratio",
    category: "endeudamiento",
    unit: "ratio",
    higherIsBetter: false,
    threshold: { ok: "<= 0.5", warn: "> 0.5 y <= 0.7", danger: "> 0.7" },
  },
  "Razón de Cobertura de Intereses": {
    key: "interest_coverage",
    category: "endeudamiento",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.5", warn: ">= 1.0 y < 1.5", danger: "< 1.0" },
  },
  "Estabilidad Financiera": {
    key: "financial_stability",
    category: "endeudamiento",
    unit: "ratio",
    higherIsBetter: false,
    threshold: { ok: "<= 1.0", warn: "> 1.0 y <= 1.5", danger: "> 1.5" },
  },
  "Rotación de la Cartera": {
    key: "receivables_turnover",
    category: "rotacion",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 4.0", warn: "> 0 y < 4.0", danger: "<= 0" },
  },
  "Periodo Promedio de Recaudo": {
    key: "average_collection_period",
    category: "rotacion",
    unit: "days",
    higherIsBetter: false,
    threshold: { ok: "<= 60 días", warn: "> 60 y <= 90 días", danger: "> 90 días" },
  },
  "Rotación de Inventarios": {
    key: "inventory_turnover",
    category: "rotacion",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: "> 0", warn: "N/A", danger: "<= 0" },
  },
  "Rotación de Activos Fijos": {
    key: "fixed_asset_turnover",
    category: "rotacion",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.0", warn: ">= 0.5 y < 1.0", danger: "< 0.5" },
  },
  "Rotación de Activos Totales": {
    key: "total_asset_turnover",
    category: "rotacion",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.0", warn: ">= 0.5 y < 1.0", danger: "< 0.5" },
  },
  "Solvencia General": {
    key: "general_solvency",
    category: "estructura",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: "> 1.0", warn: ">= 0.8 y <= 1.0", danger: "< 0.8" },
  },
  "Seguridad a largo plazo": {
    key: "long_term_security",
    category: "estructura",
    unit: "ratio",
    higherIsBetter: true,
    threshold: { ok: ">= 1.0", warn: ">= 0.5 y < 1.0", danger: "< 0.5" },
  },
  "Inmovilización de Cap. Social": {
    key: "fixed_assets_to_capital_stock",
    category: "estructura",
    unit: "ratio",
    higherIsBetter: false,
    threshold: { ok: "<= 1.0", warn: "> 1.0 y <= 1.5", danger: "> 1.5" },
  },
  "Inmovilización de Cap. Contable": {
    key: "fixed_assets_to_equity",
    category: "estructura",
    unit: "ratio",
    higherIsBetter: false,
    threshold: { ok: "<= 1.0", warn: "> 1.0 y <= 1.5", danger: "> 1.5" },
  },
};

const AI_BLOCKS = [
  "rentabilidad",
  "liquidez",
  "endeudamiento",
  "rotacion",
  "estructura",
];

const normalizeAiKpi = (kpi, blockKey) => {
  const meta = AI_KPI_CATALOG[kpi?.label];

  if (!meta) {
    return {
      key: null,
      label: kpi?.label || "KPI sin etiqueta",
      category: blockKey,
      value: null,
      displayValue: kpi?.value || null,
      unit: "unknown",
      status: kpi?.status || "unknown",
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

const buildAiPayload = (periods, options = {}) => {
  const basePeriodDate =
    options.basePeriodDate || periods?.[periods.length - 1]?.periodDate || null;

  const normalizedPeriods = periods.map(normalizeAiPeriod);

  const basePeriod = normalizedPeriods.find(
    (p) => p.periodDate === basePeriodDate
  );

  return {
    prompt_version: AI_PROMPT_VERSION,
    analysis_mode: "monoperiodo",
    language: "es-MX",
    business_context: {
      company_type: "PyME",
      country: "México",
      sector: options.sector || "servicios",
      currency: "MXN",
      periodicity: options.periodicity || "anual",
    },
    base_period: {
      id: basePeriod?.id || null,
      label: basePeriod?.label || null,
      periodDate: basePeriod?.periodDate || basePeriodDate,
    },
    periods: normalizedPeriods,
    comparative_kpis: [],
    instructions: {
      do_not_recalculate: true,
      do_not_invent_missing_data: true,
      use_only_provided_data: true,
      interpret_thresholds: true,
      interpret_trends: false,
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
          purpose:
            "Alertas generales más importantes del análisis completo. No deben ser una lista exhaustiva por bloque.",
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
          purpose:
            "Recomendaciones generales del negocio completo. No deben estar agrupadas por bloque. Deben priorizar acciones transversales para la empresa completa.",
          max_general_recommendations: 5,
          rule:
            "No repetir literalmente las recomendaciones de recommendations_by_block. Estas recomendaciones deben integrar el diagnóstico completo y priorizar acciones generales.",
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
            "Debe existir exactamente un objeto por cada block_key. Cada bloque debe incluir cuatro recomendaciones accionables específicas para su pantalla individual, incluso si sus indicadores son saludables.",
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

  // En el resumen general usamos alertas generales.
  // alerts_by_block se reserva para pantallas específicas.
  const generalAlerts = Array.isArray(result?.alerts) ? result.alerts : [];

  aiAlerts.value = generalAlerts.slice(0, 5).map((alert) => {
    const severity = cleanAiText(alert?.severity || "media");
    const blockKey = alert?.block_key || null;

    return {
      block_key: blockKey,
      block_name: BLOCK_LABELS[blockKey] || cleanAiText(alert?.block_name || ""),
      severity,
      severityKey: normalizeSeverityKey(severity),
      title: cleanAiText(alert?.title || "Alerta relevante"),
      message: cleanAiText(alert?.message || alert?.evidence || ""),
      implication: cleanAiText(alert?.implication || ""),
    };
  });

  // IMPORTANTE:
  // En el resumen general SOLO usamos result.recommendations.
  // recommendations_by_block se usa en las pantallas individuales.
  const generalRecommendations = Array.isArray(result?.recommendations)
    ? result.recommendations
    : [];

  recommendations.value =
    generalRecommendations.length > 0
      ? generalRecommendations.slice(0, 5).map(normalizeAiRecommendation)
      : [
          {
            title: "Sin recomendaciones automáticas",
            description:
              "No se generaron recomendaciones automáticas con la información disponible.",
            reason:
              "La información recibida no fue suficiente para priorizar acciones generales.",
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
    promptVersion: aiPayload?.prompt_version || AI_PROMPT_VERSION,
    analysisMode: aiPayload?.analysis_mode || "monoperiodo",
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

  console.log("✅ Análisis IA monoperiodo guardado en Firestore:", {
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

  const savedBasePeriodId = saved?.basePeriod?.id;
  const currentBasePeriodId = aiPayload?.base_period?.id;

  const savedPeriodsCount = saved?.periodsIncluded?.length || 0;
  const currentPeriodsCount = aiPayload?.periods?.length || 0;

  const isSamePromptVersion = saved?.promptVersion === aiPayload?.prompt_version;

  const isSameAnalysisContext =
    isSamePromptVersion &&
    savedBasePeriodDate === currentBasePeriodDate &&
    savedBasePeriodId === currentBasePeriodId &&
    savedPeriodsCount === currentPeriodsCount &&
    saved?.analysisMode === "monoperiodo" &&
    saved?.status === "completed" &&
    saved?.result;

  if (!isSameAnalysisContext) return false;

  applyAiResultToView(saved.result);

  console.log("✅ Análisis IA monoperiodo cargado desde Firestore:", saved);

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

    console.log("✅ Resultado IA Gemini monoperiodo:", data);
  } catch (error) {
    console.error("Error generando análisis monoperiodo con Gemini:", error);

    aiError.value = error.message;

    toast({
      message: error.message || "No se pudo generar la interpretación con IA.",
      type: "warning",
    });
  } finally {
    aiLoading.value = false;
  }
};

// ===== LÓGICA DE CARGA DE DATOS =====
const fetchDashboardData = async () => {
  try {
    projectId.value = route.params.id_proyecto;

    if (!projectId.value) {
      console.error("Falta ID Proyecto");
      return;
    }

    const periodosRef = collection(db, "proyectos", projectId.value, "periodos");
    const snapshot = await getDocs(periodosRef);

    let dataList = [];

    snapshot.forEach((docSnap) => {
      const data = docSnap.data();

      if (data.rentabilidad || data.analisis_rentabilidad) {
        dataList.push({
          id: docSnap.id,
          label: data.label || docSnap.id,
          periodDate: data.periodDate || data.label || docSnap.id,
          data,
        });
      }
    });

    if (dataList.length > 0) {
      dataList.sort((a, b) =>
        String(a.periodDate).localeCompare(String(b.periodDate))
      );

      const latest = dataList[dataList.length - 1];
      const d = latest.data;

      const dashboardData = {
        id: latest.id,
        label: latest.label,
        periodDate: latest.periodDate,
        periodo: latest.label,
        resultados_url: d.resultsFile?.url || d.resultados_url || null,
        rentabilidad:
          d.rentabilidad ||
          d.analisis_rentabilidad || { datos_crudos: {}, kpis: [] },
        liquidez:
          d.liquidez ||
          d.analisis_liquidez || { datos_crudos: {}, kpis: [] },
        endeudamiento:
          d.endeudamiento ||
          d.analisis_endeudamiento || { datos_crudos: {}, kpis: [] },
        estructura:
          d.estructura ||
          d.analisis_estructura || { datos_crudos: {}, kpis: [] },
        rotacion:
          d.rotacion ||
          d.analisis_rotacion || { datos_crudos: {}, kpis: [] },
      };

      rawPeriod.value = dashboardData;
      resultadosPdfUrl.value = dashboardData.resultados_url;

      console.log("📊 KPIs DE TODOS LOS MÓDULOS (MONOPERIODO):", {
        rentabilidad: dashboardData.rentabilidad.kpis,
        liquidez: dashboardData.liquidez.kpis,
        endeudamiento: dashboardData.endeudamiento.kpis,
        estructura: dashboardData.estructura.kpis,
        rotacion: dashboardData.rotacion.kpis,
      });

      const aiPayload = buildAiPayload([dashboardData], {
        basePeriodDate: dashboardData.periodDate,
        sector: "servicios",
        periodicity: "anual",
      });

      console.log(
        "🤖 JSON LIMPIO PARA IA (MONOPERIODO):",
        JSON.parse(JSON.stringify(aiPayload))
      );

      mapDataToDashboard(dashboardData);

      periodLabel.value = dashboardData.periodo
        ? `Periodo: ${dashboardData.periodo}`
        : "Periodo Actual";

      const hasSavedAiAnalysis = await loadSavedAiAnalysisFromFirestore(
        aiPayload
      );

      if (!hasSavedAiAnalysis) {
        await generateAiAnalysis(aiPayload);
      }
    } else {
      interpretation.value = "No hay análisis disponibles.";
    }
  } catch (error) {
    console.error("Error cargando dashboard:", error);
    interpretation.value = "Error de conexión.";

    toast({
      message: "No se pudo cargar el resumen monoperiodo.",
      type: "warning",
    });
  } finally {
    loading.value = false;
  }
};

// ===== MAPEO DE DATOS =====
const mapDataToDashboard = (data) => {
  const rent = data.rentabilidad || { datos_crudos: {}, kpis: [] };
  const liq = data.liquidez || { datos_crudos: {}, kpis: [] };
  const end = data.endeudamiento || { datos_crudos: {}, kpis: [] };
  const est = data.estructura || { datos_crudos: {}, kpis: [] };
  const rot = data.rotacion || { datos_crudos: {}, kpis: [] };

  const ventas = rent.datos_crudos?.ventas_netas || 0;
  const utNeta = rent.datos_crudos?.utilidad_neta || 0;
  const costo = rot.datos_crudos?.costo_ventas || 0;
  const utOperacion = end.datos_crudos?.utilidad_operacion || 0;

  kpis.value = [
    {
      label: "Ingresos Totales",
      value: currencyFmt.format(ventas),
      status: ventas > 0 ? "ok" : "warn",
    },
    {
      label: "Utilidad Neta",
      value: currencyFmt.format(utNeta),
      status: utNeta > 0 ? "ok" : "warn",
    },
    {
      label: "Margen Neto",
      value: percentFmt.format(ventas ? utNeta / ventas : 0),
      status: ventas && utNeta / ventas > 0.1 ? "ok" : "warn",
    },
    {
      label: "Liquidez General",
      value: findKpiValue(liq.kpis, "Razón de Liquidez") || "0.0",
      status: isStatusOk(liq.kpis, "Razón de Liquidez") ? "ok" : "warn",
    },
  ];

  const findKpiNota = (kpis, keyword) => {
    if (!kpis) return null;
    const item = kpis.find((k) =>
      k.label.toLowerCase().includes(keyword.toLowerCase())
    );
    return item?.nota_periodo || null;
  };

  cards.value[0].items = [
    {
      label: "ROE",
      target: ">10%",
      value: findKpiValue(rent.kpis, "Patrimonio") || "-",
      dot: getDotColor(rent.kpis, "Patrimonio"),
      nota: findKpiNota(rent.kpis, "Patrimonio"),
    },
    {
      label: "Margen Neto",
      target: ">10%",
      value: findKpiValue(rent.kpis, "Margen de Rentabilidad") || "-",
      dot: getDotColor(rent.kpis, "Margen de Rentabilidad"),
    },
  ];

  cards.value[1].items = [
    {
      label: "Prueba Ácida",
      target: ">0.8",
      value: findKpiValue(liq.kpis, "Prueba del Ácido") || "-",
      dot: getDotColor(liq.kpis, "Prueba del Ácido"),
    },
    {
      label: "Cap. Trabajo",
      target: "> $0",
      value: findKpiValue(liq.kpis, "Capital de Trabajo") || "-",
      dot: getDotColor(liq.kpis, "Capital de Trabajo"),
    },
  ];

  cards.value[2].items = [
    {
      label: "Nivel Deuda",
      target: "<0.5",
      value: findKpiValue(end.kpis, "Apalancamiento") || "-",
      dot: getDotColor(end.kpis, "Apalancamiento"),
    },
    {
      label: "Cobertura Int.",
      target: ">1.5x",
      value: findKpiValue(end.kpis, "Cobertura de Intereses") || "-",
      dot: getDotColor(end.kpis, "Cobertura de Intereses"),
    },
  ];

  const rawRotInv = rot.kpis?.find((k) =>
    k.label.toLowerCase().includes("inventarios")
  );

  const rotInvValue =
    !rawRotInv || rawRotInv.value === "N/A"
      ? "N/A"
      : findKpiValue(rot.kpis, "Inventarios") || "-";

  cards.value[3].items = [
    {
      label: "Rot. Inventario",
      target: ">4.0x",
      value: rotInvValue,
      dot: getDotColor(rot.kpis, "Inventarios"),
      nota: findKpiNota(rot.kpis, "Inventarios"),
    },
    {
      label: "Periodo Cobro",
      target: "<60 días",
      value: findKpiValue(rot.kpis, "Recaudo") || "-",
      dot: getDotColor(rot.kpis, "Recaudo"),
    },
  ];

  cards.value[4].items = [
    {
      label: "Solvencia",
      target: ">1.0",
      value: findKpiValue(est.kpis, "Solvencia General") || "-",
      dot: getDotColor(est.kpis, "Solvencia General"),
    },
    {
      label: "Seguridad LP",
      target: ">=1.0",
      value: findKpiValue(est.kpis, "Seguridad a largo plazo") || "-",
      dot: getDotColor(est.kpis, "Seguridad a largo plazo"),
    },
  ];

  const calcPct = (val, total) =>
    total ? `${((val / total) * 100).toFixed(1)}%` : "0%";

  const gastos = ventas - costo - utOperacion;
  const impuestos = utOperacion - utNeta;

  estructuraResultado.value = {
    period: data.periodo || "Periodo actual",
    rows: [
      {
        concept: "Ingresos",
        value: currencyFmt.format(ventas),
        pct: "100%",
        tone: "income",
      },
      {
        concept: "Costos",
        value: `(${currencyFmt.format(costo)})`,
        pct: calcPct(costo, ventas),
        tone: "negative",
      },
      {
        concept: "Gastos",
        value: `(${currencyFmt.format(gastos > 0 ? gastos : 0)})`,
        pct: calcPct(gastos > 0 ? gastos : 0, ventas),
        tone: "negative",
      },
      {
        concept: "Impuestos y Otros",
        value: `(${currencyFmt.format(impuestos > 0 ? impuestos : 0)})`,
        pct: calcPct(impuestos > 0 ? impuestos : 0, ventas),
        tone: "negative",
      },
      {
        concept: "Total (Utilidad Neta)",
        value: currencyFmt.format(utNeta),
        pct: calcPct(utNeta, ventas),
        tone: "total",
      },
    ],
  };

  interpretation.value =
    utNeta > 0
      ? "La empresa genera utilidades netas positivas."
      : "La empresa reporta pérdidas o faltan datos.";
};

// ===== FUNCIONES AUXILIARES =====
const findKpiValue = (list, labelPart) => {
  if (!list) return null;

  const item = list.find((k) =>
    k.label.toLowerCase().includes(labelPart.toLowerCase())
  );

  return item ? item.value : null;
};

const getDotColor = (list, labelPart) => {
  if (!list) return "gray";

  const item = list.find((k) =>
    k.label.toLowerCase().includes(labelPart.toLowerCase())
  );

  if (!item) return "gray";

  if (item.status === "danger" || item.status === "alert") return "alert";

  return item.status === "ok" ? "ok" : "warn";
};

const isStatusOk = (list, labelPart) => {
  return getDotColor(list, labelPart) === "ok";
};

function goDetail(routeName) {
  if (!projectId.value) return;
  router.push({ name: routeName, params: { id_proyecto: projectId.value } });
}

function goToIncomeStatementDetail() {
  if (resultadosPdfUrl.value) {
    window.open(resultadosPdfUrl.value, "_blank");
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
      </article>
    </section>

    <!-- Info -->
    <div class="info">
      <span class="material-symbols-outlined">info</span>
      <p>
        Para visualizar gráficas de evolución y comparativas detalladas, añade más periodos a tu análisis.
      </p>
    </div>

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
              <p v-if="it.nota" class="metric-nota">{{ it.nota }}</p>
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
          <span class="material-symbols-outlined" aria-hidden="true">receipt_long</span>
          <h4>Resumen del Resultado</h4>
        </div>
        <span class="result-pill">{{ estructuraResultado.period }}</span>
      </div>

      <div class="result-wrap">
        <div class="result-header-row result-grid">
          <div>Concepto</div>
          <div class="center">Valor</div>
          <div class="right">% Ventas</div>
        </div>

        <div
          v-for="row in estructuraResultado.rows"
          :key="row.concept"
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
        <button class="result-link" type="button" @click="goToIncomeStatementDetail">
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
            <h4 class="ai-section-title">Alertas relevantes</h4>

            <div
              v-for="(alert, idx) in aiAlerts"
              :key="`alert-${idx}`"
              class="ai-alert"
              :class="`severity-${alert.severityKey}`"
            >
              <p v-if="alert.block_name" class="ai-block-name">
                {{ alert.block_name }}
              </p>

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
          <h3>Recomendaciones generales</h3>
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
  transition: box-shadow 0.15s ease;
}

.kpi-card:hover {
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.08);
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
  font-size: 22px;
  font-weight: 900;
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

.metric-nota {
  margin: 0;
  font-size: 10px;
  font-weight: 500;
  color: #94a3b8;
  font-style: italic;
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

/* ===== Resultado ===== */
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

.result-pill {
  font-size: 12px;
  font-weight: 900;
  color: #507c95;
  background: #f3f4f6;
  border-radius: 10px;
  padding: 8px 14px;
  white-space: nowrap;
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
  align-items: start;
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

.ai-block-name {
  margin: 0 0 6px;
  color: #299de0;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
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
  position: relative;
  z-index: 1;
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

/* ===== Info + footer ===== */
.info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
}

.info span {
  color: #299de0;
}

.info p {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: #299de0;
}

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

  .cards-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>