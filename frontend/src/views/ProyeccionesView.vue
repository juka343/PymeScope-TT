<script setup>
import { ref, onMounted, onActivated, nextTick } from "vue";
import { useRouter, useRoute } from "vue-router";
import { db } from "@/firebase/config";
import { collection, getDocs, query, orderBy, limit, where, doc, deleteDoc, updateDoc } from "firebase/firestore";

const router = useRouter();
const route = useRoute();
const projectId = route.params.id_proyecto;

const estadoResultadosDisponible = ref(false);
const balanceDisponible = ref(false);
const periodoBaseLabel = ref("Cargando...");
const latestPeriodId = ref(null);
const latestPeriodDate = ref("");
const hasExistingProjection = ref(false);
const hasExistingBalanceProjection = ref(false);

const periodosMap = ref({});
const historialProyecciones = ref([]);

async function cargarDatos() {
  if (!projectId) {
    periodoBaseLabel.value = "Error: Proyecto no encontrado";
    return;
  }

  try {
    const periodosRef = collection(db, "proyectos", projectId, "periodos");
    const snapshot = await getDocs(periodosRef);

    if (snapshot.empty) {
      periodoBaseLabel.value = "No hay periodos disponibles";
      return;
    }

    const loaded = [];
    const datesMap = {};
    snapshot.forEach((docSnap) => {
      const data = docSnap.data();
      periodosMap.value[docSnap.id] = data.label || "Periodo";
      datesMap[docSnap.id] = data.periodDate || "";
      loaded.push({
        id: docSnap.id,
        label: data.label || "Periodo",
        periodDate: data.periodDate || "",
        hasAnalysis: Boolean(
          data.analisis_rentabilidad ||
          data.analisis_liquidez ||
          data.analisis_endeudamiento ||
          data.analisis_rotacion ||
          data.analisis_estructura
        ),
      });
    });

    const analyzedPeriods = loaded.filter(p => p.hasAnalysis);

    if (analyzedPeriods.length === 0) {
      periodoBaseLabel.value = "Sin periodos analizados";
      return;
    }

    analyzedPeriods.sort((a, b) => a.periodDate.localeCompare(b.periodDate));
    const latest = analyzedPeriods[analyzedPeriods.length - 1];

    periodoBaseLabel.value = latest.label;
    latestPeriodId.value = latest.id;
    latestPeriodDate.value = latest.periodDate;
    estadoResultadosDisponible.value = true;

    // --- Evaluar si hay una sesión "En Progreso" para ESTE último periodo ---
    const sessionER = localStorage.getItem('current_projection_result');
    const sessionConfigStr = localStorage.getItem('current_projection_config');
    const sessionBG = localStorage.getItem('current_balance_result');
    
    let isSessionForLatest = false;
    if (sessionConfigStr) {
      try {
        const config = JSON.parse(sessionConfigStr);
        if (config.periodoBaseId === latest.id) {
          isSessionForLatest = true;
        }
      } catch(e) {
        console.warn("Error parseando current_projection_config", e);
      }
    }

    if (isSessionForLatest) {
      balanceDisponible.value = !!sessionER;
      hasExistingBalanceProjection.value = !!sessionBG;
    } else {
      balanceDisponible.value = false;
      hasExistingBalanceProjection.value = false;
    }

    // --- Obtener TODOS los Estados de Resultados ---
    const proyeccionesERRef = collection(db, "proyectos", projectId, "proyecciones_er");
    const qERAll = query(proyeccionesERRef, orderBy("created_at", "desc"));
    let erSnapshotAll = await getDocs(qERAll);
    
    if (erSnapshotAll.empty) {
      const proyeccionesOldRef = collection(db, "proyectos", projectId, "proyecciones");
      const qOldAll = query(proyeccionesOldRef, orderBy("created_at", "desc"));
      const oldSnapshotAll = await getDocs(qOldAll);
      const filteredOldDocs = oldSnapshotAll.docs.filter(d => 
        (d.data().tipo_proyeccion === "estado_resultados" || !d.data().tipo_proyeccion) && 
        d.data().resultados?.ventas
      );
      erSnapshotAll = { docs: filteredOldDocs };
    }

    // --- Obtener TODOS los Balances Generales ---
    const proyeccionesBGRef = collection(db, "proyectos", projectId, "proyecciones_bg");
    const qBGAll = query(proyeccionesBGRef, orderBy("created_at", "desc"));
    let bgSnapshotAll = await getDocs(qBGAll);

    if (bgSnapshotAll.empty) {
      const proyeccionesOldRef = collection(db, "proyectos", projectId, "proyecciones");
      const qOldBalAll = query(proyeccionesOldRef, where("tipo_proyeccion", "==", "balance_general"), orderBy("created_at", "desc"));
      bgSnapshotAll = await getDocs(qOldBalAll);
    }

    // --- Agrupar Historial por erId (docSnap.id del ER) ---
    // Cada ER es una proyección única. Usamos su ID de Firestore como clave.
    const pMap = new Map();

    erSnapshotAll.docs.forEach(docSnap => {
        const data = docSnap.data();
        if (!data.periodo_base_id) return;

        const key = docSnap.id;
        // Calcular % de ventas desde supuestos guardados
        const ingresosRows = data.supuestos?.ingresos || [];
        const ventasRow = ingresosRows.find(r =>
          r.concepto?.toLowerCase().includes('ventas') || r.concepto?.toLowerCase().includes('ingresos')
        ) || ingresosRows[0];
        const ventasPct = ventasRow?.variacion ?? null;

        pMap.set(key, {
            mapKey: key,
            periodo_base_id: data.periodo_base_id,
            base_label: periodosMap.value[data.periodo_base_id] || "Periodo Desconocido",
            periodDate: datesMap[data.periodo_base_id] || "",
            erId: docSnap.id,
            erData: data,
            created_at: data.created_at,
            custom_name: data.nombre_proyeccion || null,
            proyected_label: data.periodo_proyectado || "Proyección",
            ventasPct: ventasPct,
            inflacion: data.inflacion_esperada || data.inflacion_especada || null,
            hasER: true,
            hasBG: false
        });
    });

    bgSnapshotAll.docs.forEach(docSnap => {
        const data = docSnap.data();

        if (data.er_id && pMap.has(data.er_id)) {
            // Enlace exacto: el BG apunta directamente al ER por er_id (proyecciones nuevas)
            const item = pMap.get(data.er_id);
            item.bgId = docSnap.id;
            item.bgData = data;
            item.hasBG = true;
            if (data.created_at?.seconds > item.created_at?.seconds) {
               item.created_at = data.created_at;
            }
        } else if (data.periodo_base_id) {
            // Fallback: proyecciones antiguas sin er_id → buscar el primer ER del mismo periodo base
            let matched = false;
            for (const [key, item] of pMap) {
                if (item.periodo_base_id === data.periodo_base_id && !item.hasBG) {
                    item.bgId = docSnap.id;
                    item.bgData = data;
                    item.hasBG = true;
                    matched = true;
                    break;
                }
            }
            // Si no hubo ER emparejado, crear entrada solo-BG
            if (!matched) {
                const bgKey = `bg_${docSnap.id}`;
                pMap.set(bgKey, {
                    mapKey: bgKey,
                    periodo_base_id: data.periodo_base_id,
                    base_label: periodosMap.value[data.periodo_base_id] || "Periodo Desconocido",
                    periodDate: datesMap[data.periodo_base_id] || "",
                    bgId: docSnap.id,
                    bgData: data,
                    created_at: data.created_at,
                    proyected_label: data.periodo_proyectado || "Proyección",
                    hasER: false,
                    hasBG: true
                });
            }
        }
    });

    historialProyecciones.value = Array.from(pMap.values()).sort((a, b) => {
        const ta = a.created_at?.seconds || 0;
        const tb = b.created_at?.seconds || 0;
        return tb - ta;
    });

  } catch (error) {
    console.error("Error cargando datos de proyección:", error);
    periodoBaseLabel.value = "Error al conectar";
  }
}

