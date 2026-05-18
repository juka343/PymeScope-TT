<script setup>
import { computed, onMounted, ref, nextTick } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useConfirm } from "@/composables/useConfirm";
import { useToast } from "@/composables/useToast";

import { db, storage, auth } from "@/firebase/config";
import {
  doc,
  getDoc,
  setDoc,
  updateDoc,
  getDocs,
  deleteDoc,
  collection,
  serverTimestamp,
} from "firebase/firestore";
import {
  ref as storageRef,
  uploadBytes,
  getDownloadURL,
  deleteObject,
} from "firebase/storage";

const route = useRoute();
const router = useRouter();
const projectId = route.params.id_proyecto;
const { confirm } = useConfirm();
const { toast } = useToast();

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api";

// Datos del proyecto
const projectTitle = ref("Cargando...");
const periodicity = ref("...");
const isLoadingProject = ref(true);
const projectStatus = ref("");
const projectAnalysisMode = ref("");

// Periodos
const periods = ref([]);
const isUploading = ref(false);
const isProcessing = ref(false);

// refs inputs ocultos
const fileInputRefs = ref({});
const setInputRef = (el, periodId, type) => {
  if (el) fileInputRefs.value[`${periodId}_${type}`] = el;
};

// =====================
// EDICIÓN DE NOMBRES
// =====================
const isEditingProjectName = ref(false);
const editProjectNameInput = ref("");

async function iniciarEdicionProyecto() {
  isEditingProjectName.value = true;
  editProjectNameInput.value = projectTitle.value;
  await nextTick();
  const inputEl = document.getElementById(`edit-project-input`);
  if (inputEl) inputEl.focus();
}

function cancelarEdicionProyecto() {
  isEditingProjectName.value = false;
  editProjectNameInput.value = "";
}

async function guardarNombreProyecto() {
  if (!editProjectNameInput.value.trim()) return;
  try {
    const projectRef = doc(db, "proyectos", projectId);
    await updateDoc(projectRef, {
      nombre: editProjectNameInput.value.trim()
    });
    projectTitle.value = editProjectNameInput.value.trim();
    isEditingProjectName.value = false;
  } catch (error) {
    console.error("Error al actualizar nombre del proyecto:", error);
    toast({ message: "Hubo un error al guardar el nombre.", type: "error" });
  }
}

const editingPeriodId = ref(null);
const editPeriodNameInput = ref("");

async function iniciarEdicionPeriodo(p) {
  editingPeriodId.value = p.id;
  editPeriodNameInput.value = p.label;
  await nextTick();
  const inputEl = document.getElementById(`edit-period-input-${p.id}`);
  if (inputEl) inputEl.focus();
}

function cancelarEdicionPeriodo() {
  editingPeriodId.value = null;
  editPeriodNameInput.value = "";
}

async function guardarNombrePeriodo(p) {
  if (!editPeriodNameInput.value.trim()) return;
  p.label = editPeriodNameInput.value.trim();
  p.hasChanges = true;
  p.hasAnalysis = false;
  await savePeriodToFirestore(p);
  editingPeriodId.value = null;
}

// =====================
// NAVEGACIÓN AL RESUMEN
// =====================
const completePeriods = computed(() =>
  periods.value.filter((p) => p.balanceFile && p.resultsFile)
);

const isMultiPeriod = computed(() => periods.value.length > 1);

const periodsToProcess = computed(() =>
  completePeriods.value.filter((p) => p.hasChanges || !p.hasAnalysis)
);

const canGenerate = computed(() => 
  periods.value.length > 0 && periods.value.every((p) => p.balanceFile && p.resultsFile)
);

const hasMissingDates = computed(() => {
  return (
    isMultiPeriod.value &&
    periods.value.some((p) => {
      if (periodicity.value === "anual") {
        return !p.periodDate || String(p.periodDate).length < 4;
      }

      return !p.periodDate || String(p.periodDate).length < 6;
    })
  );
});

function getModeFromCurrentPeriods() {
  return periods.value.length > 1 ? "multi" : "mono";
}

function getSummaryRouteName(mode = getModeFromCurrentPeriods()) {
  return mode === "multi" ? "resumenMulti" : "resumen";
}

function getSummaryPath(mode = getModeFromCurrentPeriods()) {
  return mode === "multi"
    ? `/proyecto/${projectId}/dashboard-multi/resumen`
    : `/proyecto/${projectId}/dashboard/resumen`;
}

async function goToSummary(mode = getModeFromCurrentPeriods(), replace = false) {
  const routeName = getSummaryRouteName(mode);

  try {
    const navigation = {
      name: routeName,
      params: { id_proyecto: projectId },
    };

    if (replace) {
      await router.replace(navigation);
    } else {
      await router.push(navigation);
    }
  } catch (error) {
    const path = getSummaryPath(mode);

    if (replace) {
      router.replace(path);
    } else {
      router.push(path);
    }
  }
}

