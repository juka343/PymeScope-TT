<script setup>
import { ref, onMounted } from "vue";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
import { useRouter, useRoute } from "vue-router";
import { db } from "@/firebase/config";
import { doc, getDoc, setDoc, collection, query, orderBy, limit, getDocs, where, addDoc, serverTimestamp } from "firebase/firestore";

const router = useRouter();
const route = useRoute();
const getRouteName = (baseName) => route.path.includes('dashboard-multi') ? `${baseName}Multi` : baseName;
const projectId = route.params.id_proyecto;

const isProcessing = ref(false);
const errorBanner = ref("");
const formularioEnviado = ref(false);

const formatMoney = (val) => {
  if (!val && val !== 0) return "$0.00";
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
  }).format(val);
};

const projectConfig = ref({
  periodicidad: "Cargando...",
  periodoBase: "Cargando...",
  periodoBaseId: route.query.periodoBaseId || null,
  periodoProyectado: "Cargando...",
  inflacionEsperada: 0,
  resultsUrl: "",
  utilidadNetaProforma: 0,
  ventasIncrementoPct: 0,
});

const bgDocIdRef = ref(null);

onMounted(async () => {
  window.scrollTo(0, 0);
  projectConfig.value.periodoBase = route.query.label || "Último disponible";

  const isHistory = route.query.isHistory === 'true';
  const lsKeyConfig = isHistory ? 'history_balance_config' : 'current_balance_config';
  const savedConfig = route.query.modo === 'editar' ? JSON.parse(localStorage.getItem(lsKeyConfig) || '{}') : null;
  
  if (route.query.modo === 'editar') {
    bgDocIdRef.value = savedConfig?.bgId || null;
  }

  if (projectId) {
    try {
      // 1. Obtener la periodicidad del proyecto
      const projectDocRef = doc(db, "proyectos", projectId);
      const projectDocSnap = await getDoc(projectDocRef);
      if (projectDocSnap.exists()) {
        projectConfig.value.periodicidad = projectDocSnap.data().periodicidad || "mensual";
      }

      // 2. Obtener URL del Balance General (PDF Base) del periodo configurado
      if (projectConfig.value.periodoBaseId) {
        const periodDocRef = doc(db, "proyectos", projectId, "periodos", projectConfig.value.periodoBaseId);
        const periodDocSnap = await getDoc(periodDocRef);
        if (periodDocSnap.exists()) {
          const pData = periodDocSnap.data();
          projectConfig.value.resultsUrl = pData.balanceFile?.url || "";
        }
      }

      // 3. Obtener datos de la proyección previa (Estado de Resultados)
      let proyDoc = null;
      // Priorizar erId de la URL (si venimos de Continuar al Balance) o del config guardado (si es edición)
      const erId = route.query.erId || savedConfig?.erId || null;

      if (erId) {
        const erDocRef = doc(db, "proyectos", projectId, "proyecciones_er", erId);
        const erSnap = await getDoc(erDocRef);
        if (erSnap.exists()) proyDoc = erSnap;
      }

      if (!proyDoc) {
        const proyeccionesERRef = collection(db, "proyectos", projectId, "proyecciones_er");
        let qProy = query(
          proyeccionesERRef, 
          orderBy("created_at", "desc"), 
          limit(1)
        );
        let proySnapshot = await getDocs(qProy);

        // Fallback: si no hay en proyecciones_er, buscar en la colección antigua
        if (proySnapshot.empty) {
          const proyeccionesOldRef = collection(db, "proyectos", projectId, "proyecciones");
          qProy = query(
            proyeccionesOldRef, 
            where("tipo_proyeccion", "==", "estado_resultados"),
            orderBy("created_at", "desc"), 
            limit(1)
          );
          proySnapshot = await getDocs(qProy);
        }
        if (!proySnapshot.empty) proyDoc = proySnapshot.docs[0];
      }

      if (proyDoc) {
        const proyData = proyDoc.data();

        // FIX 3: Validar que el ER corresponde al mismo periodo base seleccionado
        const erPeriodoBase = proyData.periodo_base_id;
        const periodoBaseSeleccionado = projectConfig.value.periodoBaseId;
        if (erPeriodoBase && periodoBaseSeleccionado && erPeriodoBase !== periodoBaseSeleccionado) {
          errorBanner.value = `⚠️ Advertencia: El Estado de Resultados Proforma disponible fue calculado sobre un periodo base diferente al seleccionado. Los valores de utilidad y ventas pueden no ser consistentes con este balance.`;
        }

        projectConfig.value.periodoProyectado = proyData.periodo_proyectado;
        projectConfig.value.inflacionEsperada = proyData.inflacion_esperada || proyData.inflacion_especada || 0;
        projectConfig.value.utilidadNetaProforma = proyData.resultados?.utilidad_neta || 0;
        
        // FIX 1: Buscar la fila de ventas por concepto en vez de asumir el índice 0
        const tablas = proyData.resultados?.tablas_proyectadas || [];
        const filaVentas = tablas.find(f => 
          f.concepto === "Ventas netas / Ingresos por servicios" ||
          f.concepto?.toLowerCase().includes("ventas")
        );
        if (filaVentas && filaVentas.valor_base !== 0) {
          projectConfig.value.ventasIncrementoPct = ((filaVentas.valor_proyectado / filaVentas.valor_base) - 1) * 100;
        }
      } else {
        errorBanner.value = "Atención: No se encontró una proyección de Estado de Resultados previa para este proyecto.";
      }
    } catch (error) {
      console.error("Error al cargar datos del balance:", error);
      errorBanner.value = "Error al conectar con la base de datos de Firebase.";
    }
  }

  // Lógica para modo Edición
  if (route.query.modo === 'editar') {
    const lsKeySupuestos = isHistory ? 'history_balance_supuestos' : 'current_balance_supuestos';
    let savedSupuestos = localStorage.getItem(lsKeySupuestos);
    let sup = null;

    if (savedSupuestos) {
      sup = JSON.parse(savedSupuestos);
    } else {
      try {
        const proyeccionesBGRef = collection(db, "proyectos", projectId, "proyecciones_bg");
        const qProy = query(proyeccionesBGRef, orderBy("created_at", "desc"), limit(1));
        let proyDoc = null;
        if (bgDocIdRef.value) {
          const docRef = doc(db, "proyectos", projectId, "proyecciones_bg", bgDocIdRef.value);
          const snap = await getDoc(docRef);
          if (snap.exists()) proyDoc = snap;
        }

        if (!proyDoc) {
          const proyeccionesBGRef = collection(db, "proyectos", projectId, "proyecciones_bg");
          const qProy = query(proyeccionesBGRef, orderBy("created_at", "desc"), limit(1));
          const proySnapshot = await getDocs(qProy);
          if (!proySnapshot.empty) proyDoc = proySnapshot.docs[0];
        }

        if (proyDoc) {
          sup = proyDoc.data().supuestos;
        }
      } catch (err) {
        console.error("Error al recuperar supuestos de Balance de Firestore:", err);
      }
    }

    if (sup) {
      const applySupuestos = (targetRef, savedList) => {
        if (!savedList) return;
        targetRef.value = targetRef.value.map(item => {
          const match = savedList.find(s => s.concepto === item.concepto);
          if (match) {
            const isMantener = !!(match.mantener_igual || match.mantenerIgual);
            return {
              ...item,
              variacion: isMantener ? "" : match.variacion,
              mantener_igual: isMantener
            };
          }
          return item;
        });
      };

      applySupuestos(activoCirculante, sup.activo_circulante || sup.activos_circulantes);
      applySupuestos(activoNoCirculante, sup.activo_no_circulante || sup.activos_no_circulantes);
      applySupuestos(pasivoCorto, sup.pasivo_corto_plazo);
      applySupuestos(pasivoLargo, sup.pasivo_largo_plazo);
      applySupuestos(capitalContribuido, sup.capital_contribuido);
      applySupuestos(capitalGanadoEditable, sup.capital_ganado);
    }
  }
});

