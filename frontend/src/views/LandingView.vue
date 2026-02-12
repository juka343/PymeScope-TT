<script setup>
import { RouterLink } from "vue-router";

import heroImage from "@/assets/images/Gemini_Generated_Image_7n5p397n5p397n5p.png";

import benefitsImage from "@/assets/images/Gemini_Generated_Image_v7l4fgv7l4fgv7l4.png";

</script>

<template>
  <div class="page">
    <nav class="nav">
      <div class="container nav-inner">
        <div class="brand">
          <span class="material-symbols-outlined brand-icon">analytics</span>
          <span class="brand-name">PymeScope</span>
        </div>

        <div class="nav-links">
          <a href="#features">Características</a>
          <a href="#process">Cómo funciona</a>

          <RouterLink to="/login" class="btn btn-primary btn-sm">
            Comenzar análisis
          </RouterLink>
        </div>

        <button class="nav-menu-btn" type="button" aria-label="Menú">
          <span class="material-symbols-outlined">menu</span>
        </button>
      </div>
    </nav>

    <section class="hero">
      <div class="container hero-grid">
        <div class="hero-copy">
          <h1 class="hero-title">
            Analiza, entiende y mejora la
            <span class="text-primary">salud financiera</span> de tu empresa
          </h1>

          <p class="hero-subtitle">
            Plataforma de análisis financiero moderna diseñada específicamente para PyMEs.
            Toma el control de tus números hoy y proyecta tu crecimiento.
          </p>

          <div class="hero-actions">
            <RouterLink to="/analisis" class="btn btn-primary btn-lg">
              Comenzar análisis
            </RouterLink>
            <a href="https://www.youtube.com/watch?v=hPr-Yc92qaY" target="_blank">
            <button class="btn btn-ghost btn-lg" type="button">
              <span class="material-symbols-outlined">play_circle</span>
              Ver demo
            </button>
            </a>

            
          </div>
        </div>

        <div class="hero-visual">
          <div class="hero-backdrop"></div>
          <div class="hero-card" role="img" aria-label="Ilustración de analista financiero">
            <div class="hero-image" :style="{ backgroundImage: `url('${heroImage}')` }"></div>
          </div>
        </div>
      </div>
    </section>

    <section id="process" class="section section-bordered">
      <div class="container">
        <div class="section-head">
          <h3 class="kicker">¿Cómo funciona la plataforma?</h3>
          <h2 class="section-title">Nuestro proceso de 3 pasos es simple</h2>
          <p class="section-subtitle">
            Desde tus datos crudos hasta decisiones estratégicas en minutos.
          </p>
        </div>

        <div class="cards-3">
          <article class="step-card">
            <div class="step-icon">
              <span class="material-symbols-outlined">cloud_upload</span>
            </div>
            <h3>Carga Automática</h3>
            <p>Sube tus estados financieros fácilmente y deja que nosotros hagamos el trabajo.</p>
          </article>

          <article class="step-card">
            <div class="step-icon">
              <span class="material-symbols-outlined">analytics</span>
            </div>
            <h3>Procesar Datos</h3>
            <p>Extraemos la información clave y calculamos indicadores financieros esenciales.</p>
          </article>

          <article class="step-card">
            <div class="step-icon">
              <span class="material-symbols-outlined">lightbulb</span>
            </div>
            <h3>Obtener Resultados</h3>
            <p>Recibe análisis detallados y visualizaciones claras para decisiones inteligentes.</p>
          </article>
        </div>
      </div>
    </section>

    <section class="section section-light">
      <div class="container split">
        <div>
          <h2 class="section-title">
            ¿Por qué es importante analizar tus finanzas?
          </h2>
          <p class="lead">
            Evita sorpresas desagradables. La mayoría de las PyMEs fracasan no por falta de ventas,
            sino por falta de visibilidad financiera. Asegura la
            longevidad de tu negocio detectando problemas a tiempo.
          </p>
        </div>

        <div class="problem-grid">
          <div class="problem-card">
            <div class="problem-icon">
              <span class="material-symbols-outlined">warning</span>
            </div>
            <div>
              <h3>Riesgos no detectados</h3>
              <p>Pasivos ocultos que crecen en silencio.</p>
            </div>
          </div>

          <div class="problem-card">
            <div class="problem-icon">
              <span class="material-symbols-outlined">credit_card_off</span>
            </div>
            <div>
              <h3>Falta de liquidez</h3>
              <p>Quedarse sin efectivo operativo.</p>
            </div>
          </div>

          <div class="problem-card">
            <div class="problem-icon">
              <span class="material-symbols-outlined">remove_circle_outline</span>
            </div>
            <div>
              <h3>Gastos hormiga</h3>
              <p>Fugas de dinero en gastos pequeños.</p>
            </div>
          </div>

          <div class="problem-card">
            <div class="problem-icon">
              <span class="material-symbols-outlined">trending_down</span>
            </div>
            <div>
              <h3>Proyecciones erróneas</h3>
              <p>Decisiones basadas en datos viejos.</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="features" class="section">
      <div class="container">
        <div class="section-head">
          <span class="kicker-alt">Potencia tu negocio</span>
          <h2 class="section-title">Características Principales</h2>
        </div>

        <div class="features-grid">
          <article class="feature">
            <div class="feature-icon">
              <span class="material-symbols-outlined">dashboard</span>
            </div>
            <h3>Panel de Control Intuitivo</h3>
            <p>Visualiza tus KPIs más importantes en un solo lugar con gráficos fáciles de entender.</p>
          </article>

          <article class="feature">
            <div class="feature-icon">
              <span class="material-symbols-outlined">ssid_chart</span>
            </div>
            <h3>Visualizaciones Comparativas</h3>
            <p>Compara periodos anteriores y detecta tendencias estacionales al instante.</p>
          </article>

          <article class="feature">
            <div class="feature-icon">
              <span class="material-symbols-outlined">description</span>
            </div>
            <h3>Reportes Automáticos</h3>
            <p>Genera reportes PDF profesionales listos para enviar a tus socios o banco.</p>
          </article>

          <article class="feature">
            <div class="feature-icon">
              <span class="material-symbols-outlined">lock_person</span>
            </div>
            <h3>Seguridad de Datos</h3>
            <p>Encriptación para asegurar que tu información financiera esté siempre protegida.</p>
          </article>

          <article class="feature">
            <div class="feature-icon">
              <span class="material-symbols-outlined">forward_10</span>
            </div>
            <h3>Proyecciones Proforma</h3>
            <p>Anticipa escenarios futuros mediante modelos dinámicos basados en tu histórico real.</p>
          </article>

          <article class="feature">
            <div class="feature-icon">
              <span class="material-symbols-outlined">psychology</span>
            </div>
            <h3>Interpretaciones Automáticas</h3>
            <p>Explicaciones claras y concisas de tus resultados, sin necesidad de ser experto.</p>
          </article>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container benefits">
        <div class="benefits-card">
          <div class="glow glow-1"></div>
          <div class="glow glow-2"></div>
          <img class="benefits-image" :src="benefitsImage" alt="Gráfica financiera positiva" />
        </div>

        <div>
          <h2 class="section-title">Beneficios tangibles para tu PyME</h2>
          <p class="lead">
            Comprende cada aspecto de tu salud financiera con un vistazo claro y conciso.
          </p>

          <ul class="checks">
            <li><span class="material-symbols-outlined ok">check_circle</span> Visibilidad Total</li>
            <li><span class="material-symbols-outlined ok">check_circle</span> Detección Temprana de Riesgos</li>
            <li><span class="material-symbols-outlined ok">check_circle</span> Toma de Decisiones Estratégicas</li>
            <li><span class="material-symbols-outlined ok">check_circle</span> Proyecciones financieras en un par de clics</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="cta">
      <div class="container cta-inner">
        <h2>Toma mejores decisiones financieras hoy</h2>
        <p>
          Obtén claridad absoluta sobre la salud financiera de tu empresa con análisis automáticos
          y proyecciones precisas.
        </p>
        <button class="btn btn-white btn-lg" type="button">Crear cuenta</button>
      </div>
    </section>

    <footer class="footer">
      <div class="container footer-inner">
        <div class="footer-left">
          <div class="footer-title">
            <span class="material-symbols-outlined">school</span>
            <span>Trabajo Terminal</span>
          </div>
          <p>ESCOM / IPN - Instituto Politécnico Nacional</p>
        </div>

        <div class="footer-links">
          <a href="#">Términos</a>
          <a href="#">Privacidad</a>
          <a href="#">Contacto</a>
          <a href="#">Ayuda</a>
        </div>
      </div>

      <div class="footer-bottom">
        © 2024 PymeScope. Todos los derechos reservados.
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Variables */
.page {
  --primary: #299de0;
  --primary-dark: #1a7ac0;
  --bg-light: #f8fafb;
  --bg-dark: #111b21;
  --text: #0e161b;
  --muted: #5b6670;

  background: var(--bg-light);
  color: var(--text);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  overflow-x: hidden;
}