onMounted(cargarDatos);
onActivated(cargarDatos);

function configurarEstadoResultados() {
  // Placeholder
}

function configurarBalance() {
  if (!balanceDisponible.value) return;

  const savedResult = localStorage.getItem('current_balance_result');
  if (savedResult) {
    router.push({ name: "ProyeccionProformaBalanceGeneral" });
    return;
  }

  router.push({
    name: "FormularioBalanceGeneral",
    query: {
      periodoBaseId: latestPeriodId.value,
      label: periodoBaseLabel.value,
      periodDate: latestPeriodDate.value
    }
  });
}

function iniciarNuevaProyeccion() {
  if (!latestPeriodId.value) return;

  // Siempre limpiamos la sesión al iniciar desde la tarjeta principal
  // garantizando que siempre sea una "Nueva Proyección" desde cero.
  localStorage.removeItem('current_projection_result');
  localStorage.removeItem('current_projection_config');
  localStorage.removeItem('current_projection_supuestos');
  localStorage.removeItem('current_balance_result');
  localStorage.removeItem('current_balance_config');
  localStorage.removeItem('current_balance_supuestos');
  
  hasExistingBalanceProjection.value = false;
  balanceDisponible.value = false;

  router.push({
    name: "FormularioEstadoDeResultados",
    query: {
      periodoBaseId: latestPeriodId.value,
      label: periodoBaseLabel.value,
      periodDate: latestPeriodDate.value
    }
  });
}

