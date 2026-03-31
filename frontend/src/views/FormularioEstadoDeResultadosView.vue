<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

function goToProyeccionProformaEdo() {
  router.push({ name: "ProyeccionProformaEdo" });
}

const projectConfig = ref({
  periodicidad: "Trimestral",
  periodoBase: "Q3 2024",
  periodoProyectado: "Q4 2024",
  inflacionEsperada: 4.5,
});

const periodOptions = ref([
  "Q4 2024",
  "Q1 2025",
  "Q2 2025",
  "Q3 2025",
  "Q4 2025",
]);

const ingresosRows = ref([
  {
    concepto: "Ventas netas / Ingresos por servicios",
    variacion: "",
    mantenerIgual: false,
  },
  {
    concepto: "Otros ingresos",
    variacion: "",
    mantenerIgual: false,
  },
  {
    concepto: "Productos financieros",
    variacion: "",
    mantenerIgual: false,
  },
]);

const costosRows = ref([
  {
    concepto: "Costo de ventas/Costo por servicios",
    subtitulo: "",
    variacion: "",
    mantenerIgual: false,
  },
  {
    concepto: "Gastos de venta",
    subtitulo: "",
    variacion: "",
    mantenerIgual: false,
  },
  {
    concepto: "Gastos de administración",
    subtitulo: "Operativos y administrativos",
    variacion: "",
    mantenerIgual: false,
  },
  {
    concepto: "Gastos de nómina",
    subtitulo: "Sueldos y salarios",
    variacion: "",
    mantenerIgual: false,
  },
  {
    concepto: "Gastos financieros",
    subtitulo: "Intereses y comisiones",
    variacion: "",
    mantenerIgual: false,
  },
  {
    concepto: "Otros gastos",
    subtitulo: "",
    variacion: "",
    mantenerIgual: false,
  },
]);

const impuestosRows = ref([
  {
    concepto: "ISR",
    variacion: "",
    mantenerIgual: false,
  },
  {
    concepto: "PTU (Participación de los Trabajadores en las Utilidades)",
    variacion: "",
    mantenerIgual: false,
  },
]);

function cancelar() {
  // Placeholder
}

function generarProyeccion() {
  // Placeholder
}
</script>

<template>
  <div class="wrap">
    <div class="page-head">
      <div class="page-head-top">
        <div>
          <h1>Supuestos Proforma – Estado de Resultados</h1>
          <p class="page-description">
            Define los supuestos para proyectar el estado de resultados a partir del último periodo disponible.
          </p>
        </div>

        <div class="info-badge">
          <span class="material-symbols-outlined">info</span>
          <span>Periodo base: Último periodo registrado</span>
        </div>
      </div>
    </div>

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon">settings</span>
        <h3>Configuración general de la proyección</h3>
      </div>

      <div class="config-grid">
        <div class="field">
          <label>Periodicidad del proyecto</label>
          <div class="readonly-box">{{ projectConfig.periodicidad }}</div>
        </div>

        <div class="field">
          <label>Periodo base</label>
          <div class="readonly-box">{{ projectConfig.periodoBase }}</div>
        </div>

        <div class="field">
          <label>Periodo a proyectar</label>
          <select v-model="projectConfig.periodoProyectado" class="input">
            <option v-for="periodo in periodOptions" :key="periodo" :value="periodo">
              {{ periodo }}
            </option>
          </select>
        </div>

        <div class="field">
          <label>Inflación esperada (%)</label>
          <div class="input-with-suffix">
            <input
              v-model="projectConfig.inflacionEsperada"
              class="input"
              type="number"
              step="0.1"
              placeholder="4.5"
            />
            <span class="suffix">%</span>
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon icon-green">trending_up</span>
        <h3>Supuestos por cuenta – Ingresos</h3>
      </div>

      <div class="assumptions-table">
        <div class="assumptions-head">
          <div class="col-concepto">Concepto</div>
          <div class="col-variacion center">Variación (%)</div>
          <div class="col-check right">Mantener igual</div>
        </div>

        <div
          v-for="(row, idx) in ingresosRows"
          :key="`ingreso-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ row.concepto }}</div>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="row.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="row.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon icon-red">trending_down</span>
        <h3>Supuestos por cuenta – Costos y gastos</h3>
      </div>

      <div class="assumptions-table">
        <div class="assumptions-head">
          <div class="col-concepto">Concepto</div>
          <div class="col-variacion center">Variación (%)</div>
          <div class="col-check right">Mantener igual</div>
        </div>

        <div
          v-for="(row, idx) in costosRows"
          :key="`costo-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ row.concepto }}</div>
            <p v-if="row.subtitulo" class="concept-sub">{{ row.subtitulo }}</p>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="row.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="row.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon icon-amber">account_balance</span>
        <h3>Impuestos</h3>
      </div>

      <div class="assumptions-table">
        <div class="assumptions-head">
          <div class="col-concepto">Concepto</div>
          <div class="col-variacion center">Variación (%)</div>
          <div class="col-check right">Mantener igual</div>
        </div>

        <div
          v-for="(row, idx) in impuestosRows"
          :key="`impuesto-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ row.concepto }}</div>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="row.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="row.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>
      </div>
    </section>

    <div class="actions">
      <button class="btn-secondary" type="button" @click="cancelar">
        Cancelar
      </button>

      <button class="btn-primary" type="button" @click="goToProyeccionProformaEdo">
        <span class="material-symbols-outlined">auto_graph</span>
        <span>Generar proyección proforma</span>
      </button>
    </div>

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
  width: min(1000px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Head */
.page-head {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8eff3;
}

.page-head-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.page-head h1 {
  margin: 0 0 8px;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
}

.page-description {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

.info-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1a8ac7;
  border: 1px solid #dbeafe;
  font-size: 12px;
  font-weight: 700;
}

.info-badge .material-symbols-outlined {
  font-size: 16px;
}

/* Cards */
.card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.section-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 900;
  color: #0e161b;
}

