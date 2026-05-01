<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useRouter, useRoute } from "vue-router";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { doc, getDoc, collection, getDocs } from "firebase/firestore";
import { auth, db } from "@/firebase/config";

const router = useRouter();
const route = useRoute();

// ====== USER ======
const user = ref(null);
let unsub = null;

const projectId = computed(() => route.params.id_proyecto);

onMounted(() => {
  unsub = onAuthStateChanged(auth, (u) => {
    user.value = u;
    if (!u) router.replace("/");
  });

  fetchProjectData(); // <-- Lanzamos la búsqueda al montar
});

onBeforeUnmount(() => {
  if (unsub) unsub();
});

const userDisplayName = computed(() => {
  if (!user.value) return "Usuario";
  return user.value.displayName || (user.value.email ? user.value.email.split("@")[0] : "Usuario");
});

const userEmail = computed(() => (user.value?.email ? user.value.email : ""));
const userPhotoURL = computed(() => user.value?.photoURL || "");

const userInitials = computed(() => {
  const name = userDisplayName.value?.trim();
  if (!name) return "U";
  if (name.includes("@")) return name[0].toUpperCase();
  const parts = name.split(" ").filter(Boolean);
  const initials = parts.slice(0, 2).map((p) => p[0]).join("");
  return (initials || name[0]).toUpperCase();
});

// ====== Proyecto Dinámico ======
const project = ref({
  name: "Cargando...",
  periodLabel: "...",
  mode: "...",
});

const fetchProjectData = async () => {
  if (!projectId.value) return;

  try {
    // 1. Obtener nombre del proyecto y modo
    const projectRef = doc(db, "proyectos", projectId.value);
    const projectSnap = await getDoc(projectRef);

    let pName = "Proyecto sin título";
    let pMode = "Monoperiodo";

    if (projectSnap.exists()) {
      pName = projectSnap.data().nombre || pName;
      const mode = projectSnap.data().analysis_mode;
      if (mode === 'multi') pMode = "Multiperiodo";
    }

    // 2. Obtener el periodo (como es monoperiodo, tomamos el primero)
    const periodosRef = collection(db, "proyectos", projectId.value, "periodos");
    const periodsSnap = await getDocs(periodosRef);

    let pLabel = "Sin periodo";
    if (!periodsSnap.empty) {
      // Obtenemos el nombre del mes/año que se guardó
      pLabel = periodsSnap.docs[0].data().label || "Periodo 1"; 
    }

    // 3. Inyectar datos a la vista
    project.value = {
      name: pName,
      periodLabel: pLabel,
      mode: pMode,
    };
  } catch (error) {
    console.error("Error cargando topbar:", error);
    project.value.name = "Error de conexión";
  }
};

const showUserMenu = ref(false);

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value;
}

function handleClickOutside(e) {
  const menu = document.querySelector('.user-dropdown-wrap');
  if (menu && !menu.contains(e.target)) {
    showUserMenu.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
});

async function handleLogout() {
  showUserMenu.value = false;
  try {
    await signOut(auth);
    router.replace("/login");
  } catch (e) {
    console.error("Error al cerrar sesión:", e);
  }
}

const emit = defineEmits(["toggle-sidebar"]);
</script>