function goToExistingAnalysis() {
  const mode = projectAnalysisMode.value || getModeFromCurrentPeriods();
  goToSummary(mode, false);
}

const generateButtonText = computed(() => {
  if (isUploading.value) return "Subiendo a Firebase...";
  if (isProcessing.value) return "Analizando con IA...";

  if (periodsToProcess.value.length === 0 && completePeriods.value.length > 0) {
    return "Ver análisis";
  }

  return "Generar análisis";
});

// =====================
// FECHAS
// =====================
const currentYear = new Date().getFullYear();

const availableYears = computed(() => {
  const years = [];
  for (let y = currentYear; y >= 2002; y--) {
    years.push(y);
  }
  return years;
});

const availableMonths = [
  { value: "01", label: "Enero" },
  { value: "02", label: "Febrero" },
  { value: "03", label: "Marzo" },
  { value: "04", label: "Abril" },
  { value: "05", label: "Mayo" },
  { value: "06", label: "Junio" },
  { value: "07", label: "Julio" },
  { value: "08", label: "Agosto" },
  { value: "09", label: "Septiembre" },
  { value: "10", label: "Octubre" },
  { value: "11", label: "Noviembre" },
  { value: "12", label: "Diciembre" },
];

const openDropdown = ref(null);

function toggleDropdown(id) {
  openDropdown.value = openDropdown.value === id ? null : id;
}

function getMonthLabel(periodDate) {
  if (!periodDate) return "Mes";

  const parts = String(periodDate).split("-");
  const month = parts[1] || "";
  const found = availableMonths.find((x) => x.value === month);

  return found ? found.label : "Mes";
}

function getYearLabel(periodDate) {
  if (!periodDate) return "Año";

  const parts = String(periodDate).split("-");
  return parts[0] || "Año";
}

function updatePeriodDate(p, type, value) {
  const safeDate = p.periodDate ? String(p.periodDate) : "";
  const parts = safeDate.split("-");

  let year = parts[0] || "";
  let month = parts[1] || "";

  if (type === "year") year = String(value);
  if (type === "month") month = String(value);

  if (periodicity.value === "anual") {
    p.periodDate = year;
  } else {
    p.periodDate = `${year}-${month}`;
  }

  handleDateChange(p);
}

function handleDateChange(p) {
  const safeDate = p.periodDate ? String(p.periodDate) : "";

  if (periodicity.value === "anual") {
    if (safeDate.length === 4) {
      p.label = `Ejercicio ${safeDate}`;
    }
  } else {
    if (safeDate.length >= 6) {
      const [year, month] = safeDate.split("-");

      if (year && month) {
        const meses = [
          "Enero",
          "Febrero",
          "Marzo",
          "Abril",
          "Mayo",
          "Junio",
          "Julio",
          "Agosto",
          "Septiembre",
          "Octubre",
          "Noviembre",
          "Diciembre",
        ];

        p.label = `${meses[parseInt(month, 10) - 1]} ${year}`;
      }
    }
  }

  p.hasChanges = true;
  p.hasAnalysis = false;

  savePeriodToFirestore(p);
}

// =====================
// PROYECTO
// =====================
async function updateProjectAnalysisMode(extraData = {}) {
  const projectRef = doc(db, "proyectos", projectId);
  const mode = isMultiPeriod.value ? "multi" : "mono";

  await setDoc(
    projectRef,
    {
      analysis_mode: mode,
      periods_count: periods.value.length,
      updatedAt: serverTimestamp(),
      ...extraData,
    },
    { merge: true }
  );

  projectAnalysisMode.value = mode;

  if (extraData.status) {
    projectStatus.value = extraData.status;
  }
}

async function markProjectPending() {
  await updateProjectAnalysisMode({ status: "pendiente" });
}

// =====================
// CARGA INICIAL
// =====================
onMounted(async () => {
  if (!projectId) {
    toast({
      message: "No se encontró el ID del proyecto en la URL.",
      type: "error",
    });
    return;
  }

  try {
    const docRef = doc(db, "proyectos", projectId);
    const docSnap = await getDoc(docRef);

    if (docSnap.exists()) {
      const data = docSnap.data();

      projectTitle.value = data.nombre || "Sin Título";
      periodicity.value = data.periodicidad || "Desconocida";
      projectStatus.value = data.status || "";
      projectAnalysisMode.value = data.analysis_mode || "";

      await loadExistingPeriods();

      if (periods.value.length === 0) addPeriod();
    } else {
      projectTitle.value = "Proyecto no encontrado";
    }
  } catch (error) {
    console.error("Error cargando proyecto:", error);
    projectTitle.value = "Error de conexión";
  } finally {
    isLoadingProject.value = false;
  }
});