.section-icon {
  font-size: 22px;
  color: #299de0;
}

.icon-green {
  color: #16a34a;
}

.icon-red {
  color: #ef4444;
}

.icon-amber {
  color: #f59e0b;
}

/* Config grid */
.config-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field label {
  color: #0e161b;
  font-size: 14px;
  font-weight: 700;
}

.readonly-box {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid #e8eff3;
  background: #f8fafb;
  color: #507c95;
  font-size: 14px;
  font-weight: 700;
}

/* Inputs */
.input {
  width: 100%;
  height: 42px;
  border: 1px solid #d1dee6;
  border-radius: 10px;
  background: #ffffff;
  color: #0e161b;
  font-size: 14px;
  padding: 0 14px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.input:focus {
  border-color: #299de0;
  box-shadow: 0 0 0 3px rgba(41, 157, 224, 0.12);
}

.input-with-suffix {
  position: relative;
}

.input-with-suffix .input {
  padding-right: 36px;
}

.suffix {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 12px;
  font-weight: 700;
}

/* Assumptions table */
.assumptions-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.assumptions-head {
  display: none;
}

.assumptions-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  align-items: center;
  padding: 14px;
  border: 1px solid transparent;
  border-radius: 12px;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.assumptions-row:hover {
  background: #f8fafc;
  border-color: #f1f5f9;
}

.concept-text {
  color: #0e161b;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.5;
}

.concept-sub {
  margin: 3px 0 0;
  color: #94a3b8;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.check-wrap {
  display: flex;
  justify-content: flex-start;
}

.checkbox {
  width: 16px;
  height: 16px;
  accent-color: #299de0;
}

/* Actions */
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 14px;
  margin-top: 2px;
  border-top: 1px solid #e8eff3;
  flex-wrap: wrap;
}

.btn-secondary,
.btn-primary {
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  padding: 11px 18px;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.05s ease;
  cursor: pointer;
}

.btn-secondary {
  background: #ffffff;
  color: #0e161b;
  border: 1px solid #d1dee6;
}

.btn-secondary:hover {
  background: #f8fafb;
}

.btn-primary {
  border: none;
  background: #299de0;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.btn-primary:hover {
  background: #1a8ac7;
}

.btn-secondary:active,
.btn-primary:active {
  transform: translateY(1px);
}

.btn-primary .material-symbols-outlined {
  font-size: 18px;
}

/* Footer */
.foot {
  margin: 4px 0 22px;
  text-align: center;
  color: #9ca3af;
  font-weight: 700;
  font-size: 12px;
}

.foot p {
  margin: 0;
  line-height: 1.6;
}

/* Responsive */
@media (min-width: 768px) {
  .config-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .assumptions-head {
    display: grid;
    grid-template-columns: 6fr 3fr 3fr;
    gap: 16px;
    align-items: center;
    padding: 0 14px 4px;
    color: #94a3b8;
    font-size: 11px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .assumptions-row {
    grid-template-columns: 6fr 3fr 3fr;
    gap: 16px;
  }

  .center {
    text-align: center;
  }

  .right {
    text-align: right;
  }

  .check-wrap {
    justify-content: flex-end;
    padding-right: 14px;
  }
}

@media (min-width: 1200px) {
  .config-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>