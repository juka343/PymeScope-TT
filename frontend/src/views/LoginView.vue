<script setup>
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import { auth } from "@/firebase/config";
import {
  signInWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  setPersistence,
  browserLocalPersistence,
  browserSessionPersistence,
} from "firebase/auth";

const router = useRouter();

const showPassword = ref(false);

const email = ref("");
const password = ref("");
const rememberMe = ref(false);

const loading = ref(false);
const errorMsg = ref("");

function togglePassword() {
  showPassword.value = !showPassword.value;
}

function mapFirebaseError(code) {
  switch (code) {
    case "auth/invalid-email":
      return "Correo inválido.";
    case "auth/user-not-found":
      return "No existe una cuenta con ese correo.";
    case "auth/wrong-password":
    case "auth/invalid-credential":
      return "Correo o contraseña incorrectos.";
    case "auth/too-many-requests":
      return "Demasiados intentos. Intenta más tarde.";
    case "auth/popup-closed-by-user":
      return "Cerraste la ventana de Google antes de terminar.";
    default:
      return "No se pudo iniciar sesión.";
  }
}

async function handleSubmit() {
  errorMsg.value = "";
  loading.value = true;

  try {
    await setPersistence(
      auth,
      rememberMe.value ? browserLocalPersistence : browserSessionPersistence
    );

    await signInWithEmailAndPassword(auth, email.value, password.value);

    router.push("/misProyectos");
  } catch (err) {
    console.error(err);
    errorMsg.value = mapFirebaseError(err?.code);
  } finally {
    loading.value = false;
  }
}

async function handleGoogle() {
  errorMsg.value = "";
  loading.value = true;

  try {
    await setPersistence(
      auth,
      rememberMe.value ? browserLocalPersistence : browserSessionPersistence
    );

    const provider = new GoogleAuthProvider();
    await signInWithPopup(auth, provider);

    router.push("/misProyectos");
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
          <div class="brand">
            <div class="brand-icon">
              <span class="material-symbols-outlined">analytics</span>
            </div>
            <span class="brand-name">PymeScope</span>
          </div>

          <div class="side-copy">
            <h2>Analiza la salud financiera de tu empresa en minutos</h2>
            <p>
              Accede a herramientas de análisis profesional y toma decisiones informadas para el
              crecimiento de tu negocio.
            </p>
          </div>

          <div class="side-links desktop-only">
            <a href="#">Privacidad</a>
            <a href="#">Términos</a>
          </div>
        </div>
      </aside>

      <main class="main">
        <div class="card">
          <div class="card-body">
            <div class="head">
              <h1>Iniciar sesión</h1>
              <p>Bienvenido de nuevo a tu panel de control</p>

              <p v-if="errorMsg" class="error">
                {{ errorMsg }}
              </p>
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

              <label class="field">
                <span class="label">Contraseña</span>

                <div class="control password">
                  <span class="icon material-symbols-outlined">lock</span>

                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="••••••••"
                    autocomplete="current-password"
                    required
                  />

                  <button class="eye" type="button" @click="showPassword = !showPassword">
                    <span class="material-symbols-outlined">
                      {{ showPassword ? "visibility_off" : "visibility" }}
                    </span>
                  </button>
                </div>
              </label>



              <div class="row">
                <label class="check">
                  <input v-model="rememberMe" type="checkbox" :disabled="loading" />
                  <span>Recordarme</span>
                </label>

                <a class="link" href="#">¿Olvidaste tu contraseña?</a>
              </div>

              <button class="btn-primary" type="submit" :disabled="loading">
                {{ loading ? "Iniciando..." : "Iniciar sesión" }}
              </button>
            </form>

            <div class="divider">
              <span></span>
              <strong>o</strong>
              <span></span>
            </div>

            <button class="btn-outline" type="button" @click="handleGoogle" :disabled="loading">
              <svg aria-hidden="true" class="google" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              <span>{{ loading ? "Espera..." : "Continuar con Google" }}</span>
            </button>
          </div>

          <div class="card-foot">
            <p>
              ¿No tienes una cuenta?
              <RouterLink class="link strong" to="/registro">Crear cuenta</RouterLink>
            </p>
          </div>
        </div>

        <div class="mobile-links">
          <a href="#">Privacidad</a>
          <a href="#">Términos</a>
          <a href="#">Ayuda</a>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Paleta base */
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
  display: flex;
  flex-direction: column;
  gap: 28px;
  height: 100%;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  display: grid;
  place-items: center;
}

.brand-icon span {
  font-size: 24px;
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

.error {
  margin: 12px 0 0;
  color: #ef4444;
  font-weight: 900;
  font-size: 13px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.password {
  position: relative;
  width: 100%;

}

.password input {
  width: 100%;
  padding-right: 48px;
}

.eye {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  cursor: pointer;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eye:hover {
  color: #475569;
}

.eye span {
  font-size: 20px;
}

.control.password {
  position: relative;
}

.control.password .icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  color: #94a3b8;
  pointer-events: none;
}

.control.password input {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  padding-left: 42px;  /* espacio para el candado */
  padding-right: 46px; /* espacio para el ojo */
  font-size: 16px;
  outline: none;
}

.control.password .eye {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;

  background: transparent;
  border: none;
  padding: 0;
  margin: 0;
  line-height: 1;
  cursor: pointer;

  color: #94a3b8;
}

.control.password .eye:hover {
  color: #475569;
}

.control.password .eye span {
  font-size: 22px;
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

input[type="email"],
input[type="password"] {
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

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  font-weight: 700;
  color: #64748b;
  font-size: 14px;
}

.check input {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  accent-color: var(--primary);
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

.divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 18px 0;
  color: #94a3b8;
}
.divider span {
  flex: 1;
  height: 1px;
  background: #e2e8f0;
}
.divider strong {
  font-size: 13px;
  font-weight: 800;
}

.btn-outline {
  height: 48px;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  background: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: 900;
  color: #334155;
  transition: background 0.15s ease, transform 0.05s ease, opacity 0.15s ease;
}
.btn-outline:hover {
  background: #f8fafc;
}
.btn-outline:active {
  transform: translateY(1px);
}
.btn-outline:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.google {
  width: 20px;
  height: 20px;
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
    padding: 64px;
    display: flex;
  }
  .main {
    width: 50%;
    padding: 48px;
  }
  .desktop-only {
    display: flex;
  }
}
</style>
