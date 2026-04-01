<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

function goToProyeccionProformaBalance() {
  router.push({ name: "ProyeccionProformaBalanceGeneral" });
}

const projectConfig = ref({
  periodicidad: "Trimestral",
  periodoBase: "Q3 2024",
  periodoProyectado: "Q4 2024",
  inflacionEsperada: 4.5,
});

const activoCirculante = ref([
  { concepto: "Caja", variacion: "", mantenerIgual: false },
  { concepto: "Bancos", variacion: "", mantenerIgual: false },
  { concepto: "Inversiones temporales", variacion: "", mantenerIgual: false },
  { concepto: "Cuentas por cobrar a clientes", variacion: "", mantenerIgual: false },
  { concepto: "Otras cuentas por cobrar (deudores diversos)", variacion: "", mantenerIgual: false },
  { concepto: "IVA por acreditar", variacion: "", mantenerIgual: false },
  { concepto: "IVA acreditable", variacion: "", mantenerIgual: false },
  { concepto: "Inventarios", variacion: "", mantenerIgual: false },
  { concepto: "Anticipo a proveedores", variacion: "", mantenerIgual: false },
  { concepto: "Papelería y artículos de escritorio", variacion: "", mantenerIgual: false },
  { concepto: "Propaganda y publicidad", variacion: "", mantenerIgual: false },
  { concepto: "Seguros y fianzas", variacion: "", mantenerIgual: false },
  { concepto: "Rentas pagadas por anticipado", variacion: "", mantenerIgual: false },
  { concepto: "Intereses pagados por anticipado", variacion: "", mantenerIgual: false },
  { concepto: "Impuestos y derechos", variacion: "", mantenerIgual: false },
]);

const activoNoCirculante = ref([
  { concepto: "Terrenos", variacion: "", mantenerIgual: false },
  { concepto: "Edificios", variacion: "", mantenerIgual: false },
  { concepto: "Maquinaria y equipo", variacion: "", mantenerIgual: false },
  { concepto: "Equipo de transporte", variacion: "", mantenerIgual: false },
  { concepto: "Mobiliario y equipo de oficina", variacion: "", mantenerIgual: false },
  { concepto: "Equipo de cómputo", variacion: "", mantenerIgual: false },
  { concepto: "Patentes", variacion: "", mantenerIgual: false },
  { concepto: "Marcas", variacion: "", mantenerIgual: false },
  { concepto: "Crédito mercantil", variacion: "", mantenerIgual: false },
  { concepto: "Franquicias", variacion: "", mantenerIgual: false },
  { concepto: "Licencias de software", variacion: "", mantenerIgual: false },
  { concepto: "Depósitos en garantía", variacion: "", mantenerIgual: false },
]);

const pasivoCorto = ref([
  { concepto: "Cuentas por pagar a proveedores", variacion: "", mantenerIgual: false },
  { concepto: "Préstamo bancario / Deuda a corto plazo", variacion: "", mantenerIgual: false },
  { concepto: "Acreedores diversos", variacion: "", mantenerIgual: false },
  { concepto: "Impuestos a la utilidad por pagar", variacion: "", mantenerIgual: false },
  { concepto: "IVA por causar o trasladar", variacion: "", mantenerIgual: false },
  { concepto: "IVA causado o trasladado", variacion: "", mantenerIgual: false },
  { concepto: "Anticipo de clientes", variacion: "", mantenerIgual: false },
  { concepto: "Rentas cobradas por anticipado", variacion: "", mantenerIgual: false },
  { concepto: "Intereses cobrados por anticipado", variacion: "", mantenerIgual: false },
]);

const pasivoLargo = ref([
  { concepto: "Acreedores diversos a largo plazo", variacion: "", mantenerIgual: false },
  { concepto: "Cuentas por pagar a largo plazo", variacion: "", mantenerIgual: false },
  { concepto: "Cobros anticipados a largo plazo", variacion: "", mantenerIgual: false },
]);

