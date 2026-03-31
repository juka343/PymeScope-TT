<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const estadoResultadosDisponible = ref(true);
const balanceDisponible = ref(false);

function configurarEstadoResultados() {
  // Placeholder
}

function configurarBalance() {
  if (!balanceDisponible.value) return;
  // Placeholder
}

function goToFormularioEstadoResultados() {
  router.push({ name: "FormularioEstadoDeResultados" });
}
</script>

<template>
  <div class="wrap">
    <div class="title">
      <h1>Proyecciones financieras</h1>
      <div class="subtitle">
        <p>
          Genera proyecciones proforma a partir del último periodo disponible
          <span class="separator">•</span>
          Genera primero el Estado de Resultados Proforma y después el Balance General Proforma.
        </p>
      </div>
    </div>

    <section class="projection-flow">
      <article class="projection-card">
        <div class="card-icon-row">
          <div class="card-icon">
            <span class="material-symbols-outlined">query_stats</span>
          </div>
        </div>

        <h3>Estado de Resultados Proforma</h3>
        <p class="card-text">
          Proyecta ingresos, costos y gastos a partir de supuestos definidos cuenta por cuenta.
        </p>

        <div class="card-footer">
          <div class="period-badge">
            <span class="material-symbols-outlined">calendar_today</span>
            <span>Periodo base: último periodo disponible</span>
          </div>

          <button
            class="btn-primary"
            type="button"
            :disabled="!estadoResultadosDisponible"
            @click="goToFormularioEstadoResultados"
          >
            <span>Configurar proyección</span>
            <span class="material-symbols-outlined">arrow_forward</span>
          </button>
        </div>
      </article>

      <div class="connector connector-desktop" aria-hidden="true">
        <div class="connector-circle">
          <span class="material-symbols-outlined">arrow_forward</span>
        </div>
        <div class="connector-line"></div>
      </div>

      <div class="connector connector-mobile" aria-hidden="true">
        <div class="connector-circle">
          <span class="material-symbols-outlined">arrow_downward</span>
        </div>
      </div>

      <article class="projection-card projection-card-disabled">
        <div class="card-icon-row">
          <div class="card-icon">
            <span class="material-symbols-outlined">balance</span>
          </div>
        </div>

        <h3>Balance General Proforma</h3>
        <p class="card-text">
          Proyecta la estructura financiera futura considerando activos, pasivos y capital.
        </p>

        <div class="card-footer">
          <div class="period-badge">
            <span class="material-symbols-outlined">calendar_today</span>
            <span>Periodo base: último periodo disponible</span>
          </div>

          <p class="availability-note">
            Disponible después de generar el Estado de Resultados Proforma
          </p>

          <button
            class="btn-primary btn-disabled"
            type="button"
            :disabled="!balanceDisponible"
            @click="configurarBalance"
          >
            <span>Configurar proyección</span>
            <span class="material-symbols-outlined">arrow_forward</span>
          </button>
        </div>
      </article>
    </section>

    <footer class="foot">
      <p>
        Todos los datos son confidenciales.<br />
        Las proyecciones son estimaciones basadas en los supuestos ingresados y no garantizan resultados futuros.
      </p>
    </footer>
  </div>
</template>

<style scoped>
.wrap {
  width: min(1200px, 100%);
  margin: 0 auto;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Title */
.title {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
}

.subtitle {
  color: #507c95;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

.subtitle p {
  margin: 0;
}

.separator {
  color: #d1d5db;
  margin: 0 6px;
}

/* Flow */
.projection-flow {
  position: relative;
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin-top: 4px;
}

/* Cards */
.projection-card {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 28px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.18s ease, transform 0.08s ease;
}

.projection-card:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.projection-card-disabled {
  opacity: 0.6;
  pointer-events: none;
  user-select: none;
}

.card-icon-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: #eff6ff;
  color: #299de0;
  border: 1px solid #dbeafe;
  display: grid;
  place-items: center;
}

.card-icon .material-symbols-outlined {
  font-size: 32px;
}

.projection-card h3 {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 900;
  color: #0e161b;
  transition: color 0.15s ease;
}

.projection-card:hover h3 {
  color: #299de0;
}

.card-text {
  margin: 0 0 24px;
  flex-grow: 1;
  color: #507c95;
  font-size: 14px;
  line-height: 1.7;
}

.card-footer {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid #e8eff3;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.period-badge {
  width: fit-content;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  background: #f8fafb;
  border: 1px solid #f1f5f9;
  color: #507c95;
  font-size: 12px;
  font-weight: 700;
}

.period-badge .material-symbols-outlined {
  font-size: 16px;
}

.availability-note {
  margin: 0;
  color: #299de0;
  font-size: 14px;
  font-weight: 900;
  line-height: 1.5;
}

/* Buttons */
.btn-primary {
  width: 100%;
  border: none;
  border-radius: 10px;
  background: #299de0;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  padding: 12px 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  transition: background 0.15s ease, transform 0.05s ease;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: #1a8ac7;
}

.btn-primary:active:not(:disabled) {
  transform: translateY(1px);
}

.btn-primary .material-symbols-outlined {
  font-size: 18px;
}

.btn-primary:disabled,
.btn-disabled {
  background: #d1d5db;
  color: #6b7280;
  box-shadow: none;
  cursor: not-allowed;
}

/* Connectors */
.connector {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.connector-desktop {
  display: none;
}

.connector-mobile {
  padding: 2px 0;
}

.connector-circle {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: #ffffff;
  border: 2px solid rgba(41, 157, 224, 0.2);
  color: #299de0;
  display: grid;
  place-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.connector-circle .material-symbols-outlined {
  font-size: 28px;
}

.connector-line {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  transform: translateX(-50%);
  background: linear-gradient(
    to bottom,
    rgba(41, 157, 224, 0),
    rgba(41, 157, 224, 0.12),
    rgba(41, 157, 224, 0)
  );
  z-index: -1;
}

/* Footer */
.foot {
  margin: auto 0 22px;
  text-align: center;
  color: #9ca3af;
  font-weight: 700;
  font-size: 12px;
  padding-top: 8px;
}

.foot p {
  margin: 0;
  line-height: 1.6;
}

/* Responsive */
@media (min-width: 768px) {
  .projection-flow {
    grid-template-columns: 1fr auto 1fr;
    align-items: stretch;
    gap: 24px;
  }

  .connector-desktop {
    display: flex;
    margin: 0 -12px;
  }

  .connector-mobile {
    display: none;
  }

  .connector-circle {
    width: 48px;
    height: 48px;
  }

  .connector-circle .material-symbols-outlined {
    font-size: 32px;
  }
}
</style>