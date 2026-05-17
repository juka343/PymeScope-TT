<script setup>
import { onBeforeUnmount, onMounted, ref, computed, nextTick } from "vue";
import { useRouter } from "vue-router";
import { ref as storageRef, deleteObject } from "firebase/storage";
import { useConfirm } from "@/composables/useConfirm";
import { useToast } from "@/composables/useToast";

import { auth, db, storage } from "@/firebase/config";
import { onAuthStateChanged, signOut } from "firebase/auth";
import {
  collection,
  doc,
  setDoc,
  updateDoc,
  getDoc,
  getDocs,
  deleteDoc,
  query,
  where,
  serverTimestamp,
} from "firebase/firestore";

const router = useRouter();
const { confirm } = useConfirm();
const { toast } = useToast();

// ====== AUTH UI ======
const user = ref(null);
const authUnsub = ref(null);

const userDisplayName = computed(() => {
  if (!user.value) return "Usuario";
  return (
    user.value.displayName ||
    (user.value.email ? user.value.email.split("@")[0] : "Usuario")
  );
});

const userEmail = computed(() => (user.value?.email ? user.value.email : ""));
const userRole = computed(() => "Usuario");
const userPhotoURL = computed(() => user.value?.photoURL || "");

// ====== ONBOARDING ======
const showOnboarding = ref(false);
const onboardingStep = ref(0);
const onboardingChecking = ref(true);

const onboardingSlides = [
  {
    title: "Bienvenido a PymeScope",
  text: `Estamos felices de tenerte aquí :)
Tus datos están seguros en todo momento.
PymeScope puede cometer errores, así que consulta a un profesional calificado para obtener asesoramiento financiero.`,    icon: "waving_hand",
  },
  {
    title: "Sube tus archivos",
    text: "Sube tus archivos de Balance General y Estado de Resultados. Nuestro sistema extraerá los datos automáticamente para generar tu dashboard financiero.",
    icon: "cloud_upload",
  },
{
    title: "Formato de Archivos",
    icon: "description",
    bullets: [
      "Evita usar abreviaturas en los nombres de las cuentas.",
      "Incluye sumas totales para cada categoría.",
      "Mantén una estructura clara y consistente.",
    ],
  },
  {
    title: "Estructura ideal de datos",
    text: "Para que el motor analítico funcione correctamente, asegúrate de que tus archivos tengan encabezados claros en la primera fila.",
    icon: "table_view",
  },
  {
    title: "¡Todo listo!",
    text: "Ahora puedes comenzar a analizar la salud financiera de tu empresa con PymeScope.",
    icon: "rocket_launch",
  },
];

async function checkOnboarding(uid) {
  onboardingChecking.value = true;

  try {
    const onboardingRef = doc(db, "user_onboarding", uid);
    const onboardingSnap = await getDoc(onboardingRef);

    if (!onboardingSnap.exists()) {
      showOnboarding.value = true;
      onboardingStep.value = 0;
      return;
    }

    const data = onboardingSnap.data();
    showOnboarding.value = data?.misProyectosIntroCompleted !== true;
    onboardingStep.value = 0;
  } catch (error) {
    console.error("Error verificando onboarding:", error);
    showOnboarding.value = true;
    onboardingStep.value = 0;
  } finally {
    onboardingChecking.value = false;
  }
}

async function finishOnboarding() {
  const currentUser = auth.currentUser;
  if (!currentUser) return;

  try {
    const onboardingRef = doc(db, "user_onboarding", currentUser.uid);

    await setDoc(
      onboardingRef,
      {
        misProyectosIntroCompleted: true,
        completedAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      },
      { merge: true }
    );

    showOnboarding.value = false;
    onboardingStep.value = 0;
  } catch (error) {
    console.error("Error guardando onboarding:", error);
    toast({
      message: "No se pudo guardar el estado del onboarding.",
      type: "error",
    });
  }
}

function nextOnboardingStep() {
  if (onboardingStep.value < onboardingSlides.length - 1) {
    onboardingStep.value += 1;
    return;
  }
  finishOnboarding();
}

function prevOnboardingStep() {
  if (onboardingStep.value > 0) {
    onboardingStep.value -= 1;
  }
}

function skipOnboarding() {
  finishOnboarding();
}