const capitalContribuido = ref([
  { concepto: "Capital social", variacion: "", mantenerIgual: false },
  { concepto: "Aportaciones para futuros aumentos de capital", variacion: "", mantenerIgual: false },
  { concepto: "Prima en venta de acciones", variacion: "", mantenerIgual: false },
  { concepto: "Donaciones", variacion: "", mantenerIgual: false },
]);

const capitalGanadoEditable = ref([
  { concepto: "Reserva legal", variacion: "", mantenerIgual: false },
  { concepto: "Otros resultados integrales", variacion: "", mantenerIgual: false },
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
          <h1>Supuestos Proforma – Balance General</h1>
          <p class="page-description">
            Define los supuestos para proyectar el balance general a partir del último periodo disponible.
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

      <p class="section-helper">
        Estos valores fueron definidos previamente en el Estado de Resultados Proforma y se aplican también al Balance General Proforma.
      </p>

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
          <div class="readonly-box">{{ projectConfig.periodoProyectado }}</div>
        </div>

        <div class="field">
          <label>Inflación esperada (%)</label>
          <div class="readonly-box">{{ projectConfig.inflacionEsperada }}%</div>
        </div>
      </div>
    </section>

    <section class="note note-info">
      <div class="note-mini">
        <span class="material-symbols-outlined">info</span>
        <span>Consideraciones automáticas</span>
      </div>
      <p>
        Las cuentas automáticas se obtienen del periodo base y del Estado de Resultados Proforma.
        Los Fondos Externos Requeridos (FER) se calculan automáticamente para cuadrar el balance,
        representando la necesidad de financiamiento o excedente de efectivo tras los supuestos aplicados.
      </p>
    </section>

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon icon-blue">account_balance_wallet</span>
        <h3>Supuestos por cuenta – Activos</h3>
      </div>

      <div class="group-label">Activo circulante</div>

      <div class="assumptions-table">
        <div class="assumptions-head">
          <div class="col-concepto">Concepto</div>
          <div class="col-variacion center">Variación (%)</div>
          <div class="col-check right">Mantener igual</div>
        </div>

        <div
          v-for="(item, idx) in activoCirculante"
          :key="`ac-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="item.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="item.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>
      </div>

      <div class="group-label group-label-bordered">Activo no circulante</div>

      <div class="assumptions-table">
        <div
          v-for="(item, idx) in activoNoCirculante"
          :key="`anc-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="item.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="item.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon icon-indigo">payments</span>
        <h3>Supuestos por cuenta – Pasivos</h3>
      </div>

      <div class="group-label">Pasivo a corto plazo</div>

      <div class="assumptions-table">
        <div class="assumptions-head">
          <div class="col-concepto">Concepto</div>
          <div class="col-variacion center">Variación (%)</div>
          <div class="col-check right">Mantener igual</div>
        </div>

        <div
          v-for="(item, idx) in pasivoCorto"
          :key="`pc-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="item.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="item.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>
      </div>

      <div class="group-label group-label-bordered">Pasivo a largo plazo</div>

      <div class="assumptions-table">
        <div
          v-for="(item, idx) in pasivoLargo"
          :key="`pl-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="item.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="item.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon icon-amber">account_balance</span>
        <h3>Supuestos por cuenta – Capital contable</h3>
      </div>

      <div class="group-label">Capital contribuido</div>

      <div class="assumptions-table">
        <div class="assumptions-head">
          <div class="col-concepto">Concepto</div>
          <div class="col-variacion center">Variación (%)</div>
          <div class="col-check right">Mantener igual</div>
        </div>

        <div
          v-for="(item, idx) in capitalContribuido"
          :key="`cc-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="item.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="item.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>
      </div>

      <div class="group-label group-label-bordered">Capital ganado</div>

      <div class="assumptions-table">
        <div class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">Utilidades o pérdidas de ejercicios anteriores</div>
          </div>

          <div class="col-variacion">
            <input class="input input-disabled" type="text" placeholder="Auto" disabled />
          </div>

          <div class="col-check check-wrap">
            <span class="mini-tag mini-tag-gray">Tomado del balance base</span>
          </div>
        </div>

        <div
          v-for="(item, idx) in capitalGanadoEditable"
          :key="`cg-${idx}`"
          class="assumptions-row"
        >
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>

          <div class="col-variacion">
            <div class="input-with-suffix">
              <input
                v-model="item.variacion"
                class="input"
                type="number"
                step="0.1"
                placeholder="0.0"
              />
              <span class="suffix">%</span>
            </div>
          </div>

          <div class="col-check check-wrap">
            <input v-model="item.mantenerIgual" class="checkbox" type="checkbox" />
          </div>
        </div>

        <div class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">Utilidad o pérdida del ejercicio</div>
          </div>

          <div class="col-variacion">
            <input class="input input-disabled" type="text" placeholder="Auto" disabled />
          </div>

          <div class="col-check check-wrap">
            <span class="mini-tag mini-tag-blue">
              Tomado del Estado de Resultados Proforma
            </span>
          </div>
        </div>
      </div>
    </section>

    <section class="note note-fer">
      <div class="fer-box">
        <div class="fer-icon">
          <span class="material-symbols-outlined">auto_fix_high</span>
        </div>

        <div class="fer-content">
          <h4>Fondos externos requeridos (FER)</h4>
          <p>
            Cuenta niveladora calculada automáticamente para cuadrar el balance general proforma.
          </p>
        </div>

        <div class="fer-status">Calculado automáticamente</div>
      </div>
    </section>

    <div class="actions">
      <button class="btn-secondary" type="button" @click="cancelar">
        Cancelar
      </button>

      <button class="btn-primary" type="button" @click="goToProyeccionProformaBalance">
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
  margin-bottom: 14px;
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

.icon-blue {
  color: #2563eb;
}

.icon-indigo {
  color: #4f46e5;
}

.icon-amber {
  color: #f59e0b;
}

.section-helper {
  margin: 0 0 18px;
  color: #507c95;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.6;
}

/* Config */
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

.input-disabled {
  background: #f8fafc;
  border-color: #f1f5f9;
  color: #94a3b8;
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

/* Assumptions */
.group-label {
  margin-top: 4px;
  margin-bottom: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background: #f8fafc;
  color: #299de0;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.group-label-bordered {
  margin-top: 14px;
}

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

.check-wrap {
  display: flex;
  justify-content: flex-start;
}

.checkbox {
  width: 16px;
  height: 16px;
  accent-color: #299de0;
}

/* Tags */
.mini-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 9px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  line-height: 1.25;
  text-align: center;
  max-width: 140px;
}

.mini-tag-gray {
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.mini-tag-blue {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid rgba(219, 234, 254, 0.9);
}

/* Notes */
.note {
  position: relative;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.note-info {
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 70%);
  border: 1px solid #dbeafe;
}

.note-mini {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #299de0;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.note-mini .material-symbols-outlined {
  font-size: 18px;
}

.note-info p {
  margin: 0;
  color: #0e161b;
  font-weight: 700;
  font-size: 14px;
  line-height: 1.55;
}

.note-fer {
  background: rgba(239, 246, 255, 0.55);
  border: 1px solid #dbeafe;
}

.fer-box {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.fer-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #dbeafe;
  color: #299de0;
  display: grid;
  place-items: center;
}

.fer-icon .material-symbols-outlined {
  font-size: 20px;
}

.fer-content h4 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 900;
  color: #0e161b;
}

.fer-content p {
  margin: 0;
  color: #507c95;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.55;
}

.fer-status {
  color: #299de0;
  font-size: 12px;
  font-weight: 800;
  font-style: italic;
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

  .fer-box {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
  }
}

@media (min-width: 1200px) {
  .config-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>


