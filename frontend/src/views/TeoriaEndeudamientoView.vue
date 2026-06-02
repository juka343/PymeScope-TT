<script setup>
import { computed, ref } from "vue";



const videos = ref([
  {
    title: "Video: Deuda MALA vs Deuda BUENA y Apalancamiento - Cómo ser rico usando la deuda!",
    youtubeUrl: "https://www.youtube.com/watch?v=7k1D4dCtkW0",
    duration: "6:36",
  },
  {
    title: "Video: ¿Qué es el APALANCAMIENTO FINANCIERO? ➕ EJEMPLO PRACTICO ✅",
    youtubeUrl: "https://www.youtube.com/watch?v=axF8URaTNuM",
    duration: "6:33",
  },
  {
    title: "Video: RAZONES FINANCIERAS DE APALANCAMIENTO | FINANZAS BÁSICAS | Contabilidad para no contadores",
    youtubeUrl: "https://www.youtube.com/watch?v=9GvkvKxyhs8", 
    duration: "13:27",
  },
]);

const resources = ref([
  {
    name: "Razones de apalancamiento, deuda y cobertura",
    meta: "FCA UAQ • PDF",
    url: "https://fca.uaq.mx/docs/ConvocatoriasLicenciatura/2023-2/GUIAS/LAF04.pdf",
    type: "pdf",
  },
  {
    name: "Las 10 razones financieras (guía completa)",
    meta: "FCCA UMSNH • PDF",
    url: "https://www.fcca.umich.mx/descargas/apuntes/academia%20de%20finanzas/finanzas%20i%20mauricio%20a.%20chagolla%20farias/10%20razones%20financieras.pdf",
    type: "pdf",
  },
]);

// ===== YouTube thumbnail dinámico =====
const thumbFallback = ref({}); // { [videoId]: true } -> usa hqdefault si falla maxres

function getYouTubeId(url) {
  if (!url) return null;

  // youtu.be/<id>
  const short = url.match(/youtu\.be\/([a-zA-Z0-9_-]{6,})/);
  if (short?.[1]) return short[1];

  // watch?v=<id>
  const watch = url.match(/[?&]v=([a-zA-Z0-9_-]{6,})/);
  if (watch?.[1]) return watch[1];

  // /embed/<id>
  const embed = url.match(/youtube\.com\/embed\/([a-zA-Z0-9_-]{6,})/);
  if (embed?.[1]) return embed[1];

  // /shorts/<id>
  const shorts = url.match(/youtube\.com\/shorts\/([a-zA-Z0-9_-]{6,})/);
  if (shorts?.[1]) return shorts[1];

  return null;
}

function thumbUrl(youtubeUrl) {
  const id = getYouTubeId(youtubeUrl);
  if (!id) return ""; // o pon un placeholder

  const useFallback = Boolean(thumbFallback.value[id]);
  const file = useFallback ? "hqdefault.jpg" : "maxresdefault.jpg";
  return `https://i.ytimg.com/vi/${id}/${file}`;
}

function onThumbError(youtubeUrl) {
  const id = getYouTubeId(youtubeUrl);
  if (!id) return;
  thumbFallback.value[id] = true;
}

function openVideo(url) {
  if (!url) return;
  window.open(url, "_blank", "noopener,noreferrer");
}

const yearLabel = computed(() => new Date().getFullYear());
</script>

