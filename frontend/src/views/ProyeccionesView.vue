<script setup>
import { ref } from "vue";

const cards = ref([
  {
    id: "er",
    icon: "query_stats",
    title: "Estado de Resultados Proforma",
    desc: "Proyecta ingresos, costos y gastos a partir de supuestos definidos cuenta por cuenta.",
    button: "Configurar proyección",
  },
  {
    id: "bg",
    icon: "balance",
    title: "Balance General Proforma",
    desc: "Proyecta la estructura financiera futura considerando activos, pasivos y capital.",
    button: "Configurar proyección",
  },
]);

function handleConfigure(id) {
  console.log("Configurar proyección:", id);
}
</script>

<template>
  <div class="wrap">
    <div class="title">
      <h1>Proyecciones financieras</h1>
      <div class="subtitle">
        <p>Genera proyecciones proforma a partir del último periodo disponible</p>
      </div>
    </div>

    <section class="grid">
      <article v-for="c in cards" :key="c.id" class="card">
        <div class="card-top">
          <div class="icon-box" aria-hidden="true">
            <span class="material-symbols-outlined">{{ c.icon }}</span>
          </div>
        </div>

        <h3 class="card-title">{{ c.title }}</h3>
        <p class="card-desc">{{ c.desc }}</p>

        <div class="card-foot">
          <div class="pill">
            <span class="material-symbols-outlined">calendar_today</span>
            <span>Periodo base: último periodo disponible</span>
          </div>

          <button class="btn-primary" type="button" @click="handleConfigure(c.id)">
            <span>{{ c.button }}</span>
            <span class="material-symbols-outlined">arrow_forward</span>
          </button>
        </div>
      </article>
    </section>

    <footer class="foot">
      <p>
        Todos los datos son confidenciales. <br />
        Las proyecciones son estimaciones basadas en los supuestos ingresados y no garantizan resultados futuros.
      </p>
    </footer>
  </div>
</template>

<style scoped>
.wrap {
  width: min(1200px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
  color: #0e161b;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

/* Title */
.title h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
}

.subtitle {
  margin-top: 6px;
  color: #507c95;
  font-weight: 700;
  font-size: 13px;
}

/* Grid */
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  margin-top: 6px;
}

.card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.15s ease, transform 0.05s ease;
  display: flex;
  flex-direction: column;
  min-height: 260px;
}

.card:hover {
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.icon-box {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  color: #299de0;
  display: grid;
  place-items: center;
}

.icon-box span {
  font-size: 32px;
}

.card-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 900;
  transition: color 0.15s ease;
}

.card:hover .card-title {
  color: #299de0;
}

.card-desc {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  line-height: 1.6;
  font-weight: 700;
  flex: 1;
}

/* Footer inside card */
.card-foot {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid #e8eff3;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #507c95;
  font-size: 12px;
  font-weight: 800;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 10px;
  padding: 8px 10px;
  width: fit-content;
}

.pill .material-symbols-outlined {
  font-size: 16px;
  opacity: 0.85;
  color: #507c95;
}

/* Button */
.btn-primary {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  background: #299de0;
  color: white;
  font-weight: 900;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 10px 22px rgba(41, 157, 224, 0.2);
  transition: filter 0.15s ease, transform 0.05s ease;
}

.btn-primary:hover {
  filter: brightness(0.95);
}

.btn-primary:active {
  transform: translateY(1px);
}

.btn-primary .material-symbols-outlined {
  font-size: 18px;
}

/* Footer */
.foot {
  margin: 8px 0 22px;
  text-align: center;
  color: #9ca3af;
  font-weight: 700;
  font-size: 12px;
}

/* Responsive */
@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
}
</style>