/* Container */
.container {
  width: min(1120px, 92vw);
  margin: 0 auto;
}

/* NAV */
.nav {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid #e8eff3;
  background: rgba(248, 250, 251, 0.95);
  backdrop-filter: blur(8px);
}
.nav-inner {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  gap: 10px;
  align-items: center;
}
.brand-icon {
  font-size: 30px;
  color: var(--primary);
}
.brand-name {
  font-weight: 800;
  font-size: 20px;
  letter-spacing: -0.02em;
}
.nav-links {
  display: flex;
  gap: 28px;
  align-items: center;
}
.nav-links a {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  text-decoration: none;
}
.nav-links a:hover {
  color: var(--primary);
}
.nav-menu-btn {
  display: none;
  border: 0;
  background: transparent;
  color: var(--text);
  cursor: pointer;
}

/* HERO */
.hero {
  padding: 56px 0 92px;
}
.hero-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 48px;
  align-items: center;
}
.hero-copy {
  text-align: left;
}
.hero-title {
  margin: 0 0 14px;
  font-weight: 900;
  font-size: clamp(32px, 4vw, 52px);
  line-height: 1.05;
  letter-spacing: -0.03em;
}
.text-primary {
  color: var(--primary);
}
.hero-subtitle {
  margin: 0;
  max-width: 560px;
  color: var(--muted);
  line-height: 1.7;
  font-size: 18px;
}
.hero-actions {
  margin-top: 18px;
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  align-items: center;
}
.hero-visual {
  position: relative;
  min-height: 320px;
}
.hero-backdrop {
  position: absolute;
  inset: 0;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(41, 157, 224, 0.10), transparent);
  transform: rotate(3deg);
  z-index: 0;
}
.hero-card {
  position: relative;
  z-index: 1;
  height: 100%;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid #eef2f5;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.12);
  background: white;
}
.hero-image {
  width: 100%;
  height: 100%;
  min-height: 320px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

/* Sections */
.section {
  padding: 80px 0;
}
.section-bordered {
  background: white;
  border-top: 1px solid #e8eff3;
  border-bottom: 1px solid #e8eff3;
}
.section-light {
  background: var(--bg-light);
}
.section-head {
  text-align: center;
  margin-bottom: 56px;
}
.kicker {
  margin: 0 0 8px;
  color: var(--primary);
  font-weight: 800;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.kicker-alt {
  color: var(--primary);
  font-weight: 800;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.section-title {
  margin: 0 0 12px;
  font-weight: 800;
  font-size: 34px;
  letter-spacing: -0.02em;
}
.section-subtitle {
  margin: 0 auto;
  max-width: 720px;
  color: var(--muted);
  line-height: 1.7;
}
.lead {
  color: var(--muted);
  font-size: 18px;
  line-height: 1.7;
}

.cards-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
}
.step-card {
  padding: 28px;
  border-radius: 14px;
  background: var(--bg-light);
  border: 1px solid #dfe7ee;
  transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
}
.step-card:hover {
  border-color: rgba(41, 157, 224, 0.35);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.step-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: rgba(41, 157, 224, 0.10);
  color: var(--primary);
  margin-bottom: 18px;
}
.step-icon span {
  font-size: 30px;
}
.step-card h3 {
  margin: 0 0 10px;
  font-weight: 800;
}
.step-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 42px;
  align-items: start;
}
.badge-problem {
  display: inline-block;
  color: #ef4444;
  font-weight: 800;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.problem-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
.problem-card {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 16px;
  background: white;
  border: 1px solid #fde2e2;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.problem-card h3 {
  margin: 0;
  font-weight: 800;
  font-size: 14px;
}
.problem-card p {
  margin: 6px 0 0;
  color: #7a8691;
  font-size: 13px;
}
.problem-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: #fef2f2;
  color: #ef4444;
}
.problem-icon span {
  font-size: 20px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
}
.feature {
  padding: 22px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #eef2f6;
  transition: box-shadow 0.2s ease;
}
.feature:hover {
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
}
.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--primary);
  color: white;
  box-shadow: 0 10px 22px rgba(41, 157, 224, 0.25);
  margin-bottom: 14px;
}
.feature-icon span {
  font-size: 22px;
}
.feature h3 {
  margin: 0 0 10px;
  font-weight: 800;
  font-size: 16px;
}
.feature p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
}

