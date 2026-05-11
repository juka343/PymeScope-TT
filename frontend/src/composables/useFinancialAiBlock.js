import { ref, computed } from "vue";
import { useRoute } from "vue-router";
import { doc, getDoc } from "firebase/firestore";
import { db } from "@/firebase/config";

export function useFinancialAiBlock(blockKey, options = {}) {
  const route = useRoute();
  const projectId = computed(() => route.params.id_proyecto || null);

  const aiResult = ref(null);
  const aiBlockLoading = ref(false);
  const aiBlockError = ref(null);
  const loadedAnalysisMode = ref(null);
  const loadedDocId = ref(null);

  const AI_COLLECTION = "ai_analysis";

  const DOC_IDS = {
    mono: "resumen_monoperiodo_latest",
    multi: "resumen_multiperiodo_latest",
  };

  const BLOCK_LABELS = {
    rentabilidad: "Rentabilidad",
    liquidez: "Liquidez",
    endeudamiento: "Endeudamiento",
    rotacion: "Rotación de activos",
    estructura: "Estructura financiera",
  };

  const normalizeBlockKey = (value) => {
    if (value === null || value === undefined) return "";

    return String(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  };

  const normalizedBlockKey = computed(() => normalizeBlockKey(blockKey));

  const routeAnalysisMode = computed(() => {
    if (options.analysisMode === "mono" || options.analysisMode === "multi") {
      return options.analysisMode;
    }

    const path = String(route.path || "");
    const name = String(route.name || "");

    if (path.includes("/dashboard-multi") || name.toLowerCase().includes("multi")) {
      return "multi";
    }

    return "mono";
  });

  const getDocSearchOrder = () => {
    if (options.docId) return [options.docId];

    const preferredMode = routeAnalysisMode.value;
    const fallbackMode = preferredMode === "multi" ? "mono" : "multi";

    return [DOC_IDS[preferredMode], DOC_IDS[fallbackMode]];
  };

  const loadAiResult = async () => {
    try {
      aiBlockLoading.value = true;
      aiBlockError.value = null;
      aiResult.value = null;
      loadedAnalysisMode.value = null;
      loadedDocId.value = null;

      if (!projectId.value) return;

      const docIds = getDocSearchOrder();

      for (const docId of docIds) {
        const refDoc = doc(
          db,
          "proyectos",
          projectId.value,
          AI_COLLECTION,
          docId
        );

        const snap = await getDoc(refDoc);

        if (!snap.exists()) continue;

        const data = snap.data();
        const result = data?.result || null;

        if (!result) continue;

        aiResult.value = result;
        loadedDocId.value = docId;
        loadedAnalysisMode.value =
          data?.analysisMode ||
          (docId === DOC_IDS.multi ? "multiperiodo" : "monoperiodo");

        return;
      }

      aiResult.value = null;
    } catch (error) {
      console.error("Error leyendo análisis IA desde Firestore:", error);
      aiBlockError.value = error.message || "Error leyendo análisis IA";
      aiResult.value = null;
    } finally {
      aiBlockLoading.value = false;
    }
  };

  // =====================
  // HELPERS DE LIMPIEZA
  // =====================
  const cleanAiText = (text) => {
    if (text === null || text === undefined) return "";

    return String(text)
      .replace(/\bok\b/gi, "nivel saludable")
      .replace(/\bwarn\b/gi, "nivel de atención")
      .replace(/\bdanger\b/gi, "riesgo elevado")
      .replace(/\bstatus\b/gi, "estado")
      .trim();
  };

  const cleanAiArray = (items) => {
    if (!Array.isArray(items)) return [];

    return items
      .map((item) => cleanAiText(item))
      .filter(Boolean);
  };

  const normalizeSeverityKey = (value) => {
    const text = cleanAiText(value).toLowerCase();

    if (text.includes("alta")) return "alta";
    if (text.includes("baja")) return "baja";

    return "media";
  };

  const sameBlock = (item) => {
    return normalizeBlockKey(item?.block_key) === normalizedBlockKey.value;
  };

  const blockDisplayName = computed(() => {
    return BLOCK_LABELS[normalizedBlockKey.value] || cleanAiText(blockKey);
  });

  // =====================
  // INTERPRETACIÓN DEL BLOQUE
  // Compatible con:
  // Formato viejo:
  // { block_key, block_name, status, interpretation, main_findings }
  //
  // Formato nuevo:
  // { block_key, title, paragraphs, indicators_explained }
  // =====================
  const blockInterpretation = computed(() => {
    const list = Array.isArray(aiResult.value?.block_interpretations)
      ? aiResult.value.block_interpretations
      : [];

    return list.find((item) => sameBlock(item)) || null;
  });

  const interpretationTitle = computed(() => {
    const block = blockInterpretation.value;

    return cleanAiText(
      block?.title ||
        block?.block_name ||
        blockDisplayName.value
    );
  });

  const interpretationParagraphs = computed(() => {
    const block = blockInterpretation.value;

    if (!block) return [];

    if (Array.isArray(block.paragraphs) && block.paragraphs.length > 0) {
      return cleanAiArray(block.paragraphs);
    }

    if (block.interpretation) {
      return [cleanAiText(block.interpretation)];
    }

    return [];
  });

  const interpretationText = computed(() => {
    return interpretationParagraphs.value.join("\n\n");
  });

  const indicatorsExplained = computed(() => {
    const block = blockInterpretation.value;

    if (!Array.isArray(block?.indicators_explained)) return [];

    return block.indicators_explained.map((item) => ({
      label: cleanAiText(item?.label || ""),
      value: cleanAiText(item?.value || ""),
      reading: cleanAiText(item?.reading || ""),
      meaning: cleanAiText(item?.meaning || ""),
      serviceBusinessImplication: cleanAiText(
        item?.service_business_implication || ""
      ),
      possibleImpact: cleanAiText(item?.possible_impact || ""),
    }));
  });

  const mainFindings = computed(() => {
    const block = blockInterpretation.value;

    if (!block) return [];

    if (Array.isArray(block.main_findings) && block.main_findings.length > 0) {
      return cleanAiArray(block.main_findings);
    }

    if (indicatorsExplained.value.length > 0) {
      return indicatorsExplained.value.map((item) => {
        const parts = [];

        if (item.label) parts.push(item.label);
        if (item.value) parts.push(item.value);
        if (item.reading) parts.push(item.reading);
        if (item.meaning) parts.push(item.meaning);
        if (item.serviceBusinessImplication) {
          parts.push(item.serviceBusinessImplication);
        }
        if (item.possibleImpact) parts.push(item.possibleImpact);

        return parts.join(" · ");
      });
    }

    return [];
  });

  // =====================
  // ALERTAS DEL BLOQUE
  // Compatible con:
  // - result.alerts filtrado por block_key
  // - result.alerts_by_block filtrado por block_key
  // =====================
  const blockAlerts = computed(() => {
    const alertsByBlock = Array.isArray(aiResult.value?.alerts_by_block)
      ? aiResult.value.alerts_by_block.filter((item) => sameBlock(item))
      : [];

    if (alertsByBlock.length > 0) return alertsByBlock;

    return Array.isArray(aiResult.value?.alerts)
      ? aiResult.value.alerts.filter((item) => sameBlock(item))
      : [];
  });

  const alertItems = computed(() => {
    return blockAlerts.value.map((item) => {
      const severity = cleanAiText(item?.severity || "media");

      return {
        title: cleanAiText(item?.title || "Alerta relevante"),
        message: cleanAiText(item?.message || ""),
        severity,
        severityKey: normalizeSeverityKey(severity),
        evidence: cleanAiText(item?.evidence || ""),
        implication: cleanAiText(item?.implication || ""),
        blockKey: normalizeBlockKey(item?.block_key || blockKey),
        blockName: BLOCK_LABELS[normalizeBlockKey(item?.block_key || blockKey)] || blockDisplayName.value,
      };
    });
  });

  // =====================
  // RECOMENDACIONES DEL BLOQUE
  // Compatible con:
  // - result.recommendations filtrado por block_key
  // - result.recommendations_by_block con arreglo interno recommendations
  // =====================
  const blockRecommendationGroup = computed(() => {
    const grouped = Array.isArray(aiResult.value?.recommendations_by_block)
      ? aiResult.value.recommendations_by_block.find((item) => sameBlock(item))
      : null;

    return grouped || null;
  });

  const blockRecommendations = computed(() => {
    const grouped = blockRecommendationGroup.value;

    if (Array.isArray(grouped?.recommendations) && grouped.recommendations.length > 0) {
      return grouped.recommendations.map((item) => ({
        ...item,
        block_key: blockKey,
      }));
    }

    return Array.isArray(aiResult.value?.recommendations)
      ? aiResult.value.recommendations.filter((item) => sameBlock(item))
      : [];
  });

  const recommendationGroupTitle = computed(() => {
    const grouped = blockRecommendationGroup.value;

    return cleanAiText(
      grouped?.title ||
        BLOCK_LABELS[normalizeBlockKey(grouped?.block_key)] ||
        blockDisplayName.value
    );
  });

  const recommendationItems = computed(() => {
    return blockRecommendations.value.map((item) => ({
      title: cleanAiText(item?.title || "Recomendación"),
      description: cleanAiText(item?.description || item?.message || ""),
      priority: cleanAiText(item?.priority || "media"),
      reason: cleanAiText(item?.reason || ""),
      expectedImpact: cleanAiText(
        item?.expected_impact || item?.expectedImpact || ""
      ),
      blockKey: normalizeBlockKey(item?.block_key || blockKey),
      blockName: blockDisplayName.value,
    }));
  });

  // =====================
  // RESUMEN ÚTIL PARA UI
  // =====================
  const hasAiResult = computed(() => Boolean(aiResult.value));

  const hasBlockData = computed(() => {
    return Boolean(
      blockInterpretation.value ||
        blockAlerts.value.length > 0 ||
        blockRecommendations.value.length > 0
    );
  });

  const hasInterpretation = computed(() => {
    return interpretationParagraphs.value.length > 0;
  });

  const hasAlerts = computed(() => {
    return alertItems.value.length > 0;
  });

  const hasRecommendations = computed(() => {
    return recommendationItems.value.length > 0;
  });

  const isAiPending = computed(() => {
    return aiBlockLoading.value || (!aiResult.value && !aiBlockError.value);
  });

  return {
    aiResult,
    aiBlockLoading: isAiPending,
    aiBlockError,
    loadAiResult,

    loadedAnalysisMode,
    loadedDocId,

    hasAiResult,
    hasBlockData,
    hasInterpretation,
    hasAlerts,
    hasRecommendations,

    blockInterpretation,
    interpretationTitle,
    interpretationParagraphs,
    interpretationText,
    indicatorsExplained,
    mainFindings,

    blockAlerts,
    alertItems,

    blockRecommendationGroup,
    recommendationGroupTitle,
    blockRecommendations,
    recommendationItems,
  };
}