onMounted(() => {
  authUnsub.value = onAuthStateChanged(auth, async (u) => {
    user.value = u;

    if (!u) {
      router.replace("/");
      return;
    }

    await checkOnboarding(u.uid);
    await loadUserProjects();
  });

  window.addEventListener("keydown", onKeydown);
});

onBeforeUnmount(() => {
  if (authUnsub.value) authUnsub.value();
  window.removeEventListener("keydown", onKeydown);
});

async function handleLogout() {
  try {
    await signOut(auth);
    router.replace("/");
  } catch (e) {
    console.error("Error al cerrar sesión:", e);
  }
}

// ====== MODAL NUEVO PROYECTO ======
const isModalOpen = ref(false);

// Form
const projectName = ref("");
const periodicity = ref("mensual");
const companyName = ref("");
const notes = ref("");

// ===== Validaciones =====
const touched = ref({
  projectName: false,
  companyName: false,
});
const submitAttempted = ref(false);

function markTouched(field) {
  touched.value[field] = true;
}

const projectNameError = computed(() => {
  if (!projectName.value.trim()) return "Este campo es obligatorio.";
  return "";
});

const companyNameError = computed(() => {
  if (!companyName.value.trim()) return "Este campo es obligatorio.";
  return "";
});

function showError(field) {
  return touched.value[field] || submitAttempted.value;
}

const isFormValid = computed(() => {
  return !projectNameError.value && !companyNameError.value;
});

function openModal() {
  resetForm();
  isModalOpen.value = true;
}
function closeModal() {
  isModalOpen.value = false;
}
function resetForm() {
  projectName.value = "";
  periodicity.value = "mensual";
  companyName.value = "";
  notes.value = "";
  touched.value = { projectName: false, companyName: false };
  submitAttempted.value = false;
}
function handleCancel() {
  closeModal();
}
const creating = ref(false);

async function handleCreate() {
  const currentUser = auth.currentUser;
  if (!currentUser) {
    toast({
      message: "Debes iniciar sesión para crear un proyecto.",
      type: "warning",
    });
    return;
  }

submitAttempted.value = true;

if (!projectName.value.trim()) {
  toast({
    message: "El nombre del proyecto es obligatorio.",
    type: "warning",
  });
  return;
}

if (!isFormValid.value) {
  return;
}

  creating.value = true;

  try {
    const projectId = crypto.randomUUID();
    const projectRef = doc(db, "proyectos", projectId);

    await setDoc(projectRef, {
      nombre: projectName.value.trim(),
      empresa: companyName.value.trim() || null,
      periodicidad: periodicity.value,
      notas: notes.value.trim() || null,
      userId: currentUser.uid,
      status: "en_edicion",
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    });

    const docSnap = await getDoc(projectRef);
    if (!docSnap.exists()) {
      throw new Error("El proyecto no se guardó correctamente en la base de datos");
    }

    closeModal();
    resetForm();

    router.push(`/proyecto/${projectId}/cargar`);
  } catch (error) {
    console.error("Error creando proyecto:", error);
    toast({
      message: "Error al crear el proyecto. Intenta de nuevo.",
      type: "error",
    });
  } finally {
    creating.value = false;
  }
}

function onKeydown(e) {
  if (e.key === "Escape" && isModalOpen.value) closeModal();
}

// ====== PROYECTOS ======
const projects = ref([]);
const loadingProjects = ref(true);

async function loadUserProjects() {
  const currentUser = auth.currentUser;
  if (!currentUser) return;

  loadingProjects.value = true;

  try {
    const projectsRef = collection(db, "proyectos");
    const q = query(projectsRef, where("userId", "==", currentUser.uid));
    const snapshot = await getDocs(q);

    const projectsList = snapshot.docs.map((docSnap) => {
      const data = docSnap.data();

      const periodsCount = Number(data.periods_count || 0);

      const analysisMode =
        data.analysis_mode || (periodsCount > 1 ? "multi" : "mono");

      return {
        id: docSnap.id,
        title: data.nombre || "Sin título",
        status: data.status || "en_edicion",
        company: data.empresa || "Sin empresa",
        periods: data.periodicidad || "Sin periodicidad",
        periodsCount,
        analysisMode,
        createdAt: data.createdAt?.toDate?.() || new Date(0),
        modified:
          data.createdAt?.toDate?.()?.toLocaleDateString("es-MX", {
            day: "numeric",
            month: "short",
            year: "numeric",
          }) || "Sin fecha",
      };
    });

    projectsList.sort((a, b) => b.createdAt - a.createdAt);
    projects.value = projectsList;
  } catch (error) {
    console.error("Error cargando proyectos:", error);
  } finally {
    loadingProjects.value = false;
  }
}