// =====================
// FIRESTORE PERIODOS
// =====================
async function loadExistingPeriods() {
  try {
    const periodosRef = collection(db, "proyectos", projectId, "periodos");
    const snapshot = await getDocs(periodosRef);

    if (snapshot.empty) return;

    const loaded = [];

    snapshot.forEach((docSnap) => {
      const data = docSnap.data();

      loaded.push({
        id: docSnap.id,
        label: data.label || "Periodo",
        periodDate: data.periodDate || "",
        balanceFile: data.balanceFile || null,
        resultsFile: data.resultsFile || null,
        hasAnalysis: Boolean(
          data.analisis_rentabilidad ||
            data.analisis_liquidez ||
            data.analisis_endeudamiento ||
            data.analisis_rotacion ||
            data.analisis_estructura
        ),
        hasChanges: false,
      });
    });

    loaded.sort((a, b) => {
      const dateA = a.periodDate || "";
      const dateB = b.periodDate || "";
      return dateA.localeCompare(dateB);
    });

    periods.value = loaded;

    await updateProjectAnalysisMode();
  } catch (error) {
    console.error("Error cargando periodos:", error);
  }
}

function addPeriod() {
  const next = periods.value.length + 1;

  const newPeriod = {
    id: crypto.randomUUID(),
    label: `Periodo ${next}`,
    periodDate: "",
    balanceFile: null,
    resultsFile: null,
    hasChanges: false,
    hasAnalysis: false,
  };

  periods.value.push(newPeriod);
  savePeriodToFirestore(newPeriod);
}

async function savePeriodToFirestore(period) {
  try {
    const periodRef = doc(db, "proyectos", projectId, "periodos", period.id);

    await setDoc(
      periodRef,
      {
        label: period.label,
        periodDate: period.periodDate,
        balanceFile: period.balanceFile,
        resultsFile: period.resultsFile,
        updatedAt: serverTimestamp(),
      },
      { merge: true }
    );

    await updateProjectAnalysisMode();
  } catch (error) {
    console.error("Error guardando periodo:", error);
  }
}

// =====================
// UPLOAD / DELETE
// =====================
function triggerFileInput(periodId, type) {
  const input = fileInputRefs.value[`${periodId}_${type}`];
  if (input) input.click();
}

async function handleFileChange(event, periodId, type) {
  const file = event.target.files?.[0];
  if (!file) return;

  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    toast({
      message: "Por favor sube solo archivos PDF.",
      type: "error",
    });
    event.target.value = null;
    return;
  }

  isUploading.value = true;

  try {
    const currentUser = auth.currentUser;
    if (!currentUser) throw new Error("Sesión no iniciada");

    const userId = currentUser.uid;
    const fileUuid = crypto.randomUUID();

    const path = `uploads/${userId}/${projectId}/${periodId}/${type}_${fileUuid}.pdf`;
    const fileRef = storageRef(storage, path);

    await uploadBytes(fileRef, file);
    const downloadURL = await getDownloadURL(fileRef);

    const p = periods.value.find((x) => x.id === periodId);

    if (p) {
      const meta = {
        uuid: fileUuid,
        name: file.name,
        url: downloadURL,
        path,
        type,
      };

      if (type === "balance") p.balanceFile = meta;
      if (type === "resultado") p.resultsFile = meta;

      p.hasChanges = true;
      p.hasAnalysis = false;

      await savePeriodToFirestore(p);
      await markProjectPending();
    }
  } catch (error) {
    console.error("Error subiendo:", error);

    toast({
      message: "Error al subir a Firebase.",
      type: "error",
    });
  } finally {
    isUploading.value = false;
    event.target.value = null;
  }
}

async function removeDocument(periodId, type) {
  const p = periods.value.find((x) => x.id === periodId);
  if (!p) return;

  const fileData = type === "balance" ? p.balanceFile : p.resultsFile;
  if (!fileData) return;

  const confirmed = await confirm({
    title: `Eliminar ${fileData.name}`,
    message: "¿Estás seguro de eliminar este archivo?",
    confirmText: "Sí, eliminar",
    variant: "danger",
  });

  if (!confirmed) return;

  isUploading.value = true;

  try {
    await deleteObject(storageRef(storage, fileData.path));

    if (type === "balance") p.balanceFile = null;
    if (type === "resultado") p.resultsFile = null;

    p.hasChanges = true;
    p.hasAnalysis = false;

    await savePeriodToFirestore(p);
    await markProjectPending();
  } catch (error) {
    console.error("Error eliminando archivo:", error);
  } finally {
    isUploading.value = false;
  }
}

