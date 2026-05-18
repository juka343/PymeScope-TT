<script setup>
import { ref, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { db } from "@/firebase/config";
import { doc, getDoc, setDoc, addDoc, collection, serverTimestamp } from "firebase/firestore";

const router = useRouter();
const route = useRoute();
const getRouteName = (baseName) => route.path.includes('dashboard-multi') ? `${baseName}Multi` : baseName;

const projectId = route.params.id_proyecto;
const isProcessing = ref(false);
const formularioEnviado = ref(false);   // controla si mostrar validaciones
const errorBanner = ref("");            // mensaje de error visible en el form

const projectConfig = ref({
  periodicidad: "Cargando...", 
  periodoBaseId: "",
  periodoBaseLabel: "Cargando...",
  periodDateBase: "",
  resultsUrl: "",
  periodoProyectado: "",
  inflacionEsperada: 0.0,
});

// Referencia al ID del documento si estamos editando
const erDocIdRef = ref(null);

const periodOptions = ref([]);

function generateNextPeriods(baseDate, periodicity) {
  const options = [];
  if (!baseDate || !periodicity) return options;

  const getMonthName = (m) => [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
  ][m - 1];

  if (periodicity.toLowerCase() === "anual") {
    let year = parseInt(baseDate);
    for (let i = 1; i <= 5; i++) {
      options.push(`Ejercicio ${year + i}`);
    }
  } 
  else if (periodicity.toLowerCase() === "mensual") {
    const [y, m] = baseDate.split("-").map(Number);
    let currentYear = y;
    let currentMonth = m;
    for (let i = 1; i <= 5; i++) {
      currentMonth++;
      if (currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
      }
      options.push(`${getMonthName(currentMonth)} ${currentYear}`);
    }
  } 
  else if (periodicity.toLowerCase() === "trimestral") {
    const [y, m] = baseDate.split("-").map(Number);
    let currentYear = y;
    let currentQ = Math.ceil(m / 3);
    
    for (let i = 1; i <= 5; i++) {
      currentQ++;
      if (currentQ > 4) {
        currentQ = 1;
        currentYear++;
      }
      options.push(`Q${currentQ} ${currentYear}`);
    }
  }

  return options;
}

// Reactividad para las opciones de periodo
watch(
  [() => projectConfig.value.periodDateBase, () => projectConfig.value.periodicidad],
  ([newDate, newFreq]) => {
    if (newDate && newFreq && newFreq !== "Cargando...") {
      const nextPeriods = generateNextPeriods(newDate, newFreq);
      periodOptions.value = nextPeriods;
      
      // Si no hay periodo proyectado seleccionado, o el actual no está en las nuevas opciones,
      // tomamos el primero por defecto (solo si no estamos en modo edición con un valor ya cargado)
      if (!projectConfig.value.periodoProyectado || !nextPeriods.includes(projectConfig.value.periodoProyectado)) {
         if (nextPeriods.length > 0 && !route.query.modo) {
           projectConfig.value.periodoProyectado = nextPeriods[0];
         }
      }
    }
  }
);

onMounted(async () => {
  const modoEditar = route.query.modo === 'editar';
  const isHistory = route.query.isHistory === 'true';
  const lsKeyConfig = isHistory ? 'history_projection_config' : 'current_projection_config';

  const savedConfig = modoEditar
    ? JSON.parse(localStorage.getItem(lsKeyConfig) || '{}')
    : null;

  projectConfig.value.periodoBaseId = route.query.periodoBaseId || savedConfig?.periodoBaseId || "";
  projectConfig.value.periodoBaseLabel = route.query.label || savedConfig?.periodoBase || "Último disponible";
  projectConfig.value.periodDateBase = route.query.periodDate || savedConfig?.periodDate || "";
  
  if (modoEditar) {
    erDocIdRef.value = savedConfig?.erId || null;
  }

  console.log("Debug Proyecciones:", {
    projectId,
    baseDate: projectConfig.value.periodDateBase,
    baseLabel: projectConfig.value.periodoBaseLabel
  });

  if (projectId) {
    try {
      const projectDocRef = doc(db, "proyectos", projectId);
      const projectDocSnap = await getDoc(projectDocRef);
      if (projectDocSnap.exists()) {
        const data = projectDocSnap.data();
        const p = data.periodicidad || "mensual";
        projectConfig.value.periodicidad = p;
      }

      if (projectConfig.value.periodoBaseId) {
        const periodDocRef = doc(db, "proyectos", projectId, "periodos", projectConfig.value.periodoBaseId);
        const periodDocSnap = await getDoc(periodDocRef);
        if (periodDocSnap.exists()) {
          const data = periodDocSnap.data();
          projectConfig.value.resultsUrl = data.resultsFile?.url || "";
          if (!projectConfig.value.periodDateBase) {
            projectConfig.value.periodDateBase = data.periodDate || "";
          }
          if (!projectConfig.value.resultsUrl) {
            console.warn("⚠️ No se encontró URL del Estado de Resultados en el periodo base.");
          }
        }
      }
    } catch (error) {
      console.error("Error al cargar datos iniciales:", error);
      projectConfig.value.periodicidad = "Desconocida";
    }
  }

  if (modoEditar) {
    const lsKeySupuestos = isHistory ? 'history_projection_supuestos' : 'current_projection_supuestos';
    let savedSupuestos = localStorage.getItem(lsKeySupuestos);
    let sup = null;

    if (savedSupuestos) {
      sup = JSON.parse(savedSupuestos);
    } else {
      try {
        const { collection, query, orderBy, limit, getDocs, where } = await import("firebase/firestore");
        const proyeccionesERRef = collection(db, "proyectos", projectId, "proyecciones_er");
        
        // Si tenemos el erId exacto del historial, lo buscamos directamente
        const erIdFromConfig = savedConfig?.erId || null;
        let proyDoc = null;

        if (erIdFromConfig) {
          const { doc: fsDoc, getDoc: fsGetDoc } = await import("firebase/firestore");
          const erDocRef = fsDoc(db, "proyectos", projectId, "proyecciones_er", erIdFromConfig);
          const erSnap = await fsGetDoc(erDocRef);
          if (erSnap.exists()) proyDoc = erSnap;
        }

        if (!proyDoc) {
          // Fallback: tomar el más reciente
          const qProy = query(proyeccionesERRef, orderBy("created_at", "desc"), limit(1));
          const proySnapshot = await getDocs(qProy);
          if (!proySnapshot.empty) {
            proyDoc = proySnapshot.docs[0];
          } else {
            const proyeccionesOldRef = collection(db, "proyectos", projectId, "proyecciones");
            const qOld = query(proyeccionesOldRef, orderBy("created_at", "desc"), limit(10));
            const oldSnapshot = await getDocs(qOld);
            proyDoc = oldSnapshot.docs.find(d =>
              (d.data().tipo_proyeccion === "estado_resultados" || !d.data().tipo_proyeccion) &&
              d.data().supuestos?.ingresos
            );
          }
        }
        
        if (proyDoc) {
          const proyData = proyDoc.data();
          sup = {
            ingresos: proyData.supuestos?.ingresos || [],
            costos: proyData.supuestos?.costos || [],
            impuestos: proyData.supuestos?.impuestos || [],
            incluirImpuestos: proyData.supuestos?.impuestos?.length > 0,
            inflacionEsperada: proyData.inflacion_esperada || proyData.inflacion_especada,
            periodoProyectado: proyData.periodo_proyectado
          };
        }
      } catch (err) {
        console.error("Error al recuperar supuestos de Firestore:", err);
      }
    }

    if (sup) {
      if (sup.ingresos) {
        ingresosRows.value = ingresosRows.value.map(baseRow => {
          const loadedRow = sup.ingresos.find(r => r.concepto === baseRow.concepto);
          return loadedRow ? { ...baseRow, variacion: loadedRow.variacion, mantener_igual: loadedRow.mantener_igual ?? loadedRow.mantenerIgual ?? false } : baseRow;
        });
      }
      if (sup.costos) {
        costosRows.value = costosRows.value.map(baseRow => {
          const loadedRow = sup.costos.find(r => r.concepto === baseRow.concepto);
          return loadedRow ? { ...baseRow, variacion: loadedRow.variacion, mantener_igual: loadedRow.mantener_igual ?? loadedRow.mantenerIgual ?? false } : baseRow;
        });
      }
      if (sup.impuestos) {
        impuestosRows.value = impuestosRows.value.map(baseRow => {
          const loadedRow = sup.impuestos.find(r => r.concepto === baseRow.concepto);
          return loadedRow ? { ...baseRow, variacion: loadedRow.variacion, mantener_igual: loadedRow.mantener_igual ?? loadedRow.mantenerIgual ?? false } : baseRow;
        });
      }
      if (typeof sup.incluirImpuestos === 'boolean') incluirImpuestos.value = sup.incluirImpuestos;
      if (sup.inflacionEsperada !== undefined) projectConfig.value.inflacionEsperada = sup.inflacionEsperada;
      if (sup.periodoProyectado) projectConfig.value.periodoProyectado = sup.periodoProyectado;
    }
  }
});

const ingresosRows = ref([
  { concepto: "Ventas netas / Ingresos por servicios", variacion: "", mantener_igual: false, isMotor: true, isVariable: false },
  { concepto: "Otros ingresos", variacion: "", mantener_igual: false, isVariable: false },
  { concepto: "Productos financieros", variacion: null, mantener_igual: false, isVariable: true },
]);

const costosRows = ref([
  { concepto: "Costo de ventas/Costo por servicios", subtitulo: "", variacion: null, mantener_igual: false, isVariable: true },
  { concepto: "Gastos de venta", subtitulo: "", variacion: null, mantener_igual: false, isVariable: true },
  { concepto: "Gastos de administración", subtitulo: "Operativos y administrativos", variacion: "", mantener_igual: false, isVariable: false },
  { concepto: "Gastos de nómina", subtitulo: "Sueldos y salarios", variacion: "", mantener_igual: false, isVariable: false },
  { concepto: "Gastos financieros", subtitulo: "Intereses y comisiones", variacion: "", mantener_igual: false, isVariable: false },
  { concepto: "Otros gastos", subtitulo: "", variacion: "", mantener_igual: false, isVariable: false },
]);

const impuestosRows = ref([
  { concepto: "ISR", variacion: null, mantener_igual: false, isVariable: true },
  { concepto: "PTU (Participación de los Trabajadores en las Utilidades)", variacion: null, mantener_igual: false, isVariable: true },
]);

const incluirImpuestos = ref(true);

function cancelar() {
  router.push({ name: getRouteName("proyecciones") });
}

function isFilaVacia(row) {
  if (row.isVariable) return false;
  return !row.mantener_igual && (row.variacion === "" || row.variacion === null || row.variacion === undefined);
}

async function generarProyeccion() {
  if (!projectConfig.value.periodoBaseId) {
    errorBanner.value = "No se detectó un periodo base válido para proyectar.";
    return;
  }

  formularioEnviado.value = true;
  errorBanner.value = "";

  const hayFilasVacias = [
    ...ingresosRows.value,
    ...costosRows.value,
    ...(incluirImpuestos.value ? impuestosRows.value : []),
  ].some(isFilaVacia);

  if (!projectConfig.value.periodoProyectado) {
    errorBanner.value = "Selecciona un periodo a proyectar antes de continuar.";
    return;
  }

  if (!projectConfig.value.resultsUrl) {
    errorBanner.value = "No se encontró el PDF del Estado de Resultados en el periodo base. Verifica que el documento esté cargado.";
    return;
  }

  if (hayFilasVacias) {
    errorBanner.value = "Todos los campos deben tener una variación (%) o estar marcados como \"Mantener igual\".";
    return;
  }

  isProcessing.value = true;

  try {
    const formatRow = (row) => ({
      concepto: row.concepto,
      variacion: (row.isVariable && (row.variacion === "" || row.variacion === null) && !row.mantener_igual) ? null : (isNaN(parseFloat(row.variacion)) ? 0 : parseFloat(row.variacion)),
      mantener_igual: row.mantener_igual
    });

    const payload = {
      project_id: projectId,
      period_id: projectConfig.value.periodoBaseId,
      results_url: projectConfig.value.resultsUrl,
      periodo_proyectado_label: projectConfig.value.periodoProyectado,
      inflacion_esperada: parseFloat(projectConfig.value.inflacionEsperada) || 0,
      periodo_base: projectConfig.value.periodoBaseLabel,
      ingresos: ingresosRows.value.map(formatRow),
      costos: costosRows.value.map(formatRow),
      impuestos: incluirImpuestos.value ? impuestosRows.value.map(formatRow) : []
    };

    const response = await fetch("http://127.0.0.1:8000/api/projections/estado-resultados", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const detailMsg = typeof errData.detail === 'object' 
        ? JSON.stringify(errData.detail) 
        : errData.detail;
      throw new Error(detailMsg || "Error en el servidor al calcular proyecciones");
    }

    const resultados = await response.json();

    // Construir objeto para guardar en Firestore
    const datos_proyeccion = {
      tipo_proyeccion: "estado_resultados",
      periodo_proyectado: projectConfig.value.periodoProyectado,
      inflacion_esperada: parseFloat(projectConfig.value.inflacionEsperada) || 0,
      periodo_base_id: projectConfig.value.periodoBaseId,
      supuestos: {
        ingresos: payload.ingresos,
        costos: payload.costos,
        impuestos: payload.impuestos
      },
      resultados: {
        tablas_proyectadas: resultados.tablas_proyectadas,
        ventas: resultados.ventas,
        utilidad_bruta: resultados.utilidad_bruta,
        utilidad_operativa: resultados.utilidad_operativa,
        utilidad_antes_impuestos: resultados.utilidad_antes_impuestos,
        impuestos: resultados.impuestos,
        impuestos_totales: resultados.impuestos_totales,
        utilidad_neta: resultados.utilidad_neta
      },
      created_at: serverTimestamp()
    };

    // Guardar en Firestore (Crear nuevo o Actualizar existente)
    const modoEditar = route.query.modo === 'editar';
    const isHistory = route.query.isHistory === 'true';
    let erDocId = erDocIdRef.value;

    if (modoEditar && erDocId) {
      const erDocRef = doc(db, "proyectos", projectId, "proyecciones_er", erDocId);
      await setDoc(erDocRef, datos_proyeccion, { merge: true });
      console.log("PROYECCIÓN ER ACTUALIZADA EN FIRESTORE:", erDocId);
    } else {
      const proyeccionesERRef = collection(db, "proyectos", projectId, "proyecciones_er");
      const erDocRef = await addDoc(proyeccionesERRef, datos_proyeccion);
      erDocId = erDocRef.id;
      console.log("PROYECCIÓN ER GUARDADA EN FIRESTORE:", erDocId);
    }
    
    // Actualizar localStorage según el modo (Historial o Sesión Actual)
    const prefix = isHistory ? 'history' : 'current';
    
    localStorage.setItem(`${prefix}_projection_result`, JSON.stringify(resultados));
    localStorage.setItem(`${prefix}_projection_config`, JSON.stringify({
      periodoBase: projectConfig.value.periodoBaseLabel,
      periodoProyectado: projectConfig.value.periodoProyectado,
      inflacion: projectConfig.value.inflacionEsperada,
      incluirImpuestos: incluirImpuestos.value,
      periodoBaseId: projectConfig.value.periodoBaseId,
      periodDate: projectConfig.value.periodDateBase,
      erId: erDocId,
    }));
    localStorage.setItem(`${prefix}_projection_supuestos`, JSON.stringify({
      ingresos: ingresosRows.value,
      costos: costosRows.value,
      impuestos: impuestosRows.value,
      incluirImpuestos: incluirImpuestos.value,
      inflacionEsperada: projectConfig.value.inflacionEsperada,
      periodoProyectado: projectConfig.value.periodoProyectado,
    }));

    router.push({ 
      name: getRouteName("ProyeccionProformaEdo"),
      query: isHistory ? { isHistory: 'true' } : {}
    });

  } catch (error) {
    console.error("Error generando proyección:", error);
    errorBanner.value = error.message || "Ocurrió un error al conectar con el motor de proyecciones.";
  } finally {
    isProcessing.value = false;
  }
}
</script>

<template>
  <div class="wrap">
    <!-- Overlay de Carga -->
    <div v-if="isProcessing" class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <h3>Generando Estado de Resultados Proforma...</h3>
        <p>Procesando OCR del documento base y aplicando supuestos financieros.</p>
      </div>
    </div>

    <!-- Alerta de Error -->
    <div v-if="errorBanner" class="form-error-banner">
      <span class="material-symbols-outlined">error</span>
      <p>{{ errorBanner }}</p>
      <button class="close-error" @click="errorBanner = ''">×</button>
    </div>

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
          <span>Periodo base: {{ projectConfig.periodoBaseLabel }}</span>
        </div>
      </div>
    </div>

    <div v-if="errorBanner" class="form-error-banner">
      <span class="material-symbols-outlined">error</span>
      <span>{{ errorBanner }}</span>
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
          <div class="readonly-box">{{ projectConfig.periodoBaseLabel }}</div>
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
            <input v-model="projectConfig.inflacionEsperada" class="input" type="number" step="0.1" placeholder="4.5" />
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

        <div v-for="(row, idx) in ingresosRows" :key="`ingreso-${idx}`" class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">{{ row.concepto }}</div>
          </div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="row.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(row) }" type="number" step="0.1" :placeholder="row.isVariable ? 'Heredará % de ventas' : '0.0'" :disabled="row.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(row)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap">
            <input v-if="!row.isMotor" v-model="row.mantener_igual" class="checkbox" type="checkbox" :disabled="!row.mantener_igual && (row.variacion !== null && row.variacion !== '' )" />
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

        <div v-for="(row, idx) in costosRows" :key="`costo-${idx}`" class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">{{ row.concepto }}</div>
            <p v-if="row.subtitulo" class="concept-sub">{{ row.subtitulo }}</p>
          </div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="row.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(row) }" type="number" step="0.1" :placeholder="row.isVariable ? 'Heredará % de ventas' : '0.0'" :disabled="row.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(row)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap">
            <input v-model="row.mantener_igual" class="checkbox" type="checkbox" :disabled="!row.mantener_igual && (row.variacion !== null && row.variacion !== '' )" />
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
        <div v-for="(row, idx) in impuestosRows" :key="`impuesto-${idx}`" class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">{{ row.concepto }}</div>
            <div class="leyenda-fiscal" v-if="row.concepto === 'ISR'" style="font-size: 11px; color: #64748b; margin-top: 6px; line-height: 1.4;">
              💡 Para personas morales en México se recomienda <strong>30%</strong> (Art. 9 LISR). 
              Verifica la tasa aplicable según el régimen fiscal de tu empresa.
            </div>
            <div class="leyenda-fiscal" v-if="row.concepto.includes('PTU')" style="font-size: 11px; color: #64748b; margin-top: 6px; line-height: 1.4;">
              💡 La tasa estándar en México es <strong>10%</strong> (Art. 123 Constitucional). 
              No aplica si la empresa tuvo pérdidas fiscales o es de nueva creación.
            </div>
          </div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="row.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(row) }" type="number" step="0.1" placeholder="" :disabled="row.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(row)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap" style="flex-direction: column; align-items: flex-end;">
            <span style="font-size: 12px; color: #94a3b8; font-weight: 700; user-select: none;">N/A</span>
            <span style="font-size: 10px; color: #94a3b8; text-align: right; max-width: 140px; margin-top: 4px; line-height: 1.3;">Los impuestos dependen de la utilidad proyectada, no pueden mantenerse fijos.</span>
          </div>
        </div>
      </div>
    </section>

    <div class="actions">
      <button class="btn-secondary" type="button" :disabled="isProcessing" @click="cancelar">Cancelar</button>
      <button class="btn-primary" type="button" :disabled="isProcessing" @click="generarProyeccion">
        <span class="material-symbols-outlined" v-if="!isProcessing">auto_graph</span>
        <span class="material-symbols-outlined" v-else>sync</span>
        <span>{{ isProcessing ? 'Calculando proyección...' : 'Generar proyección proforma' }}</span>
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

.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: grid;
  place-items: center;
  text-align: center;
}

