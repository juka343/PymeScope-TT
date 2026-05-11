<script setup>
import { useRoute } from "vue-router";
import { computed } from "vue";

const props = defineProps({
  // "mono" -> /dashboard
  // "multi" -> /dashboard-multi
  mode: { type: String, default: "mono" },
  mobileOpen: { type: Boolean, default: false },
});

const emit = defineEmits(["close"]);

const route = useRoute();

const projectId = computed(() => route.params.id_proyecto);

const base = computed(() => {
  const segment = props.mode === "multi" ? "dashboard-multi" : "dashboard";
  return `/proyecto/${projectId.value}/${segment}`;
});

const isActive = (section) => {
  return route.path.split("/").pop() === section;
};

function handleNavClick() {
  emit("close");
}
</script>

<template>
  <!-- Mobile overlay -->
  <Teleport to="body">
    <Transition name="sidebar-overlay-fade">
      <div
        v-if="mobileOpen"
        class="sidebar-overlay"
        @click="emit('close')"
      ></div>
    </Transition>
  </Teleport>

  <aside class="sidebar" :class="{ 'sidebar--mobile-open': mobileOpen }">
    <!-- Encabezado mobile -->
    <div class="sidebar-mobile-head">
      <span class="sidebar-mobile-title">Navegación</span>
      <button class="sidebar-mobile-close" @click="emit('close')">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <!-- RESUMEN -->
    <div class="side-section">
      <p class="side-title">RESUMEN RAZONES FINANCIERAS</p>

      <RouterLink
        :to="`${base}/resumen`"
        class="side-link"
        :class="{ active: isActive('resumen') }"
        @click="handleNavClick"
      >
        <span class="material-symbols-outlined">grid_view</span>
        <span>Resumen General</span>
      </RouterLink>
    </div>

    <!-- RAZONES FINANCIERAS -->
    <div class="side-section">
      <p class="side-title">RAZONES FINANCIERAS</p>

      <RouterLink
        :to="`${base}/rentabilidad`"
        class="side-link"
        :class="{ active: isActive('rentabilidad') }"
        @click="handleNavClick"
      >
        <span class="material-symbols-outlined">trending_up</span>
        <span>Rentabilidad</span>
      </RouterLink>

      <RouterLink
        :to="`${base}/liquidez`"
        class="side-link"
        :class="{ active: isActive('liquidez') }"
        @click="handleNavClick"
      >
        <span class="material-symbols-outlined">attach_money</span>
        <span>Liquidez</span>
      </RouterLink>

      <RouterLink
        :to="`${base}/endeudamiento`"
        class="side-link"
        :class="{ active: isActive('endeudamiento') }"
        @click="handleNavClick"
      >
        <span class="material-symbols-outlined">account_balance_wallet</span>
        <span>Endeudamiento</span>
      </RouterLink>

      <RouterLink
        :to="`${base}/rotacion`"
        class="side-link"
        :class="{ active: isActive('rotacion') }"
        @click="handleNavClick"
      >
        <span class="material-symbols-outlined">sync_alt</span>
        <span>Rotación de Activos</span>
      </RouterLink>

      <RouterLink
        :to="`${base}/estructura`"
        class="side-link"
        :class="{ active: isActive('estructura') }"
        @click="handleNavClick"
      >
        <span class="material-symbols-outlined">layers</span>
        <span>Estructura Financiera</span>
      </RouterLink>
    </div>

    <!-- PROYECCIONES -->
    <div class="side-section">
      <p class="side-title">PROYECCIONES PROFORMA</p>

      <RouterLink
        :to="`${base}/proyecciones`"
        class="side-link"
        :class="{ active: isActive('proyecciones') }"
        @click="handleNavClick"
      >
        <span class="material-symbols-outlined">bar_chart</span>
        <span>Proyecciones</span>
      </RouterLink>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 256px;
  background: #ffffff;
  border-right: 1px solid #e8eff3;
  padding: 16px;
  overflow-y: auto;
  display: none;
}

/* Mobile drawer */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
}

.sidebar--mobile-open {
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  width: 280px;
  box-shadow: 8px 0 30px rgba(0, 0, 0, 0.15);
  animation: slide-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slide-in {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

.sidebar-mobile-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0 16px;
  border-bottom: 1px solid #e8eff3;
  margin-bottom: 12px;
}

.sidebar-mobile-title {
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.sidebar-mobile-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  color: #507c95;
  display: flex;
  align-items: center;
}

.sidebar-mobile-close:hover {
  background: #f1f5f9;
  color: #0e161b;
}

/* Hide mobile head on desktop */
@media (min-width: 768px) {
  .sidebar-mobile-head {
    display: none;
  }
}

.side-section + .side-section {
  margin-top: 20px;
}

.side-title {
  margin: 0 0 10px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 900;
  color: #9bb0c1;
  letter-spacing: 0.08em;
}

.side-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  color: #507c95;
  text-decoration: none;
  font-weight: 800;
  font-size: 13px;
  transition: background 0.15s ease, color 0.15s ease;
}

.side-link .material-symbols-outlined {
  font-size: 20px;
}

.side-link:hover {
  background: #e8eff3;
  color: #0e161b;
}

.side-link.active {
  background: #299de0;
  color: white;
  box-shadow: 0 6px 14px rgba(41, 157, 224, 0.22);
}

@media (min-width: 768px) {
  .sidebar {
    display: block;
  }

  /* On desktop, never show mobile drawer state */
  .sidebar--mobile-open {
    position: static;
    width: 256px;
    box-shadow: none;
    animation: none;
  }
}

/* Transitions */
.sidebar-overlay-fade-enter-active,
.sidebar-overlay-fade-leave-active {
  transition: opacity 0.2s ease;
}
.sidebar-overlay-fade-enter-from,
.sidebar-overlay-fade-leave-to {
  opacity: 0;
}
</style>