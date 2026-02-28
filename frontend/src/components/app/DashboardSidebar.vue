<script setup>
import { useRoute } from "vue-router";
import { computed } from "vue";

const route = useRoute();

const projectId = computed(() => route.params.id_proyecto);

const isActive = (section) => {
  return route.path.endsWith(section);
};
</script>

<template>
  <aside class="sidebar">
    <!-- RESUMEN -->
    <div class="side-section">
      <p class="side-title">RESUMEN RAZONES FINANCIERAS</p>

      <RouterLink
        to="/app/resumen"
        class="side-link"
        :class="{ active: isActive('/app/resumen') }"
      >
        <span class="material-symbols-outlined">grid_view</span>
        <span>Resumen General</span>
      </RouterLink>
    </div>

    <!-- RAZONES FINANCIERAS -->
    <div class="side-section">
      <p class="side-title">RAZONES FINANCIERAS</p>

      <RouterLink
        :to="`/proyecto/${projectId}/dashboard/rentabilidad`"
        class="side-link"
        :class="{ active: isActive('rentabilidad') }"
      >
        <span class="material-symbols-outlined">trending_up</span>
        <span>Rentabilidad</span>
      </RouterLink>

      <RouterLink
        :to="`/proyecto/${projectId}/dashboard/liquidez`"
        class="side-link"
        :class="{ active: isActive('liquidez') }"
      >
        <span class="material-symbols-outlined">attach_money</span>
        <span>Liquidez</span>
      </RouterLink>

      <RouterLink
        :to="`/proyecto/${projectId}/dashboard/endeudamiento`"
        class="side-link"
        :class="{ active: isActive('endeudamiento') }"
      >
        <span class="material-symbols-outlined">account_balance_wallet</span>
        <span>Endeudamiento</span>
      </RouterLink>

      <RouterLink
        :to="`/proyecto/${projectId}/dashboard/rotacion`"
        class="side-link"
        :class="{ active: isActive('rotacion') }"
      >
        <span class="material-symbols-outlined">sync_alt</span>
        <span>Rotación de Activos</span>
      </RouterLink>

      <RouterLink
        :to="`/proyecto/${projectId}/dashboard/estructura`"
        class="side-link"
        :class="{ active: isActive('estructura') }"
      >
        <span class="material-symbols-outlined">layers</span>
        <span>Estructura Financiera</span>
      </RouterLink>
    </div>

    <!-- PROYECCIONES -->
    <div class="side-section">
      <p class="side-title">PROYECCIONES PROFORMA</p>

      <RouterLink
        to="/app/proyecciones"
        class="side-link"
        :class="{ active: isActive('/app/proyecciones') }"
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
}
</style>