<template>
  <header class="header">
    <div class="header-left">
      <button class="hamburger" type="button" @click="emit('toggle-sidebar')" aria-label="Abrir menú">
        <span class="material-symbols-outlined">menu</span>
      </button>

      <div class="brand">
        <div class="logo" aria-hidden="true">
          <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g clip-path="url(#clip0_6_543)">
              <path
                d="M42.1739 20.1739L27.8261 5.82609C29.1366 7.13663 28.3989 10.1876 26.2002 13.7654C24.8538 15.9564 22.9595 18.3449 20.6522 20.6522C18.3449 22.9595 15.9564 24.8538 13.7654 26.2002C10.1876 28.3989 7.13663 29.1366 5.82609 27.8261L20.1739 42.1739C21.4845 43.4845 24.5355 42.7467 28.1133 40.548C30.3042 39.2016 32.6927 37.3073 35 35C37.3073 32.6927 39.2016 30.3042 40.548 28.1133C42.7467 24.5355 43.4845 21.4845 42.1739 20.1739Z"
                fill="currentColor"
              />
            </g>
            <defs>
              <clipPath id="clip0_6_543">
                <rect width="48" height="48" fill="white" />
              </clipPath>
            </defs>
          </svg>
        </div>
        <h2 class="brand-name">PymeScope</h2>
      </div>

      <div class="project-pill">
        <span class="pill-title">{{ project.name }}</span>

        <span class="pill-divider" aria-hidden="true"></span>

        <span class="pill-meta">
          <span class="material-symbols-outlined">calendar_month</span>
          {{ project.periodLabel }}
        </span>

        <span class="pill-divider" aria-hidden="true"></span>

        <span class="pill-meta">
          <span class="material-symbols-outlined">update</span>
          {{ project.mode }}
        </span>
      </div>
    </div>

    <div class="header-right">
        <div class="actions">
          <RouterLink class="back" to="/misProyectos">
            <span class="material-symbols-outlined">arrow_back</span>
            <span class="back-text">Volver a proyectos</span>
          </RouterLink>
        </div>
      
      <button 
        class="btn-secondary" 
        type="button"
        @click="router.push(`/proyecto/${route.params.id_proyecto}/cargar`)"
      >
        <span class="material-symbols-outlined">edit</span>
        <span class="btn-text">Editar proyecto</span>
      </button>

      <!-- Avatar con dropdown -->
      <div class="user-dropdown-wrap">
        <button class="avatar-btn" type="button" @click.stop="toggleUserMenu">
          <div
            class="avatar"
            :style="userPhotoURL ? { backgroundImage: `url('${userPhotoURL}')` } : {}"
          >
            <span v-if="!userPhotoURL">{{ userInitials }}</span>
          </div>
        </button>

        <Transition name="dropdown">
          <div v-if="showUserMenu" class="user-dropdown">
            <div class="dropdown-header">
              <div
                class="dropdown-avatar"
                :style="userPhotoURL ? { backgroundImage: `url('${userPhotoURL}')` } : {}"
              >
                <span v-if="!userPhotoURL">{{ userInitials }}</span>
              </div>
              <div class="dropdown-info">
                <p class="dropdown-name">{{ userDisplayName }}</p>
                <p class="dropdown-email" v-if="userEmail">{{ userEmail }}</p>
              </div>
            </div>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item dropdown-logout" @click="handleLogout">
              <span class="material-symbols-outlined">logout</span>
              Cerrar sesión
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #ffffff;
  border-bottom: 1px solid #e8eff3;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  overflow: hidden;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--primary);
  font-weight: 800;
  font-size: 14px;
  white-space: nowrap;
}
.back:hover {
  color: var(--primary-dark);
}
.back span.material-symbols-outlined {
  font-size: 20px;
}


.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 32px;
  height: 32px;
  color: #299de0;
  display: grid;
  place-items: center;
}

.brand-name {
  margin: 0;
  font-weight: 900;
  font-size: 20px;
  display: none;
}

.btn-text {
  display: none;
}

.project-pill {
  display: none;
  align-items: center;
  gap: 12px;
  border: 1px solid #e8eff3;
  background: #f8fafb;
  padding: 6px 14px;
  border-radius: 999px;
}

.pill-title {
  font-size: 13px;
  font-weight: 800;
}

.pill-divider {
  width: 1px;
  height: 16px;
  background: #d1d5db;
}

.pill-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #507c95;
}

.pill-meta .material-symbols-outlined {
  font-size: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 10px;
  border-radius: 10px;
  border: 1px solid #d1dee6;
  background: transparent;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}

.btn-secondary:hover {
  background: #f8fafb;
}

.avatar-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: rgba(41, 157, 224, 0.1);
  color: #299de0;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 12px;

  background-size: cover;
  background-position: center;
}

@media (min-width: 480px) {
  .brand-name {
    display: block;
  }
  .header {
    padding: 12px 16px;
    gap: 16px;
  }
  .header-left {
    gap: 14px;
  }
  .header-right {
    gap: 10px;
  }
}

@media (min-width: 640px) {
  .btn-text {
    display: inline;
  }
  .btn-secondary {
    padding: 0 14px;
  }
  .header {
    padding: 12px 24px;
  }
  .header-left {
    gap: 18px;
  }
  .header-right {
    gap: 12px;
  }
}

@media (min-width: 1024px) {
  .project-pill {
    display: inline-flex;
  }
}

.hamburger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: transparent;
  border: 1px solid #e8eff3;
  cursor: pointer;
  color: #507c95;
  flex-shrink: 0;
}
.hamburger:hover {
  background: #f1f5f9;
  color: #0e161b;
}
.hamburger .material-symbols-outlined {
  font-size: 22px;
}

@media (min-width: 768px) {
  .hamburger {
    display: none;
  }
}

/* User dropdown */
.user-dropdown-wrap {
  position: relative;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 260px;
  background: #fff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  z-index: 50;
  overflow: hidden;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.dropdown-avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: rgba(41, 157, 224, 0.1);
  color: #299de0;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 14px;
  flex-shrink: 0;
  background-size: cover;
  background-position: center;
}

.dropdown-info {
  min-width: 0;
}

.dropdown-name {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: #0e161b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-email {
  margin: 2px 0 0;
  font-size: 12px;
  color: #507c95;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-divider {
  height: 1px;
  background: #e8eff3;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease;
}

.dropdown-logout {
  color: #ef4444;
}

.dropdown-logout:hover {
  background: #fef2f2;
}

.dropdown-logout .material-symbols-outlined {
  font-size: 20px;
}

/* Dropdown transitions */
.dropdown-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-6px) scale(0.96);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