// Navegación inteligente inyectando localstorage
function verProyeccionHistorica(item) {
  if (item.hasER) {
    const erData = item.erData;
    localStorage.setItem('history_projection_result', JSON.stringify({
      ...erData.resultados,
      proyected_label: erData.periodo_proyectado
    }));
    localStorage.setItem('history_projection_config', JSON.stringify({
      periodoBase: item.base_label,
      periodoProyectado: erData.periodo_proyectado,
      inflacion: erData.inflacion_especada || erData.inflacion_esperada || 0,
      incluirImpuestos: erData.supuestos?.impuestos?.length > 0,
      periodoBaseId: item.periodo_base_id,
      periodDate: item.periodDate,
      erId: item.erId,
    }));
    if (erData.supuestos) {
       localStorage.setItem('history_projection_supuestos', JSON.stringify({
          ingresos: erData.supuestos.ingresos || [],
          costos: erData.supuestos.costos || [],
          impuestos: erData.supuestos.impuestos || [],
          incluirImpuestos: erData.supuestos.impuestos?.length > 0,
          inflacionEsperada: erData.inflacion_especada || erData.inflacion_esperada || 0,
          periodoProyectado: erData.periodo_proyectado
       }));
    }
  }

  if (item.hasBG) {
    const balData = item.bgData;
    localStorage.setItem('history_balance_result', JSON.stringify(balData.resultados));
    localStorage.setItem('history_balance_config', JSON.stringify({
      periodoBase: item.base_label,
      periodoProyectado: balData.periodo_proyectado,
      inflacion: balData.inflacion_esperada || balData.inflacion_especada || 0,
      periodoBaseId: item.periodo_base_id,
      periodDate: item.periodDate,
      bgId: item.bgId,
    }));
    if (balData.supuestos) {
      localStorage.setItem('history_balance_supuestos', JSON.stringify(balData.supuestos));
    }
  } else {
    localStorage.removeItem('history_balance_result');
    localStorage.removeItem('history_balance_config');
    localStorage.removeItem('history_balance_supuestos');
  }

  router.push({ name: "ProyeccionProformaEdo", query: { isHistory: 'true' } });
}

// Lógica para edición en línea del nombre
const editingId = ref(null);
const editNameInput = ref("");

async function iniciarEdicionNombre(item) {
  editingId.value = item.erId;
  editNameInput.value = item.custom_name || item.proyected_label;
  await nextTick();
  const inputEl = document.getElementById(`edit-input-${item.erId}`);
  if (inputEl) inputEl.focus();
}

function cancelarNombre() {
  editingId.value = null;
  editNameInput.value = "";
}

async function guardarNombre(item) {
  if (!editNameInput.value.trim()) return;
  try {
    const erDocRef = doc(db, "proyectos", projectId, "proyecciones_er", item.erId);
    await updateDoc(erDocRef, {
      nombre_proyeccion: editNameInput.value.trim()
    });
    // Actualizar estado local
    item.custom_name = editNameInput.value.trim();
    editingId.value = null;
  } catch (error) {
    console.error("Error al actualizar nombre de proyección:", error);
    alert("Hubo un error al guardar el nombre.");
  }
}