function goToAnalysis(p) {
  if (!p || p.status !== "completo") return;

  const base = p.analysisMode === "multi" ? "dashboard-multi" : "dashboard";
  router.push(`/proyecto/${p.id}/${base}/resumen`);
}

const deleting = ref(null);

async function removeProject(id) {
  const confirmed = await confirm({
    title: "Eliminar proyecto",
    message:
      "¿Estás seguro de eliminar este proyecto y TODOS sus archivos? Esta acción no se puede deshacer.",
    confirmText: "Sí, eliminar",
    cancelText: "Cancelar",
    variant: "danger",
  });
  if (!confirmed) return;

  deleting.value = id;

  try {
    const periodosRef = collection(db, "proyectos", id, "periodos");
    const snapshot = await getDocs(periodosRef);

    const promesasLimpieza = [];

    snapshot.forEach((docSnap) => {
      const data = docSnap.data();

      if (data.balanceFile && data.balanceFile.path) {
        const bRef = storageRef(storage, data.balanceFile.path);
        promesasLimpieza.push(
          deleteObject(bRef).catch((e) => console.warn("Balance no hallado", e))
        );
      }

      if (data.resultsFile && data.resultsFile.path) {
        const rRef = storageRef(storage, data.resultsFile.path);
        promesasLimpieza.push(
          deleteObject(rRef).catch((e) => console.warn("Resultado no hallado", e))
        );
      }

      promesasLimpieza.push(deleteDoc(docSnap.ref));
    });

    if (promesasLimpieza.length > 0) {
      await Promise.all(promesasLimpieza);
    }

    await deleteDoc(doc(db, "proyectos", id));

    projects.value = projects.value.filter((p) => p.id !== id);
  } catch (error) {
    console.error("Error eliminando proyecto:", error);
    toast({
      message: "Error al eliminar el proyecto. Intenta de nuevo.",
      type: "error",
    });
  } finally {
    deleting.value = null;
  }
}
// ====== EDICIÓN DE NOMBRE DE PROYECTO ======
const editingId = ref(null);
const editNameInput = ref("");

async function iniciarEdicionNombre(p) {
  editingId.value = p.id;
  editNameInput.value = p.title;
  await nextTick();
  const inputEl = document.getElementById(`edit-input-${p.id}`);
  if (inputEl) inputEl.focus();
}

function cancelarNombre() {
  editingId.value = null;
  editNameInput.value = "";
}

async function guardarNombre(p) {
  if (!editNameInput.value.trim()) return;
  try {
    const projectRef = doc(db, "proyectos", p.id);
    await updateDoc(projectRef, {
      nombre: editNameInput.value.trim()
    });
    p.title = editNameInput.value.trim();
    editingId.value = null;
  } catch (error) {
    console.error("Error al actualizar nombre de proyecto:", error);
    toast({ message: "Hubo un error al guardar el nombre.", type: "error" });
  }
}
</script>