.benefits {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 46px;
  align-items: center;
}
.benefits-card {
  position: relative;
  background: #f8fafc;
  border-radius: 18px;
  padding: 26px;
  border: 1px solid #eef2f6;
}
.glow {
  position: absolute;
  border-radius: 999px;
  background: rgba(41, 157, 224, 0.12);
  filter: blur(20px);
  z-index: 0;
}
.glow-1 {
  width: 110px;
  height: 110px;
  top: -14px;
  left: -14px;
}
.glow-2 {
  width: 150px;
  height: 150px;
  bottom: -18px;
  right: -18px;
}
.benefits-image {
  width: 100%;
  border-radius: 12px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12);
  position: relative;
  z-index: 1;
}
.checks {
  list-style: none;
  padding: 0;
  margin: 18px 0 0;
  display: grid;
  gap: 12px;
}
.checks li {
  display: flex;
  gap: 10px;
  align-items: center;
  font-weight: 600;
}
.ok {
  color: #22c55e;
}

.cta {
  background: var(--primary);
  padding: 96px 0;
  color: white;
}
.cta-inner {
  text-align: center;
  max-width: 760px;
}
.cta h2 {
  margin: 0 0 14px;
  font-size: 40px;
  font-weight: 900;
}
.cta p {
  margin: 0 auto 28px;
  max-width: 680px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.85);
}

