<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { db, storage, auth } from "@/firebase/config";
import {
  doc,
  getDoc,
  setDoc,
  getDocs,
  deleteDoc,
  collection,
  serverTimestamp,
} from "firebase/firestore";
import { ref as storageRef, uploadBytes, getDownloadURL, deleteObject } from "firebase/storage";

const route = useRoute();
const router = useRouter();

const projectId = route.params.id_proyecto;

// Datos del proyecto
const projectTitle = ref("Cargando...");
const periodicity = ref("...");
const isLoadingProject = ref(true);

// Periodos
const periods = ref([]); // { id, label, balanceFile, resultsFile, hasChanges, hasAnalysis }
const isUploading = ref(false);
const isProcessing = ref(false);

// refs inputs ocultos
const fileInputRefs = ref({});
const setInputRef = (el, periodId, type) => {
  if (el) fileInputRefs.value[`${periodId}_${type}`] = el;
};

onMounted(async () => {
  if (!projectId) {
    alert("No se encontró el ID del proyecto en la URL");
    return;
  }

  try {
    const docRef = doc(db, "proyectos", projectId);
    const docSnap = await getDoc(docRef);

    if (docSnap.exists()) {
      const data = docSnap.data();
      projectTitle.value = data.nombre || "Sin Título";
      periodicity.value = data.periodicidad || "Desconocida";

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

// ===== Helpers (mono vs multi / qué procesar) =====
const completePeriods = computed(() =>
  periods.value.filter((p) => p.balanceFile && p.resultsFile)
);

// MULTI si hay más de 1 periodo completo (con BG + ER)
const isMultiPeriod = computed(() => completePeriods.value.length > 1);

// Procesar si: está completo y (cambió o no tiene análisis)
const periodsToProcess = computed(() =>
  completePeriods.value.filter((p) => p.hasChanges || !p.hasAnalysis)
);

const canGenerate = computed(() => periodsToProcess.value.length > 0);

const hasMissingDates = computed(() => {
  return isMultiPeriod.value && completePeriods.value.some(p => !p.periodDate);
});

// Autollenado: Convierte "2023-01" a "Enero 2023"
function handleDateChange(p) {
  if (p.periodDate) {
    const [year, month] = p.periodDate.split('-');
    const meses = [
      "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ];
    // Asigna el nombre automáticamente
    p.label = `${meses[parseInt(month) - 1]} ${year}`;
  }
  // Guarda en Firebase
  savePeriodToFirestore(p);
}

// Actualiza el modo del proyecto en Firestore (mono/multi)
async function updateProjectAnalysisMode() {
  const projectRef = doc(db, "proyectos", projectId);
  const mode = isMultiPeriod.value ? "multi" : "mono";

  await setDoc(
    projectRef,
    {
      analysis_mode: mode,
      periods_count: completePeriods.value.length,
      updatedAt: serverTimestamp(),
    },
    { merge: true }
  );
}

// ===== Firestore periodos =====
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

        // detecta si ya hay análisis guardado
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

    // por si el proyecto ya existía con varios periodos completos
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

    // cada cambio puede alterar si ya es multi o no (cuando se completan docs)
    await updateProjectAnalysisMode();
  } catch (error) {
    console.error("Error guardando periodo:", error);
  }
}

// ===== Upload / delete archivos =====
function triggerFileInput(periodId, type) {
  const input = fileInputRefs.value[`${periodId}_${type}`];
  if (input) input.click();
}

async function handleFileChange(event, periodId, type) {
  const file = event.target.files?.[0];
  if (!file) return;

  if (file.type !== "application/pdf") {
    alert("Por favor sube solo archivos PDF");
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

      // si cambias archivo, invalidas análisis anterior
      p.hasChanges = true;
      p.hasAnalysis = false;

      await savePeriodToFirestore(p);
    }
  } catch (error) {
    console.error("Error subiendo:", error);
    alert("Error al subir a Firebase.");
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

  if (!confirm(`¿Eliminar ${fileData.name}?`)) return;

  isUploading.value = true;

  try {
    await deleteObject(storageRef(storage, fileData.path));

    if (type === "balance") p.balanceFile = null;
    if (type === "resultado") p.resultsFile = null;

    p.hasChanges = true;
    p.hasAnalysis = false;

    await savePeriodToFirestore(p);
  } catch (error) {
    console.error("Error eliminando archivo:", error);
  } finally {
    isUploading.value = false;
  }
}

async function removePeriod(periodId) {
  const p = periods.value.find((x) => x.id === periodId);
  if (!p || !confirm(`¿Eliminar ${p.label}?`)) return;

  isUploading.value = true;

  try {
    if (p.balanceFile) await deleteObject(storageRef(storage, p.balanceFile.path)).catch(() => {});
    if (p.resultsFile) await deleteObject(storageRef(storage, p.resultsFile.path)).catch(() => {});

    await deleteDoc(doc(db, "proyectos", projectId, "periodos", periodId));
    periods.value = periods.value.filter((period) => period.id !== periodId);

    // re-etiquetar
    for (let i = 0; i < periods.value.length; i++) {
      periods.value[i].label = `Periodo ${i + 1}`;
      await savePeriodToFirestore(periods.value[i]);
    }

    // por si bajó de multi a mono
    await updateProjectAnalysisMode();
  } catch (error) {
    console.error("Error:", error);
  } finally {
    isUploading.value = false;
  }
}

// ===== Generar análisis + redirect mono/multi =====
async function generateAnalysis() {
  isProcessing.value = true;

  const aProcesar = periodsToProcess.value;

  try {
    if (aProcesar.length === 0) {
      console.log("Todo está procesado. Redirigiendo al dashboard...");
      
      const mode = isMultiPeriod.value ? "multi" : "mono";
      const base = mode === "multi"
        ? `/proyecto/${projectId}/dashboard-multi`
        : `/proyecto/${projectId}/dashboard`;

      router.push(`${base}/rentabilidad`);
      return;
    }

    const promesas = aProcesar.map((p) => {
      const payload = {
        project_id: projectId,
        period_id: p.id,
        balance_url: p.balanceFile.url,
        resultados_url: p.resultsFile.url,
        periodicidad: periodicity.value,
      };

      return fetch("http://127.0.0.1:8000/api/documents/analyze-period", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then((res) => res.json());
    });

    const resultados = await Promise.all(promesas);

    for (const res of resultados) {
      if (res.estatus === "Completado") {
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
    }

    // Guarda status + modo + count
    const projectRef = doc(db, "proyectos", projectId);
    const mode = isMultiPeriod.value ? "multi" : "mono";

    await setDoc(
      projectRef,
      {
        status: "completo",
        analysis_mode: mode,
        periods_count: completePeriods.value.length,
        updatedAt: serverTimestamp(),
      },
      { merge: true }
    );

    // Redirect: mono vs multi
    const base = mode === "multi"
      ? `/proyecto/${projectId}/dashboard-multi`
      : `/proyecto/${projectId}/dashboard`;

    router.push(`${base}/rentabilidad`);
  } catch (error) {
    console.error("Error en el análisis:", error);
    alert("Hubo un error procesando los documentos.");
  } finally {
    isProcessing.value = false;
  }
}
</script>

<template>
  <div class="page">
    <header class="header">
      <div class="header-inner">
        <div class="brand">
          <div class="logo" aria-hidden="true">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <g clip-path="url(#clip0)">
                <path
                  d="M42.1739 20.1739L27.8261 5.82609C29.1366 7.13663 28.3989 10.1876 26.2002 13.7654C24.8538 15.9564 22.9595 18.3449 20.6522 20.6522C18.3449 22.9595 15.9564 24.8538 13.7654 26.2002C10.1876 28.3989 7.13663 29.1366 5.82609 27.8261L20.1739 42.1739C21.4845 43.4845 24.5355 42.7467 28.1133 40.548C30.3042 39.2016 32.6927 37.3073 35 35C37.3073 32.6927 39.2016 30.3042 40.548 28.1133Z"
                  fill="currentColor"
                />
                <path
                  fill-rule="evenodd"
                  clip-rule="evenodd"
                  d="M7.24189 26.4066C7.31369 26.4411 7.64204 26.5637 8.52504 26.3738C9.59462 26.1438 11.0343 25.5311 12.7183 24.4963C14.7583 23.2426 17.0256 21.4503 19.238 19.238C21.4503 17.0256 23.2426 14.7583 24.4963 12.7183C25.5311 11.0343 26.1438 9.59463 26.3738 8.52504C26.5637 7.64204 26.4411 7.31369 26.4066 7.24189C26.345 7.21246 26.143 7.14535 25.6664 7.1918C24.9745 7.25925 23.9954 7.5498 22.7699 8.14278C20.3369 9.32007 17.3369 11.4915 14.4142 14.4142C11.4915 17.3369 9.32007 20.3369 8.14278 22.7699C7.5498 23.9954 7.25925 24.9745 7.1918 25.6664C7.14534 26.143 7.21246 26.345 7.24189 26.4066ZM29.9001 10.7285C29.4519 12.0322 28.7617 13.4172 27.9042 14.8126C26.465 17.1544 24.4686 19.6641 22.0664 22.0664C19.6641 24.4686 17.1544 26.465 14.8126 27.9042C13.4172 28.7617 12.0322 29.4519 10.7285 29.9001L21.5754 40.747C21.6001 40.7606 21.8995 40.931 22.8729 40.7217C23.9424 40.4916 25.3821 39.879 27.0661 38.8441C29.1062 37.5904 31.3734 35.7982 33.5858 33.5858C35.7982 31.3734 37.5904 29.1062 38.8441 27.0661C39.879 25.3821 40.4916 23.9425 40.7216 22.8729C40.931 21.8995 40.7606 21.6001 40.747 21.5754L29.9001 10.7285ZM29.2403 4.41187L43.5881 18.7597C44.9757 20.1473 44.9743 22.1235 44.6322 23.7139C44.2714 25.3919 43.4158 27.2666 42.252 29.1604C40.8128 31.5022 38.8165 34.012 36.4142 36.4142C34.012 38.8165 31.5022 40.8128 29.1604 42.252C27.2666 43.4158 25.3919 44.2714 23.7139 44.6322C22.1235 44.9743 20.1473 44.9757 18.7597 43.5881L4.41187 29.2403C3.29027 28.1187 3.08209 26.5973 3.21067 25.2783C3.34099 23.9415 3.8369 22.4852 4.54214 21.0277C5.96129 18.0948 8.43335 14.7382 11.5858 11.5858C14.7382 8.43335 18.0948 5.9613 21.0277 4.54214C22.4852 3.8369 23.9415 3.34099 25.2783 3.21067C26.5973 3.08209 28.1187 3.29028 29.2403 4.41187Z"
                  fill="currentColor"
                />
              </g>
              <defs>
                <clipPath id="clip0"><rect width="48" height="48" fill="white" /></clipPath>
              </defs>
            </svg>
          </div>
          <h2 class="brand-name">PymeScope</h2>
        </div>

        <div class="project-meta">
          <span class="project-title">{{ projectTitle }}</span>
          <span class="pill">Periodicidad: {{ periodicity }}</span>
        </div>

        <div class="actions">
          <RouterLink class="back" to="/misProyectos">
            <span class="material-symbols-outlined">arrow_back</span>
            <span class="back-text">Volver a proyectos</span>
          </RouterLink>
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
              <div class="input-with-icon">
                <input 
                  type="text" 
                  v-model="p.label" 
                  @blur="savePeriodToFirestore(p)" 
                  placeholder="Nombre (Ej. Enero 2024)" 
                  class="editable-input label-input"
                  title="Puedes editar este nombre"
                />
                <span class="material-symbols-outlined edit-icon">edit</span>
              </div>
              
              <div class="date-wrapper">
                <input 
                  type="month" 
                  v-model="p.periodDate" 
                  @change="handleDateChange(p)" 
                  class="editable-input date-input"
                  title="Selecciona el mes y año"
                />
                <span v-if="isMultiPeriod && !p.periodDate" class="required-badge">
                  * Obligatorio
                </span>
              </div>
            </div>
            <button class="btn-icon-danger" @click="removePeriod(p.id)" title="Eliminar periodo completo">
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
                      <button class="btn-text-danger" @click="removeDocument(p.id, 'balance')">
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
                accept="application/pdf"
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
                      <button class="btn-text-danger" @click="removeDocument(p.id, 'resultado')">
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
                accept="application/pdf"
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
          Comienza agregando los estados financieros correspondientes a cada trimestre del año 2024.
        </p>
      </section>
    </main>

    <footer class="bottom">
      <div class="container bottom-inner">
        <span v-if="hasMissingDates" class="warning-text">
          Faltan fechas en algunos periodos para el análisis multiperiodo.
        </span>
        <span v-else class="autosave">Todos los cambios se guardan automáticamente</span>

        <button
          class="btn-generate"
          type="button"
          :disabled="!canGenerate || isUploading || isProcessing || hasMissingDates"
          @click="generateAnalysis"
        >
          <span v-if="isUploading">Subiendo a Firebase...</span>
          <span v-else-if="isProcessing">Analizando con IA...</span>
          <span v-else>Generar análisis</span>

          <span v-if="!isUploading && !isProcessing" class="material-symbols-outlined">
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

.period-card-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
}

.mini-pill {
  font-size: 12px;
  font-weight: 800;
  color: #475569;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 999px;
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

.editable-input {
  border: 1px solid transparent;
  background: transparent;
  border-radius: 6px;
  padding: 4px 8px;
  font-family: inherit;
  font-size: 14px;
  color: #0e161b;
  transition: all 0.2s;
}

.editable-input:hover {
  background: #f1f5f9;
}

.editable-input:focus {
  outline: none;
  border-color: #299de0;
  background: white;
  box-shadow: 0 0 0 2px rgba(41, 157, 224, 0.1);
}

.label-input {
  font-weight: 900;
  width: 140px;
}

.date-input {
  color: #507c95;
  font-weight: 600;
  cursor: pointer;
}

@media (min-width: 640px) {
  .back-text {
    display: inline;
  }
  .autosave {
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

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.edit-icon {
  position: absolute;
  right: 8px;
  font-size: 14px;
  color: #94a3b8;
  pointer-events: none; /* Para que el clic pase al input */
}

.label-input {
  padding-right: 24px; /* Espacio para el lapicito */
}

.date-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
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

@media (min-width: 640px) {
  .warning-text {
    display: inline;
  }
}
</style>