<template>
  <div class="page">
    <header class="header">
      <div class="container header-inner">
        <div class="brand">
            <img src="/logo.png" alt="Logo PymeScope" class="brand-icon" />
          <h1 class="brand-name">PymeScope</h1>
        </div>

        <div class="user">
          <div
            class="avatar"
            :style="userPhotoURL ? { backgroundImage: `url('${userPhotoURL}')` } : {}"
            aria-hidden="true"
          ></div>

          <div class="user-text">
            <span class="user-name">{{ userDisplayName }}</span>
            <span class="user-role">
              {{ userRole }}<template v-if="userEmail"> · {{ userEmail }}</template>
            </span>
          </div>

          <div class="divider"></div>

          <button class="logout" type="button" @click="handleLogout">
            <span class="material-symbols-outlined">logout</span>
            <span class="logout-text">Cerrar sesión</span>
          </button>
        </div>
      </div>
    </header>

    <main class="container main">
      <div class="top">
        <div class="top-left">
          <h2>Mis proyectos de análisis</h2>
          <p>Crea y administra tus análisis financieros en un solo lugar.</p>
        </div>

        <button class="btn-primary" type="button" @click="openModal">
          <span class="material-symbols-outlined">add</span>
          Nuevo proyecto
        </button>
      </div>

      <section class="grid">
        <article v-for="p in projects" :key="p.id" class="card">
          <div class="card-top">
            <span class="badge" :class="p.status === 'completo' ? 'badge-ok' : 'badge-warn'">
              {{ p.status === "completo" ? "Completo" : "En edición" }}
            </span>
          </div>

          <div class="card-body">
            <div v-if="editingId === p.id" class="edit-name-wrap">
              <input :id="`edit-input-${p.id}`" v-model="editNameInput" class="input input-sm" type="text" @keyup.enter="guardarNombre(p)" @keyup.esc="cancelarNombre" />
              <button class="btn-icon-small btn-icon-ok" @click="guardarNombre(p)" title="Guardar"><span class="material-symbols-outlined">check</span></button>
              <button class="btn-icon-small btn-icon-cancel" @click="cancelarNombre" title="Cancelar"><span class="material-symbols-outlined">close</span></button>
            </div>
            <div v-else class="title-with-edit">
              <h3>{{ p.title }}</h3>
              <button class="btn-icon-small edit-icon-btn" @click="iniciarEdicionNombre(p)" title="Editar nombre">
                <span class="material-symbols-outlined">edit</span>
              </button>
            </div>

            <div class="meta">
              <div class="meta-row">
                <span class="material-symbols-outlined">business</span>
                <span>{{ p.company }}</span>
              </div>
              <div class="meta-row">
                <span class="material-symbols-outlined">date_range</span>
                <span>Periodos: {{ p.periods }}</span>
              </div>
            </div>
          </div>

          <div class="card-divider"></div>

          <div class="card-bottom">
            <span class="modified">Modificado: {{ p.modified }}</span>

            <div class="actions">
              <button
                class="icon-btn"
                type="button"
                title="Editar proyecto"
                @click="router.push(`/proyecto/${p.id}/cargar`)"
              >
                <span class="material-symbols-outlined">edit</span>
              </button>

              <button
                class="icon-btn danger"
                type="button"
                title="Eliminar proyecto"
                @click="removeProject(p.id)"
                :disabled="deleting === p.id"
              >
                <span class="material-symbols-outlined">
                  {{ deleting === p.id ? "hourglass_empty" : "delete" }}
                </span>
              </button>

              <button
                class="link"
                type="button"
                :disabled="p.status !== 'completo'"
                @click="goToAnalysis(p)"
              >
                Ver análisis
                <span class="material-symbols-outlined">arrow_forward</span>
              </button>
            </div>
          </div>
        </article>

        <button class="card dashed" type="button" @click="openModal">
          <div class="dashed-icon">
            <span class="material-symbols-outlined">add</span>
          </div>
          <h3>Crear nuevo análisis</h3>
          <p>Comienza un nuevo proyecto financiero desde cero</p>
        </button>
      </section>
    </main>

    <!-- MODAL NUEVO PROYECTO -->
    <div
      v-if="isModalOpen"
      class="modal-root"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div class="overlay" @click="closeModal"></div>

      <div class="modal-wrap">
        <div class="modal">
          <button class="modal-close" type="button" @click="closeModal" aria-label="Cerrar">
            <span class="material-symbols-outlined">close</span>
          </button>

          <div class="modal-head">
            <div class="modal-icon">
              <span class="material-symbols-outlined">analytics</span>
            </div>

            <div>
              <h3 id="modal-title">Crear nuevo proyecto de análisis</h3>
              <p>Define la información básica para comenzar tu análisis financiero.</p>
            </div>
          </div>

          <form class="form" @submit.prevent>
            <div class="field">
              <label for="project-name">Nombre del proyecto <span class="req">*</span></label>
              <input
                id="project-name"
                v-model.trim="projectName"
                type="text"
                placeholder="Ej. Análisis financiero 2024"
                :class="{ invalid: showError('projectName') && projectNameError }"
                @blur="markTouched('projectName')"
                required
              />
              <small v-if="showError('projectName') && projectNameError" class="field-error">
                <span class="material-symbols-outlined">error</span>
                {{ projectNameError }}
              </small>
              <small v-else>Este nombre te ayudará a identificar tu análisis</small>
            </div>

            <div class="field">
              <span class="label">Periodicidad del análisis <span class="req">*</span></span>

              <div class="radio-grid">
                <label class="radio">
                  <input v-model="periodicity" type="radio" value="mensual" />
                  <span>Mensual</span>
                </label>

                <label class="radio">
                  <input v-model="periodicity" type="radio" value="trimestral" />
                  <span>Trimestral</span>
                </label>

                <label class="radio">
                  <input v-model="periodicity" type="radio" value="anual" />
                  <span>Anual</span>
                </label>
              </div>

              <small>La periodicidad no podrá cambiarse una vez creado el proyecto</small>
            </div>

            <div class="field">
              <label for="company-name">
                Nombre de la empresa <span class="req">*</span>
              </label>
              <input
                id="company-name"
                v-model.trim="companyName"
                type="text"
                placeholder="Ej. Pyme Comercial S.A. de C.V."
                :class="{ invalid: showError('companyName') && companyNameError }"
                @blur="markTouched('companyName')"
                required
              />
              <small v-if="showError('companyName') && companyNameError" class="field-error">
                <span class="material-symbols-outlined">error</span>
                {{ companyNameError }}
              </small>
            </div>

            <div class="field">
              <label for="notes">Descripción o notas <span class="opt">(opcional)</span></label>
              <textarea
                id="notes"
                v-model.trim="notes"
                rows="3"
                placeholder="Notas adicionales sobre este análisis (opcional)"
              />
            </div>
          </form>

          <div class="modal-actions">
            <button
              class="btn-primary"
              type="button"
              @click="handleCreate"
              :disabled="creating || !projectName.trim()"
            >
              {{ creating ? "Creando..." : "Crear proyecto y continuar" }}
            </button>
            <button class="btn-secondary" type="button" @click="handleCancel" :disabled="creating">
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ONBOARDING -->
    <div
      v-if="showOnboarding && !onboardingChecking"
      class="onboarding-root"
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-title"
    >
      <div class="onboarding-overlay"></div>

      <div class="onboarding-wrap">
        <div class="onboarding-modal">
          <div class="onboarding-top">
            <span class="onboarding-step">
              Paso {{ onboardingStep + 1 }} de {{ onboardingSlides.length }}
            </span>

            <button class="onboarding-skip" type="button" @click="skipOnboarding">
              Saltar intro
            </button>
          </div>

          <div class="onboarding-body">
            <span class="material-symbols-outlined onboarding-watermark">
              {{ onboardingSlides[onboardingStep].icon }}
            </span>

            <div class="onboarding-icon">
              <span class="material-symbols-outlined">
                {{ onboardingSlides[onboardingStep].icon }}
              </span>
            </div>

            <h2 id="onboarding-title">{{ onboardingSlides[onboardingStep].title }}</h2>

            <p v-if="!onboardingSlides[onboardingStep].bullets">
              {{ onboardingSlides[onboardingStep].text }}
            </p>

            <ul
              v-else
              class="onboarding-bullet-list"
              aria-label="Recomendaciones de formato de archivos"
            >
              <li
                v-for="(item, idx) in onboardingSlides[onboardingStep].bullets"
                :key="idx"
                class="onboarding-bullet-item"
              >
                <span class="material-symbols-outlined onboarding-bullet-icon">
                  check_circle
                </span>
                <span>{{ item }}</span>
              </li>
            </ul>

            <div v-if="onboardingStep === 3" class="onboarding-table-demo">
              <div class="table-demo-badge">
                <span class="material-symbols-outlined">check_circle</span>
                Buen ejemplo
              </div>

              <div class="table-demo">
                <div class="table-demo-head">
                  <div>CUENTA</div>
                  <div class="right">MONTO</div>
                </div>
                <div class="table-demo-row">
                  <div>Caja</div>
                  <div class="right">$10,000.00</div>
                </div>
                <div class="table-demo-row">
                  <div>Bancos</div>
                  <div class="right">$1,209,742.96</div>
                </div>
                <div class="table-demo-row">
                  <div>Clientes</div>
                  <div class="right">$1,643,223.10</div>
                </div>
                <div class="table-demo-total">
                  <div>Total Activos</div>
                  <div class="right">$2,862,966.06</div>
                </div>
              </div>
            </div>
          </div>

          <div class="onboarding-bottom">
            <button
              class="onboarding-back"
              type="button"
              @click="prevOnboardingStep"
              :class="{ invisible: onboardingStep === 0 }"
            >
              <span class="material-symbols-outlined">arrow_back</span>
              Atrás
            </button>

            <div class="onboarding-dots">
              <span
                v-for="(_, idx) in onboardingSlides"
                :key="idx"
                class="onboarding-dot"
                :class="{ active: idx === onboardingStep }"
              ></span>
            </div>

            <button class="onboarding-next" type="button" @click="nextOnboardingStep">
              {{ onboardingStep === onboardingSlides.length - 1 ? "Comenzar ahora" : "Siguiente" }}
              <span class="material-symbols-outlined">
                {{
                  onboardingStep === onboardingSlides.length - 1
                    ? "rocket_launch"
                    : "arrow_forward"
                }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  --primary: #299de0;
  --bg: #f6f7f8;
  --card: #ffffff;
  --text: #0e161b;
  --muted: #507c95;
  --border: #e8eff3;

  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

.container {
  width: min(1280px, 92vw);
  margin: 0 auto;
}

/* Header */
.header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--card);
  border-bottom: 1px solid var(--border);
}

