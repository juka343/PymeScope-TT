<script setup>
import { RouterView } from "vue-router";
import DashboardTopbar from "@/components/app/DashboardTopbar.vue";
import DashboardSidebar from "@/components/app/DashboardSidebar.vue";
</script>

<template>
  <div class="dashboard-layout">
    <!-- TOPBAR -->
    <DashboardTopbar />

    <!-- BODY -->
    <div class="dashboard-body">
      <!-- SIDEBAR -->
      <DashboardSidebar />

      <!-- CONTENT -->
      <main class="dashboard-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.dashboard-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafb;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

/* BODY (Sidebar + Content) */
.dashboard-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* CONTENT */
.dashboard-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f8fafb;
}

/* Responsive */
@media (min-width: 768px) {
  .dashboard-content {
    padding: 28px 40px;
  }
}
</style>