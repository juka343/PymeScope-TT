<script setup>
import { ref, computed } from "vue";
import { RouterLink, useRouter } from "vue-router";

import { auth } from "@/firebase/config";
import {
  createUserWithEmailAndPassword,
  updateProfile,
  GoogleAuthProvider,
  signInWithPopup,
} from "firebase/auth";

const router = useRouter();

const fullName = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const acceptTerms = ref(false);

const showPassword = ref(false);
const showConfirmPassword = ref(false);

const loading = ref(false);
const errorMsg = ref("");

const passwordsMatch = computed(() => {
  if (!password.value && !confirmPassword.value) return true;
  return password.value === confirmPassword.value;
});

const canSubmit = computed(() => {
  return (
    fullName.value.trim().length > 0 &&
    email.value.trim().length > 0 &&
    password.value.length >= 8 &&
    confirmPassword.value.length >= 8 &&
    passwordsMatch.value &&
    acceptTerms.value &&
    !loading.value
  );
});

function togglePassword() {
  showPassword.value = !showPassword.value;
}

function toggleConfirmPassword() {
  showConfirmPassword.value = !showConfirmPassword.value;
}

function mapFirebaseError(err) {
  const code = err?.code || "";

  // Traducciones rápidas (porque el mundo no se va a arreglar solo)
  if (code === "auth/email-already-in-use") return "Ese correo ya está registrado.";
  if (code === "auth/invalid-email") return "El correo no es válido.";
  if (code === "auth/weak-password") return "La contraseña es muy débil (mínimo 6, tú pediste 8).";
  if (code === "auth/operation-not-allowed")
    return "Auth por correo no está habilitado en Firebase Console.";
  if (code === "auth/popup-closed-by-user") return "Cerraste el popup de Google.";
  if (code === "auth/cancelled-popup-request") return "Se canceló el popup anterior de Google.";
  return "No se pudo registrar. Intenta de nuevo.";
}

async function handleSubmit() {
  errorMsg.value = "";
  if (!canSubmit.value) return;

  loading.value = true;
  try {
    // 1) Crear usuario
    const cred = await createUserWithEmailAndPassword(
      auth,
      email.value.trim(),
      password.value
    );

    // 2) Guardar nombre en el perfil
    await updateProfile(cred.user, {
      displayName: fullName.value.trim(),
    });

    // 3) Redirigir
    await router.push("/misProyectos");
  } catch (err) {
    console.error(err);
    errorMsg.value = mapFirebaseError(err);
  } finally {
    loading.value = false;
  }
}