.header-inner {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
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
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: #e2e8f0;
  background-size: cover;
  background-position: center;
}

.user-text {
  display: none;
  flex-direction: column;
  line-height: 1.1;
}

.user-name {
  font-size: 13px;
  font-weight: 800;
}

.user-role {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 700;
}

.divider {
  width: 1px;
  height: 28px;
  background: #e2e8f0;
  display: none;
}

.logout {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-weight: 800;
  background: transparent;
  border: none;
  cursor: pointer;
}

.logout:hover {
  color: var(--primary);
}

.logout span.material-symbols-outlined {
  font-size: 20px;
}

.logout-text {
  display: none;
}

/* Main */
.main {
  padding: 32px 0;
}

.top {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 22px;
}

.top-left h2 {
  margin: 0;
  font-size: clamp(28px, 3vw, 40px);
  font-weight: 900;
  letter-spacing: -0.03em;
}

.top-left p {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 18px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 900;
  font-size: 14px;
  box-shadow: 0 10px 22px rgba(41, 157, 224, 0.2);
  border: none;
  cursor: pointer;
}

.btn-primary:hover {
  filter: brightness(0.95);
}

.btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-primary span.material-symbols-outlined {
  font-size: 20px;
}

/* Grid */
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  text-align: left;
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 12px;
}