const activoCirculante = ref([
  { concepto: "Caja", variacion: "", mantener_igual: false },
  { concepto: "Bancos", variacion: "", mantener_igual: false },
  { concepto: "Inversiones temporales", variacion: "", mantener_igual: false },
  { concepto: "Cuentas por cobrar a clientes", variacion: "", mantener_igual: false },
  { concepto: "Otras cuentas por cobrar (deudores diversos)", variacion: "", mantener_igual: false },
  { concepto: "IVA por acreditar", variacion: "", mantener_igual: false },
  { concepto: "IVA acreditable", variacion: "", mantener_igual: false },
  { concepto: "Inventarios", variacion: "", mantener_igual: false },
  { concepto: "Anticipo a proveedores", variacion: "", mantener_igual: false },
  { concepto: "Papelería y artículos de escritorio", variacion: "", mantener_igual: false },
  { concepto: "Propaganda y publicidad", variacion: "", mantener_igual: false },
  { concepto: "Seguros y fianzas", variacion: "", mantener_igual: false },
  { concepto: "Rentas pagadas por anticipado", variacion: "", mantener_igual: false },
  { concepto: "Intereses pagados por anticipado", variacion: "", mantener_igual: false },
  { concepto: "Impuestos y derechos", variacion: "", mantener_igual: false },
]);