async function handleGoogle() {
  errorMsg.value = "";
  loading.value = true;

  try {
    const provider = new GoogleAuthProvider();
    // opcional: fuerza selector de cuentas
    provider.setCustomParameters({ prompt: "select_account" });

    await signInWithPopup(auth, provider);

    // Si quieres asegurar displayName, normalmente Google lo trae ya.
    await router.push("/misProyectos");
  } catch (err) {
    console.error(err);
    errorMsg.value = mapFirebaseError(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <div class="layout">
      <!-- LADO IZQUIERDO -->
      <aside class="side">
        <div class="pattern" aria-hidden="true"></div>

        <div class="side-inner">
          <div class="brand">
            <div class="brand-icon">
              <span class="material-symbols-outlined">analytics</span>
            </div>
            <h1 class="brand-name">PymeScope</h1>
          </div>

          <div class="side-copy">
            <h2>Potencia el crecimiento de tu empresa.</h2>
            <p>
              Análisis financiero simplificado para tomar mejores decisiones. Únete a miles de
              empresas que ya confían en nosotros.
            </p>
          </div>
        </div>
      </aside>

      <!-- LADO DERECHO -->
      <main class="main">
        <div class="card">
          <div class="card-head">
            <h3>Registrar Cuenta</h3>
          </div>

          <!-- ERROR -->
          <p v-if="errorMsg" class="alert" role="alert">
            <span class="material-symbols-outlined">error</span>
            <span>{{ errorMsg }}</span>
          </p>

          <form class="form" @submit.prevent="handleSubmit">
            <label class="field">
              <span class="label">Nombre completo</span>
              <input
                v-model.trim="fullName"
                type="text"
                placeholder="Ej. Juan Pérez"
                autocomplete="name"
                required
                :disabled="loading"
              />
            </label>

            <label class="field">
              <span class="label">Correo electrónico</span>
              <input
                v-model.trim="email"
                type="email"
                placeholder="nombre@empresa.com"
                autocomplete="email"
                required
                :disabled="loading"
              />
            </label>

            <label class="field">
              <span class="label">Contraseña</span>
              <div class="password">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  autocomplete="new-password"
                  minlength="8"
                  required
                  :disabled="loading"
                />
                <button class="eye" type="button" @click="togglePassword" :disabled="loading">
                  <span class="material-symbols-outlined">
                    {{ showPassword ? "visibility_off" : "visibility" }}
                  </span>
                </button>
              </div>
              <small class="hint">Mínimo 8 caracteres.</small>
            </label>

            <label class="field">
              <span class="label">Confirmar contraseña</span>
              <div class="password">
              <input
                v-model="confirmPassword"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                autocomplete="new-password"
                minlength="8"
                required
                :class="{ invalid: !passwordsMatch }"
                :disabled="loading"
              />
              <button class="eye" type="button" @click="toggleConfirmPassword" :disabled="loading">
                  <span class="material-symbols-outlined">
                    {{ showConfirmPassword ? "visibility_off" : "visibility" }}
                  </span>
              </button>
              </div>
              <small v-if="!passwordsMatch" class="error">Las contraseñas no coinciden.</small>
            </label>

            <div class="terms">
              <input id="terms" v-model="acceptTerms" type="checkbox" :disabled="loading" />
              <label for="terms">
                Acepto los
                <a href="#" class="link">términos y condiciones</a>
                y la política de privacidad de PymeScope.
              </label>
            </div>

            <button class="btn-primary" type="submit" :disabled="!canSubmit">
              <span v-if="loading">Creando cuenta…</span>
              <span v-else>Crear cuenta</span>
            </button>

            <div class="security">
              <span class="material-symbols-outlined">lock</span>
              <span>Tu información estará protegida y solo se utilizará para el análisis financiero.</span>
            </div>

            <div class="divider">
              <span></span>
              <strong>o</strong>
              <span></span>
            </div>

            <button class="btn-outline" type="button" @click="handleGoogle" :disabled="loading">
              <svg class="google" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.84z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              <span>{{ loading ? "Abriendo Google…" : "Registrarse con Google" }}</span>
            </button>

            <p class="switch">
              ¿Ya tienes una cuenta?
              <RouterLink class="link strong" to="/login">Iniciar sesión</RouterLink>
            </p>
          </form>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Tu CSS original + una alerta chiquita */
.page {
  --primary: #299de0;
  --bg-light: #f6f7f8;
  --bg-dark: #111b21;
  --text: #111517;
  --muted: #647a87;

  min-height: 100vh;
  background: var(--bg-light);
  color: var(--text);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Left side */
.side {
  position: relative;
  padding: 32px 24px;
  background: #eef7fc;
}

.pattern {
  position: absolute;
  inset: 0;
  opacity: 0.1;
  pointer-events: none;
  background-image: url("https://lh3.googleusercontent.com/aida-public/AB6AXuBWpgyCJQAXz-rD-QigCMfCjZR40d5qgAnso9wYingDuLy34HP54DExPd5OqANTO4miLK866RfxFEV5mwNgp3JG-BhYXOT0ar6FJnLjTpQE27EoI9QJ8UXViqdsXSTmzzzG5TiuG1ph2bpUDujaZ127JdzkkxlDubvjS_XH8Vl-uf6sht964Gf1yW01s_GUCNrF4dDZqtrBJiz0aDZNBNzi3bTnmIDsiAiCW8WWm3H-6fVU-MfoO0dJNLOBTfa6KquskHYOU6X-z5s");
  background-size: cover;
  background-position: center;
}

.side-inner {
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
  gap: 10px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  display: grid;
  place-items: center;
}

.brand-icon span {
  font-size: 24px;
}

.brand-name {
  margin: 0;
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.side-copy h2 {
  margin: 0;
  font-size: clamp(28px, 3.5vw, 40px);
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.side-copy p {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.6;
}

/* Right side */
.main {
  flex: 1;
  display: grid;
  place-items: center;
  padding: 16px;
  background: var(--bg-light);
  overflow-y: auto;
}

.card {
  width: 100%;
  max-width: 480px;
  background: white;
  border: 1px solid #eef2f6;
  border-radius: 16px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
  padding: 24px;
}

.card-head {
  text-align: center;
  margin-bottom: 18px;
}

.card-head h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.alert {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 700;
  margin: 0 0 14px;
}
.alert span.material-symbols-outlined {
  font-size: 18px;
  margin-top: 1px;
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
  font-weight: 800;
}

input[type="text"],
input[type="email"],
input[type="password"] {
  height: 48px;
  border-radius: 12px;
  border: 1px solid #dce2e5;
  padding: 0 14px;
  font-size: 16px;
  background: white;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

input::placeholder {
  color: #94a3b8;
}

input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(41, 157, 224, 0.22);
}

.password {
  position: relative;
}

.password input {
  width: 100%;
  padding-right: 44px;
}

.eye {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #9aa4ad;
}

.eye:hover {
  color: #475569;
}

.eye span {
  font-size: 20px;
}

.hint {
  color: #94a3b8;
  font-size: 12px;
}

.error {
  color: #ef4444;
  font-size: 12px;
  font-weight: 700;
}

.invalid {
  border-color: rgba(239, 68, 68, 0.6) !important;
}

.terms {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding-top: 6px;
}

.terms input {
  margin-top: 3px;
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
}

.terms label {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.4;
}

.btn-primary {
  height: 50px;
  border-radius: 12px;
  background: var(--primary);
  color: white;
  font-weight: 900;
  font-size: 15px;
  box-shadow: 0 10px 22px rgba(41, 157, 224, 0.25);
  transition: filter 0.15s ease, transform 0.05s ease, opacity 0.15s ease;
}

.btn-primary:hover:enabled {
  filter: brightness(0.95);
}

.btn-primary:active:enabled {
  transform: translateY(1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.security {
  display: flex;
  gap: 10px;
  align-items: center;
  background: #eff6ff;
  color: #475569;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.35;
}

.security span.material-symbols-outlined {
  font-size: 16px;
  color: #334155;
}

.divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 6px 0;
  color: #9aa4ad;
}

.divider span {
  flex: 1;
  height: 1px;
  background: #e2e8f0;
}

.divider strong {
  font-size: 13px;
  font-weight: 900;
}

.btn-outline {
  height: 50px;
  border-radius: 12px;
  border: 1px solid #dce2e5;
  background: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: 800;
  color: #111517;
  transition: background 0.15s ease, transform 0.05s ease;
}

.btn-outline:hover {
  background: #f8fafc;
}

.btn-outline:active {
  transform: translateY(1px);
}

.google {
  width: 20px;
  height: 20px;
}

.link {
  color: var(--primary);
  font-weight: 800;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.strong {
  margin-left: 6px;
}

.switch {
  text-align: center;
  margin: 6px 0 0;
  color: #475569;
  font-size: 14px;
}

/* Responsive */
@media (min-width: 1024px) {
  .layout {
    flex-direction: row;
  }
  .side,
  .main {
    width: 50%;
  }
  .side {
    padding: 48px;
  }
  .main {
    padding: 32px;
  }
}
</style>