.badge {
  font-size: 12px;
  font-weight: 900;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid transparent;
}

.badge-ok {
  background: #ecfdf5;
  color: #047857;
  border-color: #d1fae5;
}

.badge-warn {
  background: #fffbeb;
  color: #b45309;
  border-color: #fde68a;
}

.card-body h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 900;
}

.card-body h3:hover {
  color: var(--primary);
}

.meta {
  margin-top: 14px;
  display: grid;
  gap: 10px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 14px;
}

.meta-row span.material-symbols-outlined {
  font-size: 18px;
  opacity: 0.7;
}

.card-divider {
  height: 1px;
  background: #f1f5f9;
  margin: 16px 0;
}

.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.modified {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 700;
}

.actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.icon-btn {
  padding: 6px;
  border-radius: 10px;
  background: transparent;
  color: var(--muted);
  border: none;
  cursor: pointer;
}
.icon-btn:hover {
  color: var(--primary);
}
.icon-btn span {
  font-size: 20px;
}

.icon-btn.danger:hover {
  color: #ef4444;
}

.icon-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.link {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;

  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--primary);
  font-weight: 900;
  font-size: 14px;
}
.link span {
  font-size: 18px;
}

.link:disabled {
  color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Dashed card */
.dashed {
  border: 2px dashed var(--border);
  background: rgba(255, 255, 255, 0.5);
  align-items: center;
  justify-content: center;
  min-height: 240px;
  cursor: pointer;
}
.dashed:hover {
  border-color: rgba(41, 157, 224, 0.5);
}

.dashed-icon {
  width: 48px;
  height: 48px;
  border-radius: 999px;
  background: #f0f4f8;
  color: var(--muted);
  display: grid;
  place-items: center;
  margin-bottom: 10px;
}

.dashed:hover .dashed-icon {
  background: rgba(41, 157, 224, 0.12);
  color: var(--primary);
}

.dashed h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: var(--muted);
}
.dashed:hover h3 {
  color: var(--primary);
}