const activoNoCirculante = ref([
  { concepto: "Terrenos", variacion: "", mantener_igual: false },
  { concepto: "Edificios", variacion: "", mantener_igual: false },
  { concepto: "Maquinaria y equipo", variacion: "", mantener_igual: false },
  { concepto: "Equipo de transporte", variacion: "", mantener_igual: false },
  { concepto: "Mobiliario y equipo de oficina", variacion: "", mantener_igual: false },
  { concepto: "Equipo de cómputo", variacion: "", mantener_igual: false },
  { concepto: "Patentes", variacion: "", mantener_igual: false },
  { concepto: "Marcas", variacion: "", mantener_igual: false },
  { concepto: "Crédito mercantil", variacion: "", mantener_igual: false },
  { concepto: "Franquicias", variacion: "", mantener_igual: false },
  { concepto: "Licencias de software", variacion: "", mantener_igual: false },
  { concepto: "Depósitos en garantía", variacion: "", mantener_igual: false },
]);

const pasivoCorto = ref([
  { concepto: "Cuentas por pagar a proveedores", variacion: "", mantener_igual: false },
  { concepto: "Préstamo bancario / Deuda a corto plazo", variacion: "", mantener_igual: false },
  { concepto: "Acreedores diversos", variacion: "", mantener_igual: false },
  { concepto: "Impuestos a la utilidad por pagar", variacion: "", mantener_igual: false },
  { concepto: "IVA por causar o trasladar", variacion: "", mantener_igual: false },
  { concepto: "IVA causado o trasladado", variacion: "", mantener_igual: false },
  { concepto: "Anticipo de clientes", variacion: "", mantener_igual: false },
  { concepto: "Rentas cobradas por anticipado", variacion: "", mantener_igual: false },
  { concepto: "Intereses cobrados por anticipado", variacion: "", mantener_igual: false },
]);

const pasivoLargo = ref([
  { concepto: "Acreedores diversos a largo plazo", variacion: "", mantener_igual: false },
  { concepto: "Cuentas por pagar a largo plazo", variacion: "", mantener_igual: false },
  { concepto: "Cobros anticipados a largo plazo", variacion: "", mantener_igual: false },
]);

const capitalContribuido = ref([
  { concepto: "Capital social", variacion: "", mantener_igual: false },
  { concepto: "Aportaciones para futuros aumentos de capital", variacion: "", mantener_igual: false },
  { concepto: "Prima en venta de acciones", variacion: "", mantener_igual: false },
  { concepto: "Donaciones", variacion: "", mantener_igual: false },
]);