async function removePeriod(periodId) {
  const p = periods.value.find((x) => x.id === periodId);
  if (!p) return;

  const confirmed = await confirm({
    title: `Eliminar ${p.label}`,
    message: "¿Estás seguro de eliminar este periodo y sus archivos?",
    confirmText: "Sí, eliminar",
    variant: "danger",
  });

  if (!confirmed) return;

  isUploading.value = true;

  try {
    if (p.balanceFile) {
      await deleteObject(storageRef(storage, p.balanceFile.path)).catch(() => {});
    }

    if (p.resultsFile) {
      await deleteObject(storageRef(storage, p.resultsFile.path)).catch(() => {});
    }

    await deleteDoc(doc(db, "proyectos", projectId, "periodos", periodId));

    periods.value = periods.value.filter((period) => period.id !== periodId);

    for (let i = 0; i < periods.value.length; i++) {
      const current = periods.value[i];
      const isGenericName = /^Periodo \d+$/.test(current.label);

      if (isGenericName) {
        current.label = `Periodo ${i + 1}`;
      }

      await savePeriodToFirestore(current);
    }

    await updateProjectAnalysisMode({
      status:
        canGenerate.value && periodsToProcess.value.length === 0
          ? "completo"
          : "pendiente",
    });
  } catch (error) {
    console.error("Error:", error);
  } finally {
    isUploading.value = false;
  }
}

// =====================
// ANÁLISIS
// =====================
function getColIndex(period) {
  let indiceColumna = 0;

  if (periodicity.value === "mensual" && period.periodDate) {
    const dateStr = String(period.periodDate).toLowerCase();

    if (dateStr.includes("-")) {
      const parts = dateStr.split("-");

      if (parts.length > 1) {
        indiceColumna = parseInt(parts[1], 10) - 1;
      }
    } else {
      const meses = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
      ];

      const indexEncontrado = meses.findIndex((m) => dateStr.includes(m));

      if (indexEncontrado !== -1) {
        indiceColumna = indexEncontrado;
      }
    }
  }

  if (Number.isNaN(indiceColumna) || indiceColumna < 0) return 0;

  return indiceColumna;
}

async function analyzePeriod(period) {
  const payload = {
    project_id: projectId,
    period_id: period.id,
    balance_url: period.balanceFile.url,
    resultados_url: period.resultsFile.url,
    periodicidad: periodicity.value,
    col_index: getColIndex(period),
    period_date: period.periodDate,
    period_label: period.label,
  };

  const response = await fetch(`${API_BASE_URL}/documents/analyze-period`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || "Error procesando un periodo.");
  }

  if (data?.estatus !== "Completado") {
    throw new Error("El backend no devolvió un análisis completado.");
  }

  return data;
}

async function saveAnalysisResult(res) {
  const periodoRef = doc(db, "proyectos", projectId, "periodos", res.period_id);

  await setDoc(
    periodoRef,
    {
      analisis_rentabilidad: res.dashboard_data.rentabilidad,
      analisis_liquidez: res.dashboard_data.liquidez,
      analisis_endeudamiento: res.dashboard_data.endeudamiento,
      analisis_rotacion: res.dashboard_data.rotacion,
      analisis_estructura: res.dashboard_data.estructura,
      analyzedAt: serverTimestamp(),
    },
    { merge: true }
  );

  const pLocal = periods.value.find((p) => p.id === res.period_id);

  if (pLocal) {
    pLocal.hasChanges = false;
    pLocal.hasAnalysis = true;
  }
}

async function generateAnalysis() {
  if (completePeriods.value.length === 0) {
    toast({
      message: "Carga al menos un Balance General y un Estado de Resultados.",
      type: "warning",
    });
    return;
  }

  if (hasMissingDates.value) {
    toast({
      message: "Faltan fechas en algunos periodos para el análisis multiperiodo.",
      type: "warning",
    });
    return;
  }

  isProcessing.value = true;

  try {
    const mode = getModeFromCurrentPeriods();
    const aProcesar = periodsToProcess.value;

    if (aProcesar.length === 0) {
      await goToSummary(mode, false);
      return;
    }

    const resultados = await Promise.all(aProcesar.map((p) => analyzePeriod(p)));

    for (const res of resultados) {
      console.log("Rentabilidad:", res.dashboard_data.rentabilidad?.datos_crudos);
      console.log("Liquidez:", res.dashboard_data.liquidez?.datos_crudos);
      console.log("Endeudamiento:", res.dashboard_data.endeudamiento?.datos_crudos);
      console.log("Rotación:", res.dashboard_data.rotacion?.datos_crudos);
      console.log("Estructura:", res.dashboard_data.estructura?.datos_crudos);

      await saveAnalysisResult(res);
    }

    const finalMode = getModeFromCurrentPeriods();

    const projectRef = doc(db, "proyectos", projectId);

    await setDoc(
      projectRef,
      {
        status: "completo",
        analysis_mode: finalMode,
        periods_count: periods.value.length,
        updatedAt: serverTimestamp(),
      },
      { merge: true }
    );

    projectStatus.value = "completo";
    projectAnalysisMode.value = finalMode;

    await goToSummary(finalMode, true);
  } catch (error) {
    console.error("Error en el análisis:", error);

    if (error.message && error.message.includes("DATE_MISMATCH")) {
      const match = error.message.match(/DATE_MISMATCH\|([^|]+)\|([^|]+)\|([^|]+)/);
      const docType = match ? match[1] : "documento";
      const expectedDate = match ? match[2] : "la fecha indicada";
      const periodLabel = match ? match[3] : "el periodo";
      
      await confirm({
        title: "Fechas no coinciden",
        message: "No se pudo validar la fecha ingresada con la fecha del archivo, por favor, valida que la fecha ingresada coincida con la de ambos documentos.",
        confirmText: "Entendido",
        cancelText: "",
        variant: "warning",
      });
      return;
    }

    toast({
      message: error.message || "Hubo un error procesando los documentos.",
      type: "error",
    });
  } finally {
    isProcessing.value = false;
  }
}
</script>