.footer {
  background: white;
  border-top: 1px solid #e5eaf0;
  padding: 40px 0 18px;
}
.footer-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}
.footer-left p {
  margin: 6px 0 0;
  color: #74808a;
  font-size: 13px;
}
.footer-title {
  display: flex;
  gap: 8px;
  align-items: center;
  font-weight: 800;
}
.footer-links {
  display: flex;
  gap: 22px;
  flex-wrap: wrap;
}
.footer-links a {
  text-decoration: none;
  color: #5b6670;
  font-size: 13px;
}
.footer-links a:hover {
  color: var(--primary);
}
.footer-bottom {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid #eef2f6;
  text-align: center;
  color: #9aa4ad;
  font-size: 12px;
}

.btn {
  border: 1px solid transparent;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  text-decoration: none;
  font-weight: 800;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.02s ease;
  user-select: none;
}
.btn:active {
  transform: translateY(1px);
}
.btn-sm {
  padding: 10px 14px;
  font-size: 13px;
}
.btn-lg {
  height: 48px;
  padding: 0 22px;
  font-size: 15px;
}
.btn-primary {
  background: var(--primary);
  color: white;
  box-shadow: 0 10px 22px rgba(41, 157, 224, 0.20);
}
.btn-primary:hover {
  background: var(--primary-dark);
}
.btn-ghost {
  background: transparent;
  color: var(--text);
}
.btn-ghost:hover {
  color: var(--primary);
  border-color: rgba(41, 157, 224, 0.25);
}
.btn-white {
  background: white;
  color: var(--primary);
}
.btn-white:hover {
  background: #f3f6f9;
}

/* Responsive */
@media (max-width: 980px) {
  .hero-grid,
  .split,
  .benefits {
    grid-template-columns: 1fr;
  }
  .hero-copy {
    text-align: center;
  }
  .hero-subtitle {
    margin-left: auto;
    margin-right: auto;
  }
  .hero-actions {
    justify-content: center;
  }
  .section-title {
    font-size: 30px;
  }
  .cards-3 {
    grid-template-columns: 1fr;
  }
  .features-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .nav-links {
    display: none;
  }
  .nav-menu-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