const capitalGanadoEditable = ref([
  { concepto: "Reserva legal", variacion: "", mantener_igual: false },
  { concepto: "Otros resultados integrales", variacion: "", mantener_igual: false },
]);

function cancelar() {
  router.push({ name: getRouteName("proyecciones") });
}

function isFilaVacia(item) {
  return !item.mantener_igual && (item.variacion === "" || item.variacion === null || item.variacion === undefined);
}

async function generarProyeccion() {
  if (!projectConfig.value.resultsUrl) {
    errorBanner.value = "No se encontró el PDF base del Balance General.";
    return;
  }

  formularioEnviado.value = true;

  // Validar que todas las filas editables tengan variación o estén marcadas
  const todasLasFilas = [
    ...activoCirculante.value,
    ...activoNoCirculante.value,
    ...pasivoCorto.value,
    ...pasivoLargo.value,
    ...capitalContribuido.value,
    ...capitalGanadoEditable.value,
  ];

  const hayFilasVacias = todasLasFilas.some(isFilaVacia);
  if (hayFilasVacias) {
    errorBanner.value = "Todos los campos deben tener una variación (%) o estar marcados como \"Mantener igual\".";
    return;
  }

  isProcessing.value = true;
  errorBanner.value = "";

  const payload = {
    project_id: projectId,
    period_id: projectConfig.value.periodoBaseId,
    results_url: projectConfig.value.resultsUrl,
    periodo_proyectado_label: projectConfig.value.periodoProyectado,
    inflacion_esperada: parseFloat(projectConfig.value.inflacionEsperada) || 0,
    utilidad_neta_proforma: parseFloat(projectConfig.value.utilidadNetaProforma) || 0,
    ventas_proy_incremento_pct: parseFloat(projectConfig.value.ventasIncrementoPct) || 0,
    activo_circulante: activoCirculante.value.map(s => ({
      concepto: s.concepto,
      variacion: parseFloat(s.variacion) || 0,
      mantener_igual: s.mantener_igual
    })),
    activo_no_circulante: activoNoCirculante.value.map(s => ({
      concepto: s.concepto,
      variacion: parseFloat(s.variacion) || 0,
      mantener_igual: s.mantener_igual
    })),
    pasivo_corto_plazo: pasivoCorto.value.map(s => ({
      concepto: s.concepto,
      variacion: parseFloat(s.variacion) || 0,
      mantener_igual: s.mantener_igual
    })),
    pasivo_largo_plazo: pasivoLargo.value.map(s => ({
      concepto: s.concepto,
      variacion: parseFloat(s.variacion) || 0,
      mantener_igual: s.mantener_igual
    })),
    capital_contribuido: capitalContribuido.value.map(s => ({
      concepto: s.concepto,
      variacion: parseFloat(s.variacion) || 0,
      mantener_igual: s.mantener_igual
    })),
    capital_ganado: [
      ...capitalGanadoEditable.value.map(s => ({
        concepto: s.concepto,
        variacion: parseFloat(s.variacion) || 0,
        mantener_igual: s.mantener_igual
      })),
      { concepto: "Utilidades o pérdidas de ejercicios anteriores", variacion: 0, mantener_igual: true },
      { concepto: "Utilidad o pérdida del ejercicio", variacion: 0, mantener_igual: true }
    ]
  };

  try {
    const response = await fetch(`${API_BASE_URL}/projections/balance-general`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || "Error en el servidor al calcular el balance");
    }

    const resultados = await response.json();

    // Leer el erId del ER asociado para establecer la relación directa
    const erConfig = JSON.parse(localStorage.getItem('current_projection_config') || '{}');
    const erDocId = erConfig.erId || null;

    // Construir objeto para guardar en Firestore
    const datos_proyeccion = {
      tipo_proyeccion: "balance_general",
      periodo_proyectado: projectConfig.value.periodoProyectado,
      inflacion_esperada: parseFloat(projectConfig.value.inflacionEsperada) || 0,
      periodo_base_id: projectConfig.value.periodoBaseId,
      er_id: erDocId,
      supuestos: {
        ventas_incremento_pct: payload.ventas_proy_incremento_pct,
        utilidad_neta_proforma: payload.utilidad_neta_proforma,
        activos_circulantes: payload.activo_circulante,
        activos_no_circulantes: payload.activo_no_circulante,
        pasivo_corto_plazo: payload.pasivo_corto_plazo,
        pasivo_largo_plazo: payload.pasivo_largo_plazo,
        capital_contribuido: payload.capital_contribuido,
        capital_ganado: payload.capital_ganado
      },
      resultados: {
        tablas_proyectadas: resultados.tablas_proyectadas,
        total_activo: resultados.total_activo,
        total_pasivo: resultados.total_pasivo,
        total_capital: resultados.total_capital,
        fer: resultados.fer,
        utilidad_neta_proforma: payload.utilidad_neta_proforma
      },
      created_at: serverTimestamp()
    };

    // Guardar en Firestore (Crear nuevo o Actualizar existente)
    const modoEditar = route.query.modo === 'editar';
    const isHistory = route.query.isHistory === 'true';
    let bgId = bgDocIdRef.value;

    if (modoEditar && bgId) {
      const bgDocRef = doc(db, "proyectos", projectId, "proyecciones_bg", bgId);
      await setDoc(bgDocRef, datos_proyeccion, { merge: true });
      console.log("PROYECCIÓN BG ACTUALIZADA EN FIRESTORE:", bgId);
    } else {
      const proyeccionesBGRef = collection(db, "proyectos", projectId, "proyecciones_bg");
      const bgDocRef = await addDoc(proyeccionesBGRef, datos_proyeccion);
      bgId = bgDocRef.id;
      console.log("PROYECCIÓN BG GUARDADA EN FIRESTORE:", bgId);
    }

    // Persistencia consistente con arquitectura
    const prefix = isHistory ? 'history' : 'current';

    localStorage.setItem(`${prefix}_balance_result`, JSON.stringify(resultados));
    localStorage.setItem(`${prefix}_balance_config`, JSON.stringify({
      periodoBase: projectConfig.value.periodoBase,
      periodoProyectado: projectConfig.value.periodoProyectado,
      inflacion: projectConfig.value.inflacionEsperada,
      periodoBaseId: projectConfig.value.periodoBaseId,
      bgId: bgId,
    }));
    localStorage.setItem(`${prefix}_balance_supuestos`, JSON.stringify(payload));
    
    // Al regenerar los datos, borramos el caché de la IA para forzar un nuevo análisis del FER
    localStorage.removeItem(`${prefix}_balance_ai`);

    router.push({ 
      name: getRouteName("ProyeccionProformaBalanceGeneral"),
      params: { id_proyecto: projectId },
      query: isHistory ? { isHistory: 'true' } : {}
    });
  } catch (error) {
    console.error("Error al generar la proyección:", error);
    errorBanner.value = error.message || "Error al conectar con el motor de proyecciones.";
  } finally {
    isProcessing.value = false;
  }
}
</script>

