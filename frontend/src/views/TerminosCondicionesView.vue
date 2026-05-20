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
          <h1 class="doc-title">Términos y Condiciones</h1>
          <p class="doc-date">Última actualización: Mayo 2026</p>
        </div>

        <div class="doc-body">
          <section>
            <h2>1. Aceptación de los Términos</h2>
            <p>
              Al acceder y utilizar la plataforma <strong>PymeScope</strong>, usted acepta cumplir y estar sujeto a los siguientes Términos y Condiciones. Si no está de acuerdo con alguna parte de estos términos, no debe utilizar el servicio.
            </p>
          </section>

          <section>
            <h2>2. Descargo de Responsabilidad (Disclaimer) Financiero y Legal</h2>
            <div class="alert warning">
              <span class="material-symbols-outlined alert-icon">warning</span>
              <div class="alert-content">
                <strong>Atención:</strong> PymeScope NO proporciona asesoría financiera, contable, tributaria ni legal profesional.
              </div>
            </div>
            <p>
              Las "Interpretaciones Automáticas" y proyecciones generadas dentro de la plataforma son producto de modelos de Inteligencia Artificial (LLMs) y cálculos algorítmicos. Estas interpretaciones son <strong>estrictamente informativas y orientativas</strong>. 
            </p>
            <p>
              <strong>Cualquier decisión de inversión, endeudamiento, reestructuración u operativa tomada en base a los resultados de PymeScope es responsabilidad exclusiva del usuario.</strong> Se recomienda encarecidamente consultar a un contador público certificado o asesor financiero antes de tomar decisiones críticas para su negocio.
            </p>
          </section>

          <section>
            <h2>3. Uso Aceptable de la Plataforma</h2>
            <p>El usuario se compromete a:</p>
            <ul>
              <li>Subir únicamente documentos (Estados Financieros) que sean de su propiedad o sobre los cuales tenga autorización legal para su procesamiento.</li>
              <li>Comprender que, dada la naturaleza tecnológica del sistema (extracción de texto y análisis por Inteligencia Artificial), los resultados están sujetos a márgenes de error probabilísticos. Es responsabilidad del usuario corroborar siempre que los datos extraídos y calculados coincidan fielmente con sus documentos originales antes de darlos por válidos.</li>
            </ul>
          </section>

          <section>
            <h2>4. Naturaleza Académica y Disponibilidad (SLA)</h2>
            <p>
              PymeScope es un sistema informático desarrollado como <strong>Trabajo Terminal</strong> de la <strong>Escuela Superior de Cómputo (ESCOM) - IPN</strong>. Como tal, la plataforma se ofrece "tal cual" (<em>as is</em>) para fines de evaluación académica y pruebas de concepto.
            </p>
            <p>
              <strong>No se garantiza disponibilidad comercial (SLA).</strong> El servicio puede ser interrumpido, sufrir pérdida de datos, o ser suspendido permanentemente sin previo aviso, dependiendo del ciclo de evaluación académica.
            </p>
          </section>

          <section>
            <h2>5. Modificaciones a la Plataforma</h2>
            <p>
              El equipo desarrollador se reserva el derecho de modificar o discontinuar el servicio (o cualquier parte de este), así como de alterar algoritmos de IA o métodos de cálculo en cualquier momento, según los requerimientos del IPN y los asesores del proyecto.
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

/* ALERTS */
.alert {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 20px;
}
.alert.warning {
  background: #fffbeb;
  border: 1px solid #fde68a;
}
.alert-icon {
  color: #d97706;
  font-size: 24px;
}
.alert-content {
  color: #92400e;
  font-size: 15px;
  line-height: 1.6;
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