<template>
  <div class="page">
    <!-- Overlay de Carga -->
    <div v-if="isProcessing" class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <h3>Generando Análisis Financiero...</h3>
        <p>Procesando documentos y ejecutando algoritmos de IA.</p>
      </div>
    </div>

    <header class="header">
      <div class="header-inner">
        <RouterLink to="/misProyectos" class="brand">
            <img src="/logo.png" alt="Logo PymeScope" class="brand-icon" />

          <h2 class="brand-name">PymeScope</h2>
        </RouterLink>

        <div class="project-meta">
          <div v-if="isEditingProjectName" class="edit-name-wrap" style="margin-bottom: 0;">
            <input id="edit-project-input" v-model="editProjectNameInput" class="input input-sm" type="text" @keyup.enter="guardarNombreProyecto" @keyup.esc="cancelarEdicionProyecto" />
            <button class="btn-icon-small btn-icon-ok" @click="guardarNombreProyecto" title="Guardar"><span class="material-symbols-outlined">check</span></button>
            <button class="btn-icon-small btn-icon-cancel" @click="cancelarEdicionProyecto" title="Cancelar"><span class="material-symbols-outlined">close</span></button>
          </div>
          <div v-else class="title-with-edit" style="margin-bottom: 0;">
            <span class="project-title">{{ projectTitle }}</span>
            <button class="btn-icon-small edit-icon-btn" @click="iniciarEdicionProyecto" title="Editar nombre">
              <span class="material-symbols-outlined">edit</span>
            </button>
          </div>
          <span class="pill">Periodicidad: {{ periodicity }}</span>
        </div>

        <div class="actions">
          <RouterLink class="back" to="/misProyectos">
            <span class="material-symbols-outlined">arrow_back</span>
            <span class="back-text">Volver a proyectos</span>
          </RouterLink>

          <button
            v-if="projectStatus === 'completo'"
            class="btn-back-analysis"
            type="button"
            @click="goToExistingAnalysis"
          >
            <span class="material-symbols-outlined">analytics</span>
            <span class="back-text">Volver al análisis</span>
          </button>
        </div>
      </div>
    </header>

    <main class="container main">
      <section class="intro">
        <h1>Carga de documentos financieros</h1>
        <p>Agrega los estados financieros según la periodicidad del análisis.</p>

        <div class="info">
          <span class="material-symbols-outlined">info</span>
          <p>
            Cada periodo requiere un <strong>Balance General</strong> y un
            <strong>Estado de Resultados</strong> para poder generar el análisis completo.
          </p>
        </div>
      </section>

      <section class="periodicity">
        <div class="periodicity-left">
          <span class="material-symbols-outlined">calendar_month</span>
          <p>
            <strong>Periodicidad del análisis: {{ periodicity }}</strong>
            <span class="muted">(Solo lectura)</span>
          </p>
        </div>

        <p class="periodicity-right">
          La periodicidad se define al crear el proyecto y no puede modificarse.
        </p>
      </section>

      <section class="add">
        <button class="btn-primary" type="button" @click="addPeriod">
          <span class="material-symbols-outlined">add</span>
          Añadir periodo
        </button>
      </section>

      <section v-if="periods.length" class="periods">
        <article v-for="p in periods" :key="p.id" class="period-card">
          <header class="period-card-head">
            <div class="head-left">
              <div v-if="editingPeriodId === p.id" class="edit-name-wrap" style="margin-bottom: 0;">
                <input
                  :id="`edit-period-input-${p.id}`"
                  v-model="editPeriodNameInput"
                  class="input input-sm"
                  style="font-weight: 900; width: 140px;"
                  type="text"
                  @keyup.enter="guardarNombrePeriodo(p)"
                  @keyup.esc="cancelarEdicionPeriodo"
                />
                <button class="btn-icon-small btn-icon-ok" @click="guardarNombrePeriodo(p)" title="Guardar"><span class="material-symbols-outlined">check</span></button>
                <button class="btn-icon-small btn-icon-cancel" @click="cancelarEdicionPeriodo" title="Cancelar"><span class="material-symbols-outlined">close</span></button>
              </div>
              <div v-else class="title-with-edit" style="margin-bottom: 0;">
                <span style="font-weight: 900; width: 140px; display: inline-block;">{{ p.label }}</span>
                <button class="btn-icon-small edit-icon-btn" @click="iniciarEdicionPeriodo(p)" title="Editar nombre">
                  <span class="material-symbols-outlined">edit</span>
                </button>
              </div>

              <div class="date-wrapper">
                <div class="date-selects">
                  <div
                    v-if="periodicity !== 'anual'"
                    class="custom-select"
                    tabindex="0"
                    @blur="openDropdown = null"
                  >
                    <div
                      class="selected-value"
                      @click="toggleDropdown(`${p.id}-month`)"
                    >
                      <span>{{ getMonthLabel(p.periodDate) }}</span>
                      <span class="material-symbols-outlined">expand_more</span>
                    </div>

                    <ul
                      v-show="openDropdown === `${p.id}-month`"
                      class="options-list"
                      @mousedown.prevent
                    >
                      <li
                        v-for="m in availableMonths"
                        :key="m.value"
                        @click="updatePeriodDate(p, 'month', m.value); openDropdown = null"
                        :class="{
                          active:
                            p.periodDate &&
                            String(p.periodDate).split('-')[1] === m.value
                        }"
                      >
                        {{ m.label }}
                      </li>
                    </ul>
                  </div>

                  <div
                    class="custom-select"
                    tabindex="0"
                    @blur="openDropdown = null"
                  >
                    <div
                      class="selected-value"
                      @click="toggleDropdown(`${p.id}-year`)"
                    >
                      <span>{{ getYearLabel(p.periodDate) }}</span>
                      <span class="material-symbols-outlined">expand_more</span>
                    </div>

                    <ul
                      v-show="openDropdown === `${p.id}-year`"
                      class="options-list"
                      @mousedown.prevent
                    >
                      <li
                        v-for="y in availableYears"
                        :key="y"
                        @click="updatePeriodDate(p, 'year', y); openDropdown = null"
                        :class="{
                          active:
                            p.periodDate &&
                            String(p.periodDate).split('-')[0] == y
                        }"
                      >
                        {{ y }}
                      </li>
                    </ul>
                  </div>
                </div>

                <span
                  v-if="
                    isMultiPeriod &&
                    (!p.periodDate ||
                      (periodicity === 'anual'
                        ? String(p.periodDate).length < 4
                        : String(p.periodDate).length < 6))
                  "
                  class="required-badge"
                >
                  * Obligatorio
                </span>
              </div>
            </div>

            <button
              class="btn-icon-danger"
              @click="removePeriod(p.id)"
              title="Eliminar periodo completo"
            >
              <span class="material-symbols-outlined">delete</span>
            </button>
          </header>

          <div class="docs">
            <div class="doc">
              <div class="doc-left">
                <span class="material-symbols-outlined">description</span>
                <div>
                  <p class="doc-title">Balance General</p>
                  <p class="doc-sub">
                    <span v-if="p.balanceFile" class="file-success">
                      {{ p.balanceFile.name }}
                      <button
                        class="btn-text-danger"
                        @click="removeDocument(p.id, 'balance')"
                      >
                        (Eliminar)
                      </button>
                    </span>

                    <span v-else class="file-empty">No cargado</span>
                  </p>
                </div>
              </div>

              <input
                type="file"
                hidden
                accept=".pdf"
                :ref="(el) => setInputRef(el, p.id, 'balance')"
                @change="(e) => handleFileChange(e, p.id, 'balance')"
              />

              <button
                class="btn-secondary"
                type="button"
                @click="triggerFileInput(p.id, 'balance')"
                v-if="!p.balanceFile"
              >
                Cargar
              </button>
            </div>

            <div class="doc">
              <div class="doc-left">
                <span class="material-symbols-outlined">receipt_long</span>
                <div>
                  <p class="doc-title">Estado de Resultados</p>
                  <p class="doc-sub">
                    <span v-if="p.resultsFile" class="file-success">
                      {{ p.resultsFile.name }}
                      <button
                        class="btn-text-danger"
                        @click="removeDocument(p.id, 'resultado')"
                      >
                        (Eliminar)
                      </button>
                    </span>

                    <span v-else class="file-empty">No cargado</span>
                  </p>
                </div>
              </div>

              <input
                type="file"
                hidden
                accept=".pdf"
                :ref="(el) => setInputRef(el, p.id, 'resultado')"
                @change="(e) => handleFileChange(e, p.id, 'resultado')"
              />

              <button
                class="btn-secondary"
                type="button"
                @click="triggerFileInput(p.id, 'resultado')"
                v-if="!p.resultsFile"
              >
                Cargar
              </button>
            </div>
          </div>
        </article>
      </section>

      <section v-else class="empty">
        <div class="empty-icon">
          <span class="material-symbols-outlined">folder_open</span>
        </div>
        <h3>No hay periodos añadidos</h3>
        <p>
          Comienza agregando los estados financieros correspondientes a cada periodo.
        </p>
      </section>
    </main>

    <footer class="bottom">
      <div class="container bottom-inner">
        <span v-if="hasMissingDates" class="warning-text">
          Faltan fechas en algunos periodos para el análisis multiperiodo.
        </span>

        <span v-else class="autosave">
          Todos los cambios se guardan automáticamente
        </span>

        <button
          class="btn-generate"
          type="button"
          :disabled="!canGenerate || isUploading || isProcessing || hasMissingDates"
          @click="generateAnalysis"
        >
          <span>{{ generateButtonText }}</span>

          <span
            v-if="!isUploading && !isProcessing"
            class="material-symbols-outlined"
          >
            arrow_forward
          </span>
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.page {
  --primary: #299de0;
  --primary-dark: #1d7cb5;
  --bg: #f8fafb;
  --surface: #ffffff;
  --text: #0e161b;
  --muted: #507c95;
  --border: #e5e7eb;

  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  padding-bottom: 92px;
}

