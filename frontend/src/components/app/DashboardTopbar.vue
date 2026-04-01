<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useRouter, useRoute } from "vue-router";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { doc, getDoc, collection, getDocs } from "firebase/firestore"; // <-- Importado
import { auth, db } from "@/firebase/config"; // <-- Asegúrate de importar db

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

async function handleLogout() {
  try {
    await signOut(auth);
    router.replace("/");
  } catch (e) {
    console.error("Error al cerrar sesión:", e);
  }
}
</script>

<template>
  <header class="header">
    <div class="header-left">
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
        Editar proyecto
      </button>

      <!-- Avatar: si hay foto, úsala. Si no, iniciales -->
      <button class="avatar-btn" type="button" @click="handleLogout" title="Cerrar sesión">
        <div
          class="avatar"
          :style="userPhotoURL ? { backgroundImage: `url('${userPhotoURL}')` } : {}"
        >
          <span v-if="!userPhotoURL">{{ userInitials }}</span>
        </div>
      </button>

      <!--  mostrar texto (opcional) -->
      <!--
      <div class="user-text">
        <div class="user-name">{{ userDisplayName }}</div>
        <div class="user-email" v-if="userEmail">{{ userEmail }}</div>
      </div>
      -->
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
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
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
  gap: 12px;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid #d1dee6;
  background: transparent;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
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

@media (min-width: 1024px) {
  .project-pill {
    display: inline-flex;
  }
}
</style>