.loading-content h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 900;
  color: #0e161b;
}

.loading-content p {
  margin: 0;
  font-size: 13px;
  color: #507c95;
  font-weight: 700;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #299de0;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.close-error {
  background: none;
  border: none;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
  color: #b91c1c;
  margin-left: auto;
  line-height: 1;
}

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

.section-title-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.section-title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 900;
  color: #0e161b;
}

.tax-include-check {
  width: 16px;
  height: 16px;
  accent-color: #299de0;
  cursor: pointer;
}

.section-icon {
  font-size: 22px;
  color: #299de0;
}

.icon-green { color: #16a34a; }
.icon-red { color: #ef4444; }
.icon-amber { color: #f59e0b; }

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

.input-with-suffix .input { padding-right: 36px; }

.suffix {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 12px;
  font-weight: 700;
}

.assumptions-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.assumptions-head { display: none; }

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

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 14px;
  margin-top: 2px;
  border-top: 1px solid #e8eff3;
  flex-wrap: wrap;
}

.btn-secondary, .btn-primary {
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

.btn-secondary:hover { background: #f8fafb; }

.btn-primary {
  border: none;
  background: #299de0;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.btn-primary:hover { background: #1a8ac7; }

.btn-secondary:active, .btn-primary:active { transform: translateY(1px); }

.btn-primary .material-symbols-outlined { font-size: 18px; }

.foot {
  margin: 4px 0 22px;
  text-align: center;
  color: #9ca3af;
  font-weight: 700;
  font-size: 12px;
}

.foot p { margin: 0; line-height: 1.6; }

@media (min-width: 768px) {
  .config-grid { grid-template-columns: repeat(2, 1fr); }
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
  .section-title-toggle h3 {
    text-transform: none;
    font-size: 18px;
    font-weight: 900;
    color: #0e161b;
    letter-spacing: normal;
  }
  .assumptions-row {
    grid-template-columns: 6fr 3fr 3fr;
    gap: 16px;
  }
  .center { text-align: center; }
  .right { text-align: right; }
  .check-wrap { justify-content: flex-end; padding-right: 14px; }
}

@media (min-width: 1200px) {
  .config-grid { grid-template-columns: repeat(4, 1fr); }
}

.form-error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 12px;
  padding: 12px 16px;
  color: #b91c1c;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 4px;
}

.form-error-banner .material-symbols-outlined { font-size: 20px; flex-shrink: 0; }

.required-badge {
  font-size: 11px;
  font-weight: 800;
  color: #ef4444;
  background: #fee2e2;
  padding: 2px 6px;
  border-radius: 6px;
  margin-top: 4px;
  display: inline-block;
}

.input-error {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.18) !important;
  background: #fff5f5 !important;
}
</style>