.container {
  width: min(1200px, 92vw);
  margin: 0 auto;
}

/* Header */
.header {
  position: sticky;
  top: 0;
  z-index: 50;
  width: 100%;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.header-inner {
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 160px;
  text-decoration: none;
  color: inherit;
}

.brand-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
  display: block;
}
.logo {
  width: 32px;
  height: 32px;
  color: var(--primary);
  display: grid;
  place-items: center;
}

.brand-name {
  margin: 0;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.project-meta {
  display: none;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
}

.project-title {
  font-size: 13px;
  font-weight: 900;
}

.pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #334155;
  font-size: 12px;
  font-weight: 800;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  min-width: 180px;
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--primary);
  font-weight: 800;
  font-size: 14px;
}

.back:hover {
  color: var(--primary-dark);
}

.back span.material-symbols-outlined {
  font-size: 20px;
}

.back-text {
  display: none;
}

.btn-back-analysis {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  cursor: pointer;
  color: #22c55e;
  font-weight: 800;
  font-size: 14px;
  padding: 0;
}

.btn-back-analysis:hover {
  color: #16a34a;
}

.btn-back-analysis span.material-symbols-outlined {
  font-size: 20px;
}

/* Main */
.main {
  padding: 28px 0 48px;
}

.intro h1 {
  margin: 0 0 8px;
  font-size: 30px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.intro p {
  margin: 0;
  color: var(--muted);
}

.info {
  margin-top: 14px;
  max-width: 620px;
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px 12px;
  border-radius: 12px;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  color: #0b2b52;
}

.info span.material-symbols-outlined {
  color: var(--primary);
  margin-top: 1px;
}

.info p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}

