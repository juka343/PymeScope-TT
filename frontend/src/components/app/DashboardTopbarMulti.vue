<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { getAuth, onAuthStateChanged, signOut } from "firebase/auth";

const route = useRoute();
const router = useRouter();
const auth = getAuth();

const user = ref(null);

// Mock (luego lo conectas a Firestore por projectId)
const project = ref({
  name: "Análisis trimestral 2024",
  rangeLabel: "Q1 - Q3 2024",
  periodicityLabel: "Trimestral",
  basePeriodLabel: "Q2 2024",
});

const projectId = computed(() => route.params.id_proyecto);

onMounted(() => {
  onAuthStateChanged(auth, (u) => {
    user.value = u;
  });
});

const userDisplayName = computed(() => {
  if (!user.value) return "";
  return user.value.displayName || user.value.email || "";
});

const userInitials = computed(() => {
  const name = userDisplayName.value || "U";
  const parts = name.split(" ").filter(Boolean);
  const initials = (parts[0]?.[0] || "U") + (parts[1]?.[0] || "");
  return initials.toUpperCase().slice(0, 2);
});

async function handleLogout() {
  await signOut(auth);
  router.push("/");
}
</script>

<template>
  <header class="header">
    <div class="left">
      <div class="brand">
        <div class="logo" aria-hidden="true">
          <svg class="logo-svg" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
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

      <!-- Pill multi -->
      <div class="pill">
        <span class="pill-title">{{ project.name }}</span>

        <span class="sep" aria-hidden="true"></span>

        <span class="pill-meta">
          <span class="material-symbols-outlined">calendar_month</span>
          {{ project.rangeLabel }}
        </span>

        <span class="sep" aria-hidden="true"></span>

        <span class="pill-meta">
          <span class="material-symbols-outlined">update</span>
          {{ project.periodicityLabel }}
        </span>

        <span class="sep" aria-hidden="true"></span>

        <span class="base-tag">
          <span class="base-text">Periodo Base: {{ project.basePeriodLabel }}</span>
        </span>
      </div>
    </div>

    <div class="right">
      <RouterLink class="btn btn-back" :to="`/misProyectos`">
        <span class="material-symbols-outlined">arrow_back</span>
        <span class="btn-text">Volver a proyectos</span>
      </RouterLink>

      <button class="btn" type="button">
        <span class="material-symbols-outlined">edit</span>
        <span>Editar proyecto</span>
      </button>

      <button class="avatar-btn" type="button" @click="handleLogout" title="Cerrar sesión">
        <div class="avatar">{{ userInitials }}</div>
      </button>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e8eff3;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  white-space: nowrap;
}

.left {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
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

.logo-svg {
  width: 100%;
  height: 100%;
}

.brand-name {
  margin: 0;
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.015em;
  color: #0e161b;
}

/* Pill */
.pill {
  display: none;
  align-items: center;
  gap: 14px;
  padding: 6px 14px;
  border-radius: 999px;
  background: #f8fafb;
  border: 1px solid #e8eff3;
  min-width: 0;
}

.pill-title {
  font-size: 13px;
  font-weight: 800;
  color: #0e161b;
}

.sep {
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

.base-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 8px;
  background: #eff6ff;
  border: 1px solid #dbeafe;
}

.base-text {
  font-size: 10px;
  font-weight: 900;
  color: #2563eb;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* Right */
.right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid #d1dee6;
  background: transparent;
  color: #0e161b;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}

.btn:hover {
  background: #f8fafb;
  border-color: #299de0;
}

.btn .material-symbols-outlined {
  font-size: 18px;
}

.btn-back {
  color: #299de0;
}

.btn-text {
  display: none;
}

.avatar-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: rgba(41, 157, 224, 0.1);
  color: #299de0;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 12px;
}

/* Responsive */
@media (min-width: 640px) {
  .btn-text {
    display: inline;
  }
}

@media (min-width: 1024px) {
  .pill {
    display: inline-flex;
  }
}
</style>