<template>
  <div class="wrap">
    <!-- Overlay de Carga (Arquitectura Consistente) -->
    <div v-if="isProcessing" class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <h3>Generando Balance General Proforma...</h3>
        <p>Procesando OCR del documento base y aplicando supuestos financieros.</p>
      </div>
    </div>

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
          <span>Periodo base: {{ projectConfig.periodoBase }}</span>
        </div>
      </div>
    </div>

    <!-- Alerta de Error -->
    <div v-if="errorBanner" class="form-error-banner">
      <span class="material-symbols-outlined">error</span>
      <p>{{ errorBanner }}</p>
      <button class="close-error" @click="errorBanner = ''">×</button>
    </div>

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon">settings</span>
        <h3>Configuración general de la proyección</h3>
      </div>

      <p class="section-helper">
        Estos valores provienen del Estado de Resultados Proforma previo para garantizar la consistencia contable.
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

    <section class="card">
      <div class="section-title">
        <span class="material-symbols-outlined section-icon icon-blue">account_balance_wallet</span>
        <h3>Supuestos por cuenta – Activos</h3>
      </div>
      <p class="method-hint">
        <span class="material-symbols-outlined" style="font-size:13px;vertical-align:-2px">info</span>
        Variación en 0% aplica automáticamente el <strong>{{ projectConfig.ventasIncrementoPct.toFixed(1) }}%</strong> del ER proforma (método % de Ventas).
      </p>

      <div class="group-label">Activo circulante</div>
      <div class="assumptions-table">
        <div class="assumptions-head">
          <div class="col-concepto">Concepto</div>
          <div class="col-variacion center">Variación (%)</div>
          <div class="col-check right">Mantener igual</div>
        </div>

        <div v-for="(item, idx) in activoCirculante" :key="`ac-${idx}`" class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="item.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(item) }" type="number" step="0.1" placeholder="Auto" :disabled="item.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(item)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap">
            <input v-model="item.mantener_igual" class="checkbox" type="checkbox" :disabled="!item.mantener_igual && (item.variacion !== null && item.variacion !== '' )" />
          </div>
        </div>
      </div>

      <div class="group-label group-label-bordered">Activo no circulante</div>
      <div class="assumptions-table">
        <div v-for="(item, idx) in activoNoCirculante" :key="`anc-${idx}`" class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="item.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(item) }" type="number" step="0.1" placeholder="Auto" :disabled="item.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(item)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap">
            <input v-model="item.mantener_igual" class="checkbox" type="checkbox" :disabled="!item.mantener_igual && (item.variacion !== null && item.variacion !== '' )" />
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

        <div v-for="(item, idx) in pasivoCorto" :key="`pc-${idx}`" class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="item.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(item) }" type="number" step="0.1" placeholder="Auto" :disabled="item.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(item)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap">
            <input v-model="item.mantener_igual" class="checkbox" type="checkbox" :disabled="!item.mantener_igual && (item.variacion !== null && item.variacion !== '' )" />
          </div>
        </div>
      </div>

      <div class="group-label group-label-bordered">Pasivo a largo plazo</div>
      <div class="assumptions-table">
        <div v-for="(item, idx) in pasivoLargo" :key="`pl-${idx}`" class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="item.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(item) }" type="number" step="0.1" placeholder="Auto" :disabled="item.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(item)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap">
            <input v-model="item.mantener_igual" class="checkbox" type="checkbox" :disabled="!item.mantener_igual && (item.variacion !== null && item.variacion !== '' )" />
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

        <div v-for="(item, idx) in capitalContribuido" :key="`cc-${idx}`" class="assumptions-row">
          <div class="col-concepto">
            <div class="concept-text">{{ item.concepto }}</div>
          </div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="item.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(item) }" type="number" step="0.1" placeholder="Auto" :disabled="item.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(item)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap">
            <input v-model="item.mantener_igual" class="checkbox" type="checkbox" :disabled="!item.mantener_igual && (item.variacion !== null && item.variacion !== '' )" />
          </div>
        </div>
      </div>

      <div class="group-label group-label-bordered">Capital ganado</div>
      <div class="assumptions-table">
        <!-- 
        <div class="assumptions-row">
          <div class="col-concepto"><div class="concept-text">Utilidades de ejercicios anteriores</div></div>
          <div class="col-variacion"><input class="input input-disabled" type="text" placeholder="Inmovilizado" disabled /></div>
          <div class="col-check check-wrap"><span class="mini-tag mini-tag-gray">Automático</span></div>
        </div> 
        -->

        <div v-for="(item, idx) in capitalGanadoEditable" :key="`cg-${idx}`" class="assumptions-row">
          <div class="col-concepto"><div class="concept-text">{{ item.concepto }}</div></div>
          <div class="col-variacion">
            <div class="input-with-suffix">
              <input v-model="item.variacion" class="input" :class="{ 'input-error': formularioEnviado && isFilaVacia(item) }" type="number" step="0.1" placeholder="Auto" :disabled="item.mantener_igual" />
              <span class="suffix">%</span>
            </div>
            <span v-if="formularioEnviado && isFilaVacia(item)" class="required-badge">* Obligatorio</span>
          </div>
          <div class="col-check check-wrap"><input v-model="item.mantener_igual" class="checkbox" type="checkbox" :disabled="!item.mantener_igual && (item.variacion !== null && item.variacion !== '' )" /></div>
        </div>

        <div class="assumptions-row">
          <div class="col-concepto"><div class="concept-text">Utilidad neta proforma</div></div>
          <div class="col-variacion">
            <input 
              class="input input-disabled" 
              type="text" 
              :value="formatMoney(projectConfig.utilidadNetaProforma)" 
              disabled 
              style="opacity: 0.65; color: var(--text-tertiary);"
            />
          </div>
          <div class="col-check check-wrap"><span class="mini-tag mini-tag-blue">Cálculo extraído del Estado de Resultados Proforma</span></div>
        </div>
      </div>
    </section>

    <div class="actions">
      <button class="btn-secondary" type="button" @click="cancelar" :disabled="isProcessing">Cancelar</button>
      <button class="btn-primary" type="button" @click="generarProyeccion" :disabled="isProcessing">
        <span class="material-symbols-outlined" v-if="!isProcessing">auto_graph</span>
        <span class="material-symbols-outlined" v-else>sync</span>
        <span>{{ isProcessing ? 'Procesando...' : 'Generar proyección proforma' }}</span>
      </button>
    </div>

    <footer class="foot">
      <p>
        Las proyecciones son estimaciones basadas en los supuestos ingresados.<br />
        Los Fondos Externos Requeridos (FER) se calculan automáticamente para equilibrar el balance.
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