.dashed p {
  margin: 6px 0 0;
  font-size: 12px;
  color: #94a3b8;
  text-align: center;
  max-width: 240px;
}

/* Modal crear proyecto */
.modal-root {
  position: fixed;
  inset: 0;
  z-index: 60;
}
.overlay {
  position: absolute;
  inset: 0;
  background: rgba(17, 24, 39, 0.6);
  backdrop-filter: blur(6px);
}
.modal-wrap {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 16px;
}
.modal {
  width: 100%;
  max-width: 560px;
  background: white;
  border: 1px solid #eef2f6;
  border-radius: 16px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.25);
  padding: 18px;
  position: relative;
}
.modal-close {
  position: absolute;
  right: 12px;
  top: 12px;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: #94a3b8;
  background: transparent;
  border: none;
  cursor: pointer;
}
.modal-close:hover {
  color: #475569;
}
.modal-close span {
  font-size: 22px;
}
.modal-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 6px 4px 10px;
}
.modal-icon {
  width: 48px;
  height: 48px;
  border-radius: 999px;
  background: rgba(41, 157, 224, 0.12);
  color: var(--primary);
  display: grid;
  place-items: center;
  flex: 0 0 auto;
}
.modal-icon span {
  font-size: 24px;
}
.modal-head h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 900;
}
.modal-head p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.4;
}
.form {
  padding: 8px 4px 0;
  display: grid;
  gap: 14px;
}
.field label,
.field .label {
  display: block;
  font-size: 13px;
  font-weight: 900;
  margin-bottom: 6px;
}
.req {
  color: #ef4444;
}
.opt {
  color: #94a3b8;
  font-weight: 700;
}
.field input,
.field textarea {
  width: 100%;
  border: 1px solid #dce2e5;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  background: #fff;
}
.field textarea {
  resize: vertical;
}
.field input:focus,
.field textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(41, 157, 224, 0.22);
}
.field small {
  display: block;
  margin-top: 6px;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 600;
}
.radio-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}
.radio {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px;
  cursor: pointer;
  background: #fff;
  font-weight: 900;
  color: #0f172a;
}
.radio input {
  accent-color: var(--primary);
}
.modal-actions {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  gap: 10px;
  flex-direction: column;
}
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  color: #0f172a;
  font-weight: 900;
  font-size: 14px;
  cursor: pointer;
}
.btn-secondary:hover {
  background: #f8fafc;
}

/* Onboarding */
.onboarding-bullet-list {
  margin: 22px 0 0;
  padding: 0;
  list-style: none;
  width: 100%;
  max-width: 640px;
  display: grid;
  gap: 22px;
  position: relative;
  z-index: 1;
  text-align: left;
}

.onboarding-bullet-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  color: #507c95;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.65;
}

.onboarding-bullet-icon {
  font-size: 24px;
  color: #299de0;
  flex: 0 0 auto;
  margin-top: 1px;
}

.onboarding-root {
  position: fixed;
  inset: 0;
  z-index: 80;
}

.onboarding-overlay {
  position: absolute;
  inset: 0;
  background: rgba(17, 24, 39, 0.48);
  backdrop-filter: blur(8px);
}

.onboarding-wrap {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 16px;
}

.onboarding-modal {
  width: 100%;
  max-width: 620px;
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 18px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  position: relative;
}

.onboarding-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid #e8eff3;
}

.onboarding-step {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #507c95;
}

.onboarding-skip {
  background: transparent;
  border: none;
  color: #299de0;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.onboarding-body {
  position: relative;
  padding: 52px 32px 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: linear-gradient(180deg, #f0f8fd 0%, #ffffff 100%);
  overflow: hidden;
}
.onboarding-body p {
  margin: 14px 0 0;
  max-width: 430px;
  font-size: 14px;
  line-height: 1.6;
  font-weight: 700;
  color: #507c95;
  position: relative;
  z-index: 1;
  white-space: pre-line;
}

.onboarding-watermark {
  position: absolute;
  right: -12px;
  bottom: -18px;
  font-size: 170px;
  color: #299de0;
  opacity: 0.04;
  pointer-events: none;
}

.onboarding-icon {
  width: 84px;
  height: 84px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #ffffff;
  border: 1px solid #d1dee6;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
}

.onboarding-icon .material-symbols-outlined {
  font-size: 42px;
  color: #299de0;
}

.onboarding-body h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
  letter-spacing: -0.02em;
  position: relative;
  z-index: 1;
}