.periodicity {
  margin-top: 18px;
  padding: 14px 14px;
  border-radius: 12px;
  background: #f3f4f6;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.periodicity-left {
  display: flex;
  gap: 10px;
  align-items: center;
}

.periodicity-left span.material-symbols-outlined {
  color: #64748b;
}

.periodicity-left p {
  margin: 0;
  font-size: 13px;
}

.muted {
  color: #64748b;
  font-weight: 600;
}

.periodicity-right {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.add {
  margin-top: 18px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 900;
  font-size: 14px;
  box-shadow: 0 10px 22px rgba(41, 157, 224, 0.22);
  transition: filter 0.15s ease, transform 0.05s ease;
}

.btn-primary:hover {
  filter: brightness(0.95);
}

.btn-primary:active {
  transform: translateY(1px);
}

.btn-primary span.material-symbols-outlined {
  font-size: 20px;
}

.periods {
  margin-top: 18px;
  display: grid;
  gap: 14px;
}

.period-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.05);
}

.period-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.docs {
  display: grid;
  gap: 10px;
}

.doc {
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px;
  background: #fbfdff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.doc-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.doc-left span.material-symbols-outlined {
  color: var(--primary);
}

.doc-title {
  margin: 0;
  font-weight: 900;
  font-size: 13px;
}

.doc-sub {
  margin: 2px 0 0;
  color: #64748b;
  font-size: 12px;
}

.btn-secondary {
  padding: 8px 12px;
  border-radius: 12px;
  background: #e2f2fb;
  color: var(--primary-dark);
  font-weight: 900;
  font-size: 13px;
}

.btn-secondary:hover {
  filter: brightness(0.98);
}

.btn-icon-danger {
  background: transparent;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
}

.btn-icon-danger:hover {
  background: #fee2e2;
}

.file-success {
  color: #16a34a;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.file-empty {
  color: #94a3b8;
  font-style: italic;
}

.btn-text-danger {
  background: none;
  border: none;
  color: #ef4444;
  font-size: 11px;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
  font-weight: 600;
}

.btn-text-danger:hover {
  color: #b91c1c;
}