.icon-blue { color: #2563eb; }
.icon-indigo { color: #4f46e5; }
.icon-amber { color: #f59e0b; }

.section-helper {
  margin: 0 0 18px;
  color: #507c95;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.6;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field label {
  color: #0e161b;
  font-size: 13px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.02em;
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


.method-hint {
  margin: -6px 0 12px;
  color: #6b7c8d;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
}

.method-hint strong {
  color: #1a8ac7;
  font-weight: 700;
}

.method-hint .material-symbols-outlined {
  color: #94a3b8;
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
  font-size: 14px;
  font-weight: 700;
  color: #0e161b;
  line-height: 1.5;
}

.check-wrap {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-right: 14px;
}

.checkbox {
  width: 16px;
  height: 16px;
  accent-color: #299de0;
  cursor: pointer;
}

.input-with-suffix {
  position: relative;
}

.input {
  width: 100%;
  height: 42px;
  border: 1px solid #d1dee6;
  border-radius: 10px;
  background: #ffffff;
  color: #0e161b;
  font-size: 14px;
  padding: 0 35px 0 14px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.input:focus {
  border-color: #299de0;
  box-shadow: 0 0 0 3px rgba(41, 157, 224, 0.12);
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

.mini-tag {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 900;
  text-transform: uppercase;
}

.mini-tag-gray { background: #f1f5f9; color: #64748b; }
.mini-tag-blue { background: #eff6ff; color: #2563eb; }

.group-label {
  margin: 15px 0 8px;
  font-size: 11px;
  font-weight: 900;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.group-label-bordered {
  padding-top: 15px;
  border-top: 1px dashed #e2e8f0;
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
.btn-primary:disabled, .btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }

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

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #299de0;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

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

.foot {
  margin: 4px 0 22px;
  text-align: center;
  color: #9ca3af;
  font-weight: 700;
  font-size: 12px;
}

.foot p { margin: 0; line-height: 1.6; }

@media (min-width: 768px) {
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
  .center { text-align: center; }
  .right { text-align: right; }
  .check-wrap { justify-content: flex-end; padding-right: 14px; }
}

@media (min-width: 1200px) {
  .config-grid { grid-template-columns: repeat(4, 1fr); }
}
</style>