<template>
  <div class="learning-page">
    <main class="container">
      <!-- Header -->
      <header class="page-title">
        <h1>
          <span class="kicker">Centro de aprendizaje</span>
          <span class="headline">Endeudamiento</span>
        </h1>
      </header>

      <div class="grid">
        <!-- Left -->
        <section class="left">
          <!-- Card: definición -->
          <article class="card">
            <h2 class="card-title">
              <span class="material-symbols-outlined icon">info</span>
              ¿Qué es y por qué es importante?
            </h2>

            <div class="card-text">
              <p>
            El endeudamiento es el nivel en que una empresa utiliza recursos ajenos para financiar sus
            operaciones y sus activos. Analizar esta razón permite conocer qué tan dependiente es el negocio
            de sus deudas y qué tan capaz es de cumplir con los compromisos financieros que ha adquirido,
            tanto en el corto como en el largo plazo.
            </p>
            <p>
            Para las pequeñas y medianas empresas (PYMES), controlar el endeudamiento es clave porque un uso
            excesivo de deuda puede comprometer la estabilidad financiera, aumentar el riesgo y reducir la
            capacidad de maniobra ante imprevistos. Evaluar estas razones ayuda a identificar si la empresa
            mantiene un equilibrio adecuado entre capital propio y financiamiento externo, y si sus utilidades
            son suficientes para sostener el costo de sus obligaciones.
            </p>
            </div>
          </article>

          <!-- Card: fórmulas -->
          <article class="card">
            <h2 class="card-title">
              <span class="material-symbols-outlined icon">calculate</span>
              Principales Fórmulas
            </h2>

            <div class="formula-list">
                <div class="formula">
                <h3 class="formula-label">Apalancamiento o Deuda sobre el Activo Total</h3>
                <p class="formula-eq">(Pasivo Total / Activo Total)</p>
                <p class="formula-desc">
                    Mide la proporción de los activos de la empresa que está financiada con deuda.
                </p>
                </div>

                <div class="formula">
                <h3 class="formula-label">Razón de Cobertura de Intereses</h3>
                <p class="formula-eq">(Utilidad de Operación / Intereses)</p>
                <p class="formula-desc">
                    Indica cuántas veces la utilidad de operación puede cubrir el pago de los intereses.
                </p>
                </div>

                <div class="formula">
                <h3 class="formula-label">Razón de Estabilidad Financiera</h3>
                <p class="formula-eq">(Pasivo Total / Capital Social)</p>
                <p class="formula-desc">
                    Evalúa el equilibrio entre el capital propio de la empresa y el financiamiento obtenido mediante deuda.
                </p>
                </div>
            </div>
          </article>
        </section>

        <!-- Right -->
        <aside class="right">
          <!-- Video Card -->
          <article class="card card-compact">
            <h2 class="card-title compact">
              <span class="material-symbols-outlined icon">play_circle</span>
              Material Audiovisual
            </h2>

            <div class="video-list">
              <button
                v-for="(v, idx) in videos"
                :key="idx"
                type="button"
                class="video-item"
                @click="openVideo(v.youtubeUrl)"
              >
                <div class="thumb">
                  <img
                    class="thumb-img"
                    :src="thumbUrl(v.youtubeUrl)"
                    :alt="`Thumbnail: ${v.title}`"
                    @error="onThumbError(v.youtubeUrl)"
                  />

                  <div class="thumb-overlay">
                    <div class="play">
                      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                        <path d="M8 5v14l11-7z"></path>
                      </svg>
                    </div>
                  </div>

                  <span class="duration">{{ v.duration }}</span>
                </div>

                <p class="video-title">{{ v.title }}</p>
              </button>
            </div>
          </article>

          <!-- Resources -->
          <article class="card card-compact">
            <h2 class="card-title compact">
              <span class="material-symbols-outlined icon">folder_open</span>
              Recursos Adicionales
            </h2>

            <ul class="resource-list">
              <li v-for="(r, idx) in resources" :key="idx">
                <a class="resource-item" :href="r.url" target="_blank" rel="noopener noreferrer">
                  <div class="resource-ico" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none">
                      <path
                        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>
                  </div>

                  <div class="resource-meta">
                    <p class="resource-name">{{ r.name }}</p>
                    <p class="resource-sub">{{ r.meta }}</p>
                  </div>
                </a>
              </li>
            </ul>
          </article>
        </aside>
      </div>

      <footer class="footer">
        <p>© {{ yearLabel }} Learning Center - Rentabilidad para PYMES. Todos los derechos reservados.</p>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.learning-page {
  background: #fcfcfc;
  color: #333;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

.container {
  width: min(1200px, 92vw);
  margin: 0 auto;
  padding: 48px 0 64px;
}

/* Title */
.page-title {
  margin-bottom: 28px;
}

.kicker {
  display: block;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #2d9cdb;
  margin-bottom: 6px;
}

.headline {
  display: block;
  font-size: clamp(44px, 6vw, 72px);
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1.02;

  /* gradient text */
  background: linear-gradient(90deg, #111827, #1f2937, #2d9cdb);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

/* Layout grid */
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 22px;
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: 6fr 4fr;
    align-items: start;
  }
}

.left,
.right {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Card */
.card {
  background: #fff;
  border: 1px solid #f0f2f5;
  border-radius: 14px;
  padding: 22px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
}

.card-compact {
  padding: 16px;
}

.card-title {
  margin: 0 0 14px;
  font-size: 22px;
  font-weight: 800;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-title.compact {
  font-size: 18px;
  margin-bottom: 12px;
}

.icon {
  color: #299de0;
  font-size: 24px;
}

/* Text */
.card-text {
  color: #4b5563;
  line-height: 1.75;
  display: grid;
  gap: 12px;
}

.card-text p {
  margin: 0;
}

/* Formulas */
.formula-list {
  display: grid;
  gap: 14px;
}

.formula {
  background: #f8fafc;
  border-left: 4px solid #2d9cdb;
  border-radius: 10px;
  padding: 16px;
}

.formula-label {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6b7280;
}

.formula-eq {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 16px;
  color: #111827;
  word-break: break-word;
}

.formula-desc {
  margin: 10px 0 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
}

/* Videos */
.video-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-item {
  appearance: none;
  border: none;
  background: transparent;
  text-align: left;
  padding: 0;
  cursor: pointer;
}

.video-item + .video-item {
  border-top: 1px solid #f0f2f5;
  padding-top: 16px;
}

.thumb {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background: #e5e7eb;
  aspect-ratio: 16 / 9;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transform: scale(1);
  transition: transform 0.25s ease;
}

.video-item:hover .thumb-img {
  transform: scale(1.04);
}

.thumb-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.28);
  display: grid;
  place-items: center;
  transition: background 0.2s ease;
}

.video-item:hover .thumb-overlay {
  background: rgba(0, 0, 0, 0.38);
}

.play {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 999px;
  display: grid;
  place-items: center;
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.18);
  transform: scale(1);
  transition: transform 0.2s ease;
}

.video-item:hover .play {
  transform: scale(1.06);
}

.play svg {
  width: 28px;
  height: 28px;
  color: #299de0;
  margin-left: 2px;
}

.duration {
  position: absolute;
  right: 10px;
  bottom: 10px;
  background: rgba(0, 0, 0, 0.72);
  color: white;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 8px;
}

.video-title {
  margin: 10px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.video-note {
  margin: 10px 0 0;
  font-size: 13px;
  color: #6b7280;
}

/* Resources */
.resource-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid transparent;
  text-decoration: none;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.resource-item:hover {
  background: #f9fafb;
  border-color: #f0f2f5;
}

.resource-ico {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: #299de0;
  background: #eff6ff;
  transition: background 0.15s ease, color 0.15s ease;
}

.resource-item:hover .resource-ico {
  background: #2d9cdb;
  color: white;
}

.resource-ico svg {
  width: 22px;
  height: 22px;
}

.resource-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.resource-name {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.resource-sub {
  margin: 0;
  font-size: 12px;
  color: #9ca3af;
  font-weight: 700;
}

/* Footer */
.footer {
  margin-top: 42px;
  border-top: 1px solid #f0f2f5;
  padding-top: 18px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
</style>