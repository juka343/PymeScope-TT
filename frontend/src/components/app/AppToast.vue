<script setup>
import { useToast } from "@/composables/useToast";

const { toasts, removeToast } = useToast();

const iconMap = {
  success: "check_circle",
  error: "error",
  warning: "warning",
  info: "info",
};
</script>

<template>
  <Teleport to="body">
    <div class="toast-container" aria-live="polite">
      <TransitionGroup name="toast-slide">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast"
          :class="`toast--${t.type}`"
          @click="removeToast(t.id)"
        >
          <span class="material-symbols-outlined toast-icon">
            {{ iconMap[t.type] || "info" }}
          </span>
          <span class="toast-msg">{{ t.message }}</span>
          <button class="toast-close" @click.stop="removeToast(t.id)" aria-label="Cerrar">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  pointer-events: none;
}

.toast {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  background: white;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.15);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border-left: 4px solid transparent;
}

.toast--error {
  border-left-color: #ef4444;
  background: #fef2f2;
  color: #991b1b;
}

.toast--success {
  border-left-color: #22c55e;
  background: #f0fdf4;
  color: #166534;
}

.toast--warning {
  border-left-color: #f59e0b;
  background: #fffbeb;
  color: #92400e;
}

.toast--info {
  border-left-color: #3b82f6;
  background: #eff6ff;
  color: #1e40af;
}

.toast-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.toast--error .toast-icon { color: #ef4444; }
.toast--success .toast-icon { color: #22c55e; }
.toast--warning .toast-icon { color: #f59e0b; }
.toast--info .toast-icon { color: #3b82f6; }

.toast-msg {
  flex: 1;
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  border-radius: 6px;
  color: #94a3b8;
  display: flex;
  align-items: center;
}

.toast-close:hover {
  color: #475569;
  background: rgba(0, 0, 0, 0.06);
}

.toast-close span {
  font-size: 18px;
}

/* Transitions */
.toast-slide-enter-active {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s ease;
}
.toast-slide-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.toast-slide-enter-from {
  transform: translateX(100%);
  opacity: 0;
}
.toast-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