async function eliminarProyeccion(item) {
  if (!confirm(`¿Estás seguro de que deseas eliminar la proyección de "${item.proyected_label}"?\n\nEsta acción no se puede deshacer.`)) {
    return;
  }
  
  try {
    if (item.erId) {
      await deleteDoc(doc(db, "proyectos", projectId, "proyecciones_er", item.erId));
    }
    if (item.bgId) {
      await deleteDoc(doc(db, "proyectos", projectId, "proyecciones_bg", item.bgId));
    }
    
    // Remover de la vista usando mapKey como clave única garantizada
    historialProyecciones.value = historialProyecciones.value.filter(p => p.mapKey !== item.mapKey);
    
    // Si borramos la proyección que estaba activa en sesión, reiniciar el estado local
    if (item.periodo_base_id === latestPeriodId.value) {
        hasExistingProjection.value = false;
        hasExistingBalanceProjection.value = false;
        balanceDisponible.value = false;
        localStorage.removeItem('current_projection_result');
        localStorage.removeItem('current_projection_config');
        localStorage.removeItem('current_balance_result');
        localStorage.removeItem('current_balance_config');
    }
    
  } catch (error) {
    console.error("Error al eliminar la proyección:", error);
    alert("Hubo un error al eliminar la proyección.");
  }
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
            <span>Periodo base: {{ periodoBaseLabel }}</span>
          </div>

          <button
            class="btn-primary"
            type="button"
            :disabled="!estadoResultadosDisponible"
            @click="iniciarNuevaProyeccion"
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

      <article class="projection-card" :class="{ 'projection-card-disabled': !balanceDisponible }">
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
            <span>Periodo base: {{ periodoBaseLabel }}</span>
          </div>

          <p v-if="!balanceDisponible" class="availability-note">
            Disponible después de generar el Estado de Resultados Proforma
          </p>

          <button
            class="btn-primary"
            :class="{ 'btn-disabled': !balanceDisponible }"
            type="button"
            :disabled="!balanceDisponible"
            @click="configurarBalance"
          >
            <span>{{ hasExistingBalanceProjection ? 'Ver proyección' : 'Configurar proyección' }}</span>
            <span class="material-symbols-outlined">arrow_forward</span>
          </button>
        </div>
      </article>
    </section>

    <!-- HISTORIAL DE PROYECCIONES -->
    <section v-if="historialProyecciones.length > 0" class="history-section">
      <div class="history-header">
        <h2>Historial de Proyecciones</h2>
        <p>Accede a las proyecciones realizadas anteriormente en este proyecto.</p>
      </div>
      
      <div class="history-grid">
        <article v-for="item in historialProyecciones" :key="item.mapKey" class="history-card">
          <div class="hc-top">
            <div class="hc-title-box">
              <div v-if="editingId === item.erId" class="edit-name-wrap">
                <input :id="`edit-input-${item.erId}`" v-model="editNameInput" class="input input-sm" type="text" @keyup.enter="guardarNombre(item)" @keyup.esc="cancelarNombre" />
                <button class="btn-icon-small btn-icon-ok" @click="guardarNombre(item)" title="Guardar"><span class="material-symbols-outlined">check</span></button>
                <button class="btn-icon-small btn-icon-cancel" @click="cancelarNombre" title="Cancelar"><span class="material-symbols-outlined">close</span></button>
              </div>
              <div v-else class="title-with-edit">
                <h4>{{ item.custom_name || item.proyected_label }}</h4>
                <button class="btn-icon-small edit-icon-btn" @click="iniciarEdicionNombre(item)" title="Editar nombre">
                  <span class="material-symbols-outlined">edit</span>
                </button>
              </div>
              <p>Basado en: {{ item.base_label }}</p>
            </div>
            <button class="btn-icon-delete" @click="eliminarProyeccion(item)" title="Eliminar proyección">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </div>
          
          <div class="hc-status">
            <div class="status-pill" :class="item.hasER ? 'status-ok' : 'status-missing'">
              <span class="material-symbols-outlined">{{ item.hasER ? 'check_circle' : 'cancel' }}</span>
              <span>Estado de Resultados</span>
            </div>
            <div class="status-pill" :class="item.hasBG ? 'status-ok' : 'status-missing'">
              <span class="material-symbols-outlined">{{ item.hasBG ? 'check_circle' : 'pending' }}</span>
              <span>Balance General</span>
            </div>
          </div>

          <div class="hc-metrics" v-if="item.ventasPct !== null || item.inflacion !== null">
            <div class="hc-metric-chip" v-if="item.ventasPct !== null">
              <span class="material-symbols-outlined">trending_up</span>
              <span>Ventas {{ item.ventasPct >= 0 ? '+' : '' }}{{ item.ventasPct }}%</span>
            </div>
            <div class="hc-metric-chip hc-metric-neutral" v-if="item.inflacion !== null">
              <span class="material-symbols-outlined">price_change</span>
              <span>Inflación {{ item.inflacion }}%</span>
            </div>
          </div>
          
          <div class="hc-bottom">
            <span class="hc-date" v-if="item.created_at">
              {{ new Date(item.created_at.seconds * 1000).toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric' }) }}
            </span>
            <span class="hc-date" v-else>Fecha desconocida</span>
            
            <button class="btn-outline" @click="verProyeccionHistorica(item)">
              Ver proyección
            </button>
          </div>
        </article>
      </div>
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

.btn-outline-small {
  background: transparent;
  border: 1px solid #d1d5db;
  color: #6b7280;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  width: fit-content;
  align-self: center;
}

.btn-outline-small:hover {
  background: #f3f4f6;
  color: #374151;
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

/* --- HISTORIAL DE PROYECCIONES STYLES --- */
.history-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e8eff3;
}

.history-header {
  margin-bottom: 20px;
}

.history-header h2 {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 800;
  color: #0e161b;
}

.history-header p {
  margin: 0;
  color: #507c95;
  font-size: 14px;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.history-card {
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 14px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.18s ease, transform 0.08s ease;
}

.history-card:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.hc-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.hc-title-box h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 800;
  color: #0e161b;
  line-height: 1.2;
}

.hc-title-box p {
  margin: 0;
  font-size: 12px;
  color: #507c95;
  font-weight: 600;
}

.btn-icon-delete {
  background: transparent;
  border: none;
  color: #d1d5db;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.15s ease;
  display: grid;
  place-items: center;
  margin-top: 0;
}

.btn-icon-delete:hover {
  background: #fef2f2;
  color: #ef4444;
}

.btn-icon-delete .material-symbols-outlined {
  font-size: 20px;
}

/* Inline Edit Styles */
.title-with-edit {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.title-with-edit h4 {
  margin: 0;
}

.edit-icon-btn {
  background: transparent;
  border: none;
  color: #9ca3af;
  padding: 2px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: all 0.15s ease;
}

.edit-icon-btn:hover {
  background: #f3f4f6;
  color: #299de0;
}

.edit-icon-btn .material-symbols-outlined {
  font-size: 16px;
}

.edit-name-wrap {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.input-sm {
  padding: 4px 8px;
  font-size: 14px;
  height: 28px;
  width: 150px;
}

.btn-icon-small {
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.btn-icon-small .material-symbols-outlined {
  font-size: 16px;
  font-weight: 700;
}

.btn-icon-ok {
  color: #059669;
  background: #ecfdf5;
}

.btn-icon-ok:hover {
  background: #d1fae5;
}

.btn-icon-cancel {
  color: #ef4444;
  background: #fef2f2;
}

.btn-icon-cancel:hover {
  background: #fee2e2;
}

.hc-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
}

.status-pill .material-symbols-outlined {
  font-size: 16px;
}

.status-ok {
  color: #059669;
}

.status-missing {
  color: #9ca3af;
}

.hc-bottom {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px dashed #e8eff3;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hc-date {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 600;
}

.btn-outline {
  background: #ffffff;
  border: 1px solid #299de0;
  color: #299de0;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-outline:hover {
  background: #eff6ff;
}

.hc-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-top: 4px;
}

.hc-metric-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #059669;
  font-size: 11px;
  font-weight: 700;
}

.hc-metric-chip .material-symbols-outlined {
  font-size: 13px;
}

.hc-metric-neutral {
  background: #eff6ff;
  color: #2563eb;
}

</style>