.onboarding-table-demo {
  width: 100%;
  max-width: 380px;
  margin-top: 24px;
  background: #f8fafb;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 18px 16px 14px;
  position: relative;
  z-index: 1;
}

.table-demo-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #dcfce7;
  color: #166534;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #bbf7d0;
  white-space: nowrap;
}

.table-demo-badge .material-symbols-outlined {
  font-size: 14px;
}

.table-demo {
  margin-top: 10px;
  background: #ffffff;
  border: 1px solid #d1dee6;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.table-demo-head,
.table-demo-row,
.table-demo-total {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.table-demo-head > div,
.table-demo-row > div,
.table-demo-total > div {
  padding: 10px 12px;
  font-size: 13px;
}

.table-demo-head {
  background: #e8eff3;
  border-bottom: 1px solid #d1dee6;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0e161b;
}

.table-demo-row {
  border-bottom: 1px solid #eef2f6;
  color: #507c95;
  font-weight: 700;
}

.table-demo-total {
  background: #f8fafb;
  color: #0e161b;
  font-weight: 900;
}

.right {
  text-align: right;
}

.onboarding-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 22px;
  border-top: 1px solid #e8eff3;
  background: #ffffff;
}

.onboarding-back,
.onboarding-next {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 900;
  padding: 10px 14px;
  cursor: pointer;
}

.onboarding-back {
  border: 1px solid #d1dee6;
  background: #ffffff;
  color: #507c95;
}

.onboarding-back:hover {
  background: #f8fafb;
  color: #0e161b;
}

.onboarding-next {
  border: none;
  background: #299de0;
  color: #ffffff;
  box-shadow: 0 10px 22px rgba(41, 157, 224, 0.2);
}

.onboarding-next:hover {
  filter: brightness(0.96);
}

.onboarding-dots {
  display: flex;
  align-items: center;
  gap: 8px;
}

.onboarding-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #d1dee6;
}

.onboarding-dot.active {
  background: #299de0;
}

.invisible {
  visibility: hidden;
}

/* Validaciones */
.invalid {
  border-color: rgba(239, 68, 68, 0.6) !important;
  background: #fef8f8 !important;
}

.field-error {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #ef4444;
  background: #fee2e2;
  padding: 8px 12px;
  border-radius: 8px;
  margin-top: 6px;
  animation: shake 0.3s ease;
}

.field-error .material-symbols-outlined {
  font-size: 18px;
  flex-shrink: 0;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-4px); }
  40% { transform: translateX(4px); }
  60% { transform: translateX(-3px); }
  80% { transform: translateX(2px); }
}

/* Responsive */
@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .top {
    flex-direction: row;
    align-items: flex-end;
  }

  .logout-text {
    display: inline;
  }

  .modal-actions {
    flex-direction: row-reverse;
    justify-content: flex-start;
  }

  .radio-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 768px) {
  .user-text {
    display: flex;
  }

  .divider {
    display: block;
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .onboarding-top,
  .onboarding-bottom {
    padding: 16px;
  }

  .onboarding-body {
    padding: 36px 20px 28px;
  }

  .onboarding-body h2 {
    font-size: 22px;
  }

.onboarding-body p {
  margin: 14px 0 0;
  max-width: 430px;
  font-size: 14px;
  line-height: 1.6;
  font-weight: 700;
  color: #507c95;
  position: relative;
  z-index: 1;
  white-space: pre-line;
}

  .onboarding-bottom {
    flex-wrap: wrap;
  }

  .onboarding-dots {
    order: 3;
    width: 100%;
    justify-content: center;
  }

  .table-demo-head > div,
  .table-demo-row > div,
  .table-demo-total > div {
    font-size: 12px;
    padding: 9px 10px;
  }
}

/* Inline Edit Styles */
.title-with-edit {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.title-with-edit h3 {
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
</style>