/* Empty */
.empty {
  margin-top: 28px;
  padding: 56px 18px;
  border: 2px dashed var(--border);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.6);
  display: grid;
  place-items: center;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 999px;
  background: #eff6ff;
  display: grid;
  place-items: center;
  margin-bottom: 10px;
}

.empty-icon span.material-symbols-outlined {
  font-size: 32px;
  color: var(--primary);
}

.empty h3 {
  margin: 0;
  font-weight: 900;
}

.empty p {
  margin: 8px 0 0;
  color: var(--muted);
  max-width: 420px;
}

/* Bottom bar */
.bottom {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background: var(--surface);
  border-top: 1px solid var(--border);
  box-shadow: 0 -4px 10px rgba(0, 0, 0, 0.05);
  z-index: 40;
}

.bottom-inner {
  padding: 14px 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
}

.autosave {
  display: none;
  color: #64748b;
  font-size: 13px;
}

.btn-generate {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 12px;
  font-weight: 900;
  color: white;
  background: var(--primary);
  box-shadow: 0 12px 22px rgba(41, 157, 224, 0.22);
  transition: filter 0.15s ease, transform 0.05s ease, opacity 0.15s ease;
}

.btn-generate:active:enabled {
  transform: translateY(1px);
}

.btn-generate:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  background: #cbd5e1;
  color: #64748b;
}

.btn-generate span.material-symbols-outlined {
  font-size: 20px;
}

/* Inline Edit Styles */
.title-with-edit {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.title-with-edit h3, .title-with-edit .project-title {
  margin: 0;
}

.edit-icon-btn {
  background: transparent;
  border: none;
  color: #9ca3af;
  padding: 2px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: all 0.15s ease;
}

.edit-icon-btn:hover {
  background: #f3f4f6;
  color: #299de0;
}

.edit-icon-btn .material-symbols-outlined {
  font-size: 16px;
}

.edit-name-wrap {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.input-sm {
  padding: 4px 8px;
  font-size: 14px;
  height: 28px;
  width: 150px;
  border: 1px solid #dce2e5;
  border-radius: 6px;
  outline: none;
}
.input-sm:focus {
  border-color: #299de0;
  box-shadow: 0 0 0 2px rgba(41, 157, 224, 0.1);
}

.btn-icon-small {
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.btn-icon-small .material-symbols-outlined {
  font-size: 16px;
  font-weight: 700;
}

.btn-icon-ok {
  color: #059669;
  background: #ecfdf5;
}

.btn-icon-ok:hover {
  background: #d1fae5;
}

.btn-icon-cancel {
  color: #ef4444;
  background: #fef2f2;
}

.btn-icon-cancel:hover {
  background: #fee2e2;
}

.date-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-selects {
  display: flex;
  gap: 8px;
}

.custom-select {
  position: relative;
  outline: none;
}

.selected-value {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  color: #0e161b;
  cursor: pointer;
  min-width: 80px;
  transition: all 0.2s;
}

.selected-value:hover {
  background: #f1f5f9;
}

.custom-select:focus .selected-value {
  border-color: #299de0;
  background: white;
  box-shadow: 0 0 0 2px rgba(41, 157, 224, 0.1);
}

.selected-value span.material-symbols-outlined {
  font-size: 16px;
  color: #94a3b8;
}

.options-list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 100;
  min-width: 100%;
  max-height: 180px;
  overflow-y: auto;
  margin: 0;
  padding: 4px;
  list-style: none;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.options-list li {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
  color: #334155;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}

.options-list li:hover {
  background: #f1f5f9;
}

.options-list li.active {
  background: #e0f2fe;
  color: #0369a1;
  font-weight: 700;
}

.options-list::-webkit-scrollbar {
  width: 6px;
}

.options-list::-webkit-scrollbar-track {
  background: transparent;
}

.options-list::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 10px;
}

.required-badge {
  font-size: 11px;
  font-weight: 800;
  color: #ef4444;
  background: #fee2e2;
  padding: 2px 6px;
  border-radius: 6px;
}

.warning-text {
  color: #ef4444;
  font-size: 13px;
  font-weight: 700;
  display: none;
}

/* Loading Overlay */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: grid;
  place-items: center;
  text-align: center;
}

.loading-content h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 900;
  color: #0e161b;
}

.loading-content p {
  margin: 0;
  font-size: 13px;
  color: #507c95;
  font-weight: 700;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #299de0;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

@media (min-width: 640px) {
  .back-text {
    display: inline;
  }

  .autosave {
    display: inline;
  }

  .warning-text {
    display: inline;
  }
}

@media (min-width: 768px) {
  .project-meta {
    display: flex;
  }

  .periodicity {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .periodicity-right {
    text-align: right;
    max-width: 420px;
  }
}

@media (min-width: 1024px) {
  .header-inner {
    padding: 12px 40px;
  }
}
</style>