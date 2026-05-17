<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  documentName: {
    type: String,
    default: "tu documento",
  },
});
</script>

<template>
  <Teleport to="body">
    <Transition name="loading-fade">
      <div v-if="isOpen" class="loading-overlay no-print" data-html2canvas-ignore="true">
        <div class="loading-modal">
          <div class="loading-body">
            <span class="material-symbols-outlined loading-watermark">description</span>
            
            <div class="loading-icon">
              <div class="spinner"></div>
            </div>
            <h2>Generando PDF</h2>
            <p>
              Por favor, espera mientras procesamos y descargamos {{ documentName }}.
              Esto puede tomar unos segundos.
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  padding: 24px;
}

.loading-modal {
  width: 100%;
  max-width: 500px;
  background: #ffffff;
  border: 1px solid #e8eff3;
  border-radius: 18px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  position: relative;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

.loading-body {
  padding: 52px 32px 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: linear-gradient(180deg, #f0f8fd 0%, #ffffff 100%);
}

.loading-watermark {
  position: absolute;
  right: -12px;
  bottom: -18px;
  font-size: 170px;
  color: #299de0;
  opacity: 0.04;
  pointer-events: none;
}

.loading-icon {
  width: 84px;
  height: 84px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #ffffff;
  border: 1px solid #d1dee6;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
  margin-bottom: 20px;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid #e8eff3;
  border-top-color: #299de0;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-body h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  color: #0e161b;
  letter-spacing: -0.02em;
}

.loading-body p {
  margin: 14px 0 0;
  max-width: 360px;
  font-size: 14px;
  line-height: 1.6;
  font-weight: 700;
  color: #507c95;
}

/* Transitions */
.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.2s ease;
}
.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}
</style>
