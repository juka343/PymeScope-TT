<script setup>
import { ref } from "vue";
import { RouterLink } from "vue-router";
import { auth } from "@/firebase/config";
import { sendPasswordResetEmail } from "firebase/auth";

const email = ref("");
const loading = ref(false);
const errorMsg = ref("");
const successMsg = ref(false);

function mapFirebaseError(code) {
  switch (code) {
    case "auth/invalid-email":
      return "Correo inválido.";
    case "auth/user-not-found":
      return "No existe una cuenta con ese correo.";
    case "auth/too-many-requests":
      return "Demasiados intentos. Intenta más tarde.";
    default:
      return "No se pudo enviar el enlace.";
  }
}

async function handleSubmit() {
  errorMsg.value = "";
  successMsg.value = false;
  loading.value = true;

  try {
    auth.languageCode = 'es'; // Forzar que el correo llegue en español
    await sendPasswordResetEmail(auth, email.value);
    successMsg.value = true;
    email.value = ""; // clear email after success
  } catch (err) {
    console.error(err);
    errorMsg.value = mapFirebaseError(err?.code);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <div class="layout">
      <aside class="side">
        <div class="side-bg" aria-hidden="true"></div>
        <div class="side-overlay" aria-hidden="true"></div>

        <div class="side-content">
          <RouterLink to="/" class="brand" style="text-decoration: none; color: inherit;">
            <img src="/pymescopeNegativo.png" alt="Logo PymeScope" class="brand-img-full" />
          </RouterLink>

          <div class="side-copy">
            <h2>Analiza la salud financiera de tu empresa en minutos</h2>
            <p>
              Accede a herramientas de análisis profesional y toma decisiones informadas para el
              crecimiento de tu negocio.
            </p>
          </div>

          <div class="side-links desktop-only"></div>
        </div>
      </aside>

      <main class="main">
        <div class="card">
          <div class="card-body">
            <div class="head">
              <h1>Recuperar Contraseña</h1>
              <p>Te enviaremos un enlace seguro para restablecerla</p>

              <div v-if="errorMsg" class="form-error">
                <span class="material-symbols-outlined">error</span>
                <span>{{ errorMsg }}</span>
              </div>
              
              <div v-if="successMsg" class="form-success">
                <span class="material-symbols-outlined">check_circle</span>
                <span>¡Enlace enviado! Revisa tu bandeja de entrada (y la carpeta de spam).</span>
              </div>
            </div>

            <form class="form" @submit.prevent="handleSubmit">
              <label class="field">
                <span class="label">Correo electrónico</span>
                <div class="control">
                  <span class="icon material-symbols-outlined">mail</span>
                  <input
                    v-model.trim="email"
                    type="email"
                    placeholder="nombre@empresa.com"
                    autocomplete="email"
                    required
                    :disabled="loading"
                  />
                </div>
              </label>

              <button class="btn-primary" type="submit" :disabled="loading">
                {{ loading ? "Enviando enlace..." : "Enviar enlace" }}
              </button>
            </form>

          </div>

          <div class="card-foot">
            <p>
              ¿Recordaste tu contraseña?
              <RouterLink class="link strong" to="/login">Volver al inicio de sesión</RouterLink>
            </p>
          </div>
        </div>

        <div class="mobile-links">
          <a href="#">Aviso de Privacidad</a>
          <a href="#">Términos y Condiciones</a>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Paleta base (Igual a LoginView) */
.page {
  --primary: #299de0;
  --primary-dark: #1a6ba3;
  --bg-light: #f6f7f8;
  --bg-dark: #111b21;

  --text: #0f172a;
  --muted: #64748b;

  --card: #ffffff;
  --card-dark: #1e2730;

  background: var(--bg-light);
  color: var(--text);
  min-height: 100vh;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.side {
  position: relative;
  background: var(--primary);
  color: white;
  padding: 32px 24px;
  overflow: hidden;
}

.side-bg {
  position: absolute;
  inset: 0;
  background-image: url("https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2670&auto=format&fit=crop");
  background-size: cover;
  background-position: center;
  opacity: 0.2;
  mix-blend-mode: overlay;
}

.side-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(41, 157, 224, 0.9), rgba(26, 107, 163, 0.9));
}

.side-content {
  position: relative;
  z-index: 1;
  max-width: 520px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-img-full {
  width: 200px;
  height: auto;
  object-fit: contain;
  display: block;
  transform: translateX(-28px);
}

.brand-name {
  font-size: 24px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.side-copy {
  max-width: 480px;
}

.side-copy h2 {
  margin: 0;
  font-size: clamp(28px, 3.5vw, 40px);
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.side-copy p {
  margin: 14px 0 0;
  color: rgba(219, 234, 254, 0.95);
  font-size: 18px;
  line-height: 1.65;
  font-weight: 600;
}

.side-links {
  display: flex;
  gap: 24px;
  font-size: 14px;
  font-weight: 600;
  color: rgba(219, 234, 254, 0.95);
}

.side-links a:hover {
  color: white;
}

/* MAIN */
.main {
  flex: 1;
  display: grid;
  place-items: center;
  padding: 24px;
}

.card {
  width: 100%;
  max-width: 480px;
  background: var(--card);
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 18px 45px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.card-body {
  padding: 32px;
}

.head {
  text-align: center;
  margin-bottom: 22px;
}

.head h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.head p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.form-error {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 14px 0 0;
  padding: 8px 12px;
  border-radius: 8px;
  background: #fee2e2;
  color: #ef4444;
  font-size: 13px;
  font-weight: 700;
  animation: shake 0.3s ease;
}

.form-error .material-symbols-outlined {
  font-size: 18px;
  flex-shrink: 0;
}

.form-success {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 14px 0 0;
  padding: 8px 12px;
  border-radius: 8px;
  background: #dcfce7;
  color: #15803d;
  font-size: 13px;
  font-weight: 700;
}

.form-success .material-symbols-outlined {
  font-size: 18px;
  flex-shrink: 0;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-4px); }
  40% { transform: translateX(4px); }
  60% { transform: translateX(-3px); }
  80% { transform: translateX(2px); }
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.control {
  position: relative;
}

.icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  color: #94a3b8;
  pointer-events: none;
}

input[type="email"] {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  padding: 0 14px 0 42px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

input::placeholder {
  color: #94a3b8;
}

input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(41, 157, 224, 0.25);
  background: white;
}

.link {
  color: var(--primary);
  font-weight: 800;
  font-size: 14px;
}
.link:hover {
  filter: brightness(0.9);
}
.strong {
  margin-left: 6px;
}

/* Buttons */
.btn-primary {
  height: 48px;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 900;
  font-size: 15px;
  box-shadow: 0 10px 22px rgba(41, 157, 224, 0.25);
  transition: filter 0.15s ease, transform 0.05s ease, opacity 0.15s ease;
  margin-top: 6px;
}

.btn-primary:hover {
  filter: brightness(0.95);
}
.btn-primary:active {
  transform: translateY(1px);
}

.btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* Footer inside card */
.card-foot {
  border-top: 1px solid #eef2f6;
  background: #f8fafc;
  padding: 14px 18px;
  text-align: center;
}
.card-foot p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

/* Mobile links */
.mobile-links {
  margin-top: 18px;
  display: flex;
  gap: 22px;
  justify-content: center;
  color: #64748b;
  font-size: 14px;
}
.mobile-links a:hover {
  color: #0f172a;
}

.desktop-only {
  display: none;
}

/* Responsive: vuelve 2 columnas */
@media (min-width: 1024px) {
  .layout {
    flex-direction: row;
  }
  .side {
    width: 50%;
    padding: 48px;
  }
  .main {
    width: 50%;
    padding: 32px;
  }
  .desktop-only {
    display: flex;
  }
}
</style>
