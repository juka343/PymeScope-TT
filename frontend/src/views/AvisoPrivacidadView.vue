<script setup>
import { RouterLink } from "vue-router";
</script>

<template>
  <div class="page">
    <nav class="nav">
      <div class="container nav-inner">
        <RouterLink to="/" class="brand">
          <img src="/logo.png" alt="Logo PymeScope" class="brand-icon" />
          <span class="brand-name">PymeScope</span>
        </RouterLink>
        <div class="nav-actions">
          <RouterLink to="/" class="btn btn-ghost btn-sm">
            <span class="material-symbols-outlined">arrow_back</span>
            Volver al inicio
          </RouterLink>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <div class="container doc-container">
        <div class="doc-header">
          <span class="kicker">Legal</span>
          <h1 class="doc-title">Aviso de Privacidad</h1>
          <p class="doc-date">Última actualización: Mayo 2026</p>
        </div>

        <div class="doc-body">
          <section>
            <h2>1. Naturaleza del Proyecto</h2>
            <p>
              <strong>PymeScope</strong> es una plataforma desarrollada con fines estrictamente académicos como parte de un Trabajo Terminal en la <strong>Escuela Superior de Cómputo (ESCOM)</strong> del <strong>Instituto Politécnico Nacional (IPN)</strong>. Los datos recopilados no son utilizados con fines comerciales, publicitarios o de lucro.
            </p>
          </section>

          <section>
            <h2>2. Datos Recopilados</h2>
            <p>Para el correcto funcionamiento de la plataforma, recopilamos los siguientes datos:</p>
            <ul>
              <li><strong>Datos de Autenticación:</strong> Correo electrónico y nombre de usuario (gestionados a través de Google Authentication y Firebase).</li>
              <li><strong>Datos Financieros:</strong> Archivos PDF correspondientes a Estados de Resultados y Balances Generales subidos voluntariamente por el usuario para su análisis.</li>
            </ul>
          </section>

          <section>
            <h2>3. Uso de la Información</h2>
            <p>
              Los documentos financieros subidos a PymeScope son procesados utilizando servicios de Inteligencia Artificial de terceros, específicamente <strong>Azure Document Intelligence</strong> (para la extracción de texto OCR) y <strong>Google Gemini</strong> para la generación de interpretaciones basadas en los resultados calculados por el sistema. 
            </p>
            <p>
              Estos datos se utilizan <strong>exclusivamente</strong> para calcular los indicadores financieros (KPIs) solicitados por el usuario y generar los tableros de control dentro de la sesión activa.
            </p>
          </section>

          <section>
            <h2>4. Almacenamiento y Protección de Datos</h2>
            <p>
              Los archivos PDF se almacenan de forma segura en los servicios en la nube de <strong>Firebase Storage</strong> para que el usuario pueda acceder a su historial de proyectos financieros en cualquier momento.
            </p>
            <p>
              La protección de estos documentos y datos está respaldada por las políticas de seguridad perimetral (CORS) configuradas en nuestra arquitectura y por la infraestructura de seguridad nativa de los proveedores en la nube utilizados (Firebase y Azure). No obstante, se recomienda a los usuarios <strong>no subir documentos que contengan información extremadamente sensible, confidencial, secretos industriales o datos bancarios críticos</strong>, dado que PymeScope es un sistema que se encuentra en fase de prototipo.
            </p>
          </section>

          <section>
            <h2>5. Uso de Servicios de Terceros</h2>
            <p>
              Al utilizar PymeScope, el usuario acepta que su información será procesada temporalmente por infraestructuras de Microsoft (Azure) y Google (Gemini/Firebase). PymeScope no tiene control directo sobre las políticas de retención internas de dichos proveedores, aunque las llamadas a las APIs están configuradas bajo estándares de privacidad estándar.
            </p>
          </section>

          <section>
            <h2>6. Contacto</h2>
            <p>
              Para cualquier duda relacionada con el manejo de la información en este Trabajo Terminal, por favor póngase en contacto con el equipo de desarrollo a través de los canales institucionales de ESCOM - IPN.
            </p>
          </section>
        </div>
      </div>
    </main>

    <footer class="footer">
      <div class="container footer-inner">
        <div class="footer-left">
          <div class="footer-title">
            <span class="material-symbols-outlined">school</span>
            <span>Trabajo Terminal</span>
          </div>
          <p>ESCOM / IPN - Instituto Politécnico Nacional</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.page {
  --primary: #299de0;
  --bg-light: #f8fafb;
  --text: #0e161b;
  --muted: #5b6670;
  background: var(--bg-light);
  color: var(--text);
  font-family: Inter, system-ui, sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

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
  text-decoration: none;
  color: var(--text);
}
.brand-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
}
.brand-name {
  font-weight: 800;
  font-size: 20px;
  letter-spacing: -0.02em;
}

/* CONTENT */
.main-content {
  flex: 1;
  padding: 64px 0 96px;
}
.doc-container {
  max-width: 800px;
  background: white;
  border-radius: 16px;
  border: 1px solid #e8eff3;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
  padding: 48px;
}
.doc-header {
  margin-bottom: 48px;
  text-align: center;
  border-bottom: 1px solid #e8eff3;
  padding-bottom: 32px;
}
.kicker {
  color: var(--primary);
  font-weight: 800;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.doc-title {
  margin: 12px 0 8px;
  font-weight: 900;
  font-size: 36px;
  letter-spacing: -0.02em;
}
.doc-date {
  color: var(--muted);
  font-size: 14px;
}
.doc-body section {
  margin-bottom: 32px;
}
.doc-body h2 {
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 16px;
  color: #1a202c;
}
.doc-body p {
  color: #475569;
  line-height: 1.7;
  margin-bottom: 16px;
  font-size: 15px;
}
.doc-body ul {
  color: #475569;
  line-height: 1.7;
  font-size: 15px;
  padding-left: 20px;
  margin-bottom: 16px;
}
.doc-body li {
  margin-bottom: 8px;
}

/* FOOTER */
.footer {
  background: white;
  border-top: 1px solid #e5eaf0;
  padding: 40px 0 40px;
}
.footer-inner {
  display: flex;
  justify-content: center;
  align-items: center;
}
.footer-left {
  text-align: center;
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
  justify-content: center;
  font-weight: 800;
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
  transition: all 0.2s ease;
}
.btn-sm {
  padding: 10px 14px;
  font-size: 13px;
}
.btn-ghost {
  background: transparent;
  color: var(--muted);
}
.btn-ghost:hover {
  color: var(--primary);
  background: rgba(41, 157, 224, 0.05);
}
.material-symbols-outlined {
  font-size: 18px;
}

@media (max-width: 768px) {
  .doc-container {
    padding: 32px 20px;
  }
  .doc-title {
    font-size: 28px;
  }
}
</style>
