<script setup>
import { onBeforeUnmount, onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";

import { auth, db } from "@/firebase/config";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { collection, doc, setDoc, getDocs, query, where, orderBy, serverTimestamp } from "firebase/firestore";

const router = useRouter();

// ====== AUTH UI ======
const user = ref(null);
const authUnsub = ref(null);

const userDisplayName = computed(() => {
  if (!user.value) return "Usuario";
  return user.value.displayName || (user.value.email ? user.value.email.split("@")[0] : "Usuario");
});

const userEmail = computed(() => (user.value?.email ? user.value.email : ""));
const userRole = computed(() => "Usuario"); 
const userPhotoURL = computed(() => user.value?.photoURL || ""); // si alguien ve esto, las fotos solo funcioan con google xdddd

onMounted(() => {
  authUnsub.value = onAuthStateChanged(auth, async (u) => {
    user.value = u;

    if (!u) {
      router.replace("/"); // sin sesión, fuera
    } else {
      // Cargar proyectos cuando hay usuario autenticado
      await loadUserProjects();
    }
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
    router.replace("/"); // landing
  } catch (e) {
    console.error("Error al cerrar sesión:", e);
  }
}

//  MODAL 
const isModalOpen = ref(false);

// Form (solo UI)
const projectName = ref("");
const periodicity = ref("monthly"); // 
const companyName = ref("");
const notes = ref("");

function openModal() {
  isModalOpen.value = true;
}
function closeModal() {
  isModalOpen.value = false;
}
function resetForm() {
  projectName.value = "";
  periodicity.value = "monthly";
  companyName.value = "";
  notes.value = "";
}
function handleCancel() {
  closeModal();
}
const creating = ref(false);

async function handleCreate() {
  const currentUser = auth.currentUser;
  if (!currentUser) {
    alert("Debes iniciar sesión para crear un proyecto");
    return;
  }

  if (!projectName.value.trim()) {
    alert("El nombre del proyecto es obligatorio");
    return;
  }

  creating.value = true;

  try {
    // Generar ID único para el proyecto
    const projectId = crypto.randomUUID();
    const projectRef = doc(db, "proyectos", projectId);

    // Guardar en Firestore con userId para filtrado personal
    await setDoc(projectRef, {
      nombre: projectName.value.trim(),
      empresa: companyName.value.trim() || null,
      periodicidad: periodicity.value,
      notas: notes.value.trim() || null,
      userId: currentUser.uid, // Para que solo el dueño pueda verlo
      status: "en_edicion", //Este campo se actualizará a "completo" cuando el análisis esté listo.
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    });

    closeModal();
    resetForm();

    // Redirigir a la vista de carga de documentos
    router.push(`/proyecto/${projectId}/cargar`);
  } catch (error) {
    console.error("Error creando proyecto:", error);
    alert("Error al crear el proyecto. Intenta de nuevo.");
  } finally {
    creating.value = false;
  }
}

function onKeydown(e) {
  if (e.key === "Escape" && isModalOpen.value) closeModal();
}

//  PROYECTOS
const projects = ref([]);
const loadingProjects = ref(true);

// Cargar proyectos del usuario desde Firestore
async function loadUserProjects() {
  const currentUser = auth.currentUser;
  if (!currentUser) return;

  loadingProjects.value = true;
  try {
    const projectsRef = collection(db, "proyectos");
    // Query simple sin orderBy (evita necesidad de índice compuesto)
    const q = query(
      projectsRef,
      where("userId", "==", currentUser.uid)
    );
    const snapshot = await getDocs(q);
    
    const projectsList = snapshot.docs.map((doc) => {
      const data = doc.data();
      return {
        id: doc.id,
        title: data.nombre || "Sin título",
        status: data.status || "en_edicion", // Por ahora, asumimos que el proyecto se crea en estado "en edición".
        company: data.empresa || "Sin empresa",
        periods: data.periodicidad || "Sin periodicidad",
        createdAt: data.createdAt?.toDate?.() || new Date(0),
        modified: data.createdAt?.toDate?.()?.toLocaleDateString("es-MX", {
          day: "numeric",
          month: "short",
          year: "numeric",
        }) || "Sin fecha",
      };
    });

    // Ordenar en el cliente (más recientes primero)
    projectsList.sort((a, b) => b.createdAt - a.createdAt);
    projects.value = projectsList;
  } catch (error) {
    console.error("Error cargando proyectos:", error);
  } finally {
    loadingProjects.value = false;
  }
}

function removeProject(id) {
  projects.value = projects.value.filter((p) => p.id !== id);
}
</script>

<template>
  <div class="page">
    <header class="header">
      <div class="container header-inner">
        <div class="brand">
          <div class="logo" aria-hidden="true">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M42.1739 20.1739L27.8261 5.82609C29.1366 7.13663 28.3989 10.1876 26.2002 13.7654C24.8538 15.9564 22.9595 18.3449 20.6522 20.6522C18.3449 22.9595 15.9564 24.8538 13.7654 26.2002C10.1876 28.3989 7.13663 29.1366 5.82609 27.8261L20.1739 42.1739C21.4845 43.4845 24.5355 42.7467 28.1133 40.548C30.3042 39.2016 32.6927 37.3073 35 35C37.3073 32.6927 39.2016 30.3042 40.548 28.1133C42.7467 24.5355 43.4845 21.4845 42.1739 20.1739Z"
                fill="currentColor"
              />
              <path
                fill-rule="evenodd"
                clip-rule="evenodd"
                d="M7.24189 26.4066C7.31369 26.4411 7.64204 26.5637 8.52504 26.3738C9.59462 26.1438 11.0343 25.5311 12.7183 24.4963C14.7583 23.2426 17.0256 21.4503 19.238 19.238C21.4503 17.0256 23.2426 14.7583 24.4963 12.7183C25.5311 11.0343 26.1438 9.59463 26.3738 8.52504C26.5637 7.64204 26.4411 7.31369 26.4066 7.24189C26.345 7.21246 26.143 7.14535 25.6664 7.1918C24.9745 7.25925 23.9954 7.5498 22.7699 8.14278C20.3369 9.32007 17.3369 11.4915 14.4142 14.4142C11.4915 17.3369 9.32007 20.3369 8.14278 22.7699C7.5498 23.9954 7.25925 24.9745 7.1918 25.6664C7.14534 26.143 7.21246 26.345 7.24189 26.4066ZM29.9001 10.7285C29.4519 12.0322 28.7617 13.4172 27.9042 14.8126C26.465 17.1544 24.4686 19.6641 22.0664 22.0664C19.6641 24.4686 17.1544 26.465 14.8126 27.9042C13.4172 28.7617 12.0322 29.4519 10.7285 29.9001L21.5754 40.747C21.6001 40.7606 21.8995 40.931 22.8729 40.7217C23.9424 40.4916 25.3821 39.879 27.0661 38.8441C29.1062 37.5904 31.3734 35.7982 33.5858 33.5858C35.7982 31.3734 37.5904 29.1062 38.8441 27.0661C39.879 25.3821 40.4916 23.9425 40.7216 22.8729C40.931 21.8995 40.7606 21.6001 40.747 21.5754L29.9001 10.7285ZM29.2403 4.41187L43.5881 18.7597C44.9757 20.1473 44.9743 22.1235 44.6322 23.7139C44.2714 25.3919 43.4158 27.2666 42.252 29.1604C40.8128 31.5022 38.8165 34.012 36.4142 36.4142C34.012 38.8165 31.5022 40.8128 29.1604 42.252C27.2666 43.4158 25.3919 44.2714 23.7139 44.6322C22.1235 44.9743 20.1473 44.9757 18.7597 43.5881L4.41187 29.2403C3.29027 28.1187 3.08209 26.5973 3.21067 25.2783C3.34099 23.9415 3.8369 22.4852 4.54214 21.0277C5.96129 18.0948 8.43335 14.7382 11.5858 11.5858C14.7382 8.43335 18.0948 5.9613 21.0277 4.54214C22.4852 3.8369 23.9415 3.34099 25.2783 3.21067C26.5973 3.08209 28.1187 3.29028 29.2403 4.41187Z"
                fill="currentColor"
              />
            </svg>
          </div>
          <h1 class="brand-name">PymeScope</h1>
        </div>

        <div class="user">
          <!-- Avatar real (si hay foto), si no, círculo gris -->
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
            <h3>{{ p.title }}</h3>

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
              <button class="icon-btn" type="button" title="Editar proyecto">
                <span class="material-symbols-outlined">edit</span>
              </button>

              <button
                class="icon-btn danger"
                type="button"
                title="Eliminar proyecto"
                @click="removeProject(p.id)"
              >
                <span class="material-symbols-outlined">delete</span>
              </button>

              <a class="link" href="#">
                Ver análisis
                <span class="material-symbols-outlined">arrow_forward</span>
              </a>
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

    <!-- MODAL -->
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
                required
              />
              <small>Este nombre te ayudará a identificar tu análisis</small>
            </div>

            <div class="field">
              <span class="label">Periodicidad del análisis <span class="req">*</span></span>

              <div class="radio-grid">
                <label class="radio">
                  <input v-model="periodicity" type="radio" value="monthly" />
                  <span>Mensual</span>
                </label>

                <label class="radio">
                  <input v-model="periodicity" type="radio" value="quarterly" />
                  <span>Trimestral</span>
                </label>

                <label class="radio">
                  <input v-model="periodicity" type="radio" value="annual" />
                  <span>Anual</span>
                </label>
              </div>

              <small>La periodicidad no podrá cambiarse una vez creado el proyecto</small>
            </div>

            <div class="field">
              <label for="company-name">
                Nombre de la empresa <span class="opt">(opcional)</span>
              </label>
              <input
                id="company-name"
                v-model.trim="companyName"
                type="text"
                placeholder="Ej. Pyme Comercial S.A. de C.V."
              />
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
              {{ creating ? 'Creando...' : 'Crear proyecto y continuar' }}
            </button>
            <button class="btn-secondary" type="button" @click="handleCancel" :disabled="creating">
              Cancelar
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
}

.btn-primary:hover {
  filter: brightness(0.95);
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

.link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--primary);
  font-weight: 900;
  font-size: 14px;
  text-decoration: none;
}
.link span {
  font-size: 18px;
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

/* Modal */
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

/* Form */
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

/* radios */
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
}

.btn-secondary:hover {
  background: #f8fafc;
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
</style>
