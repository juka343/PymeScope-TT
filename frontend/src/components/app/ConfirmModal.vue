<script setup>
import { useConfirm } from "@/composables/useConfirm";

const { isOpen, title, message, confirmText, cancelText, variant, handleConfirm, handleCancel } =
  useConfirm();
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm-fade">
      <div v-if="isOpen" class="confirm-overlay" @click.self="handleCancel">
        <Transition name="confirm-scale" appear>
          <div v-if="isOpen" class="confirm-modal" role="dialog" aria-modal="true">
            <!-- Icono -->
            <div class="confirm-icon" :class="`confirm-icon--${variant}`">
              <span class="material-symbols-outlined">
                {{ variant === "danger" ? "delete_forever" : variant === "warning" ? "warning" : "info" }}
              </span>
            </div>

            <!-- Contenido -->
            <h3 class="confirm-title">{{ title }}</h3>
            <p v-if="message" class="confirm-message">{{ message }}</p>

            <!-- Acciones -->
            <div class="confirm-actions">
              <button class="confirm-btn confirm-btn--cancel" @click="handleCancel">
                {{ cancelText }}
              </button>
              <button
                class="confirm-btn"
                :class="`confirm-btn--${variant}`"
                @click="handleConfirm"
              >
                {{ confirmText }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  padding: 24px;
}

.confirm-modal {
  background: white;
  border-radius: 20px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.2);
  padding: 28px 24px 22px;
  width: 100%;
  max-width: 400px;
  text-align: center;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

.confirm-icon {
  width: 56px;
  height: 56px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  margin: 0 auto 16px;
}

.confirm-icon span {
  font-size: 28px;
}

.confirm-icon--danger {
  background: #fee2e2;
  color: #ef4444;
}

.confirm-icon--warning {
  background: #fef3c7;
  color: #f59e0b;
}

.confirm-icon--info {
  background: #dbeafe;
  color: #3b82f6;
}

.confirm-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 900;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.confirm-message {
  margin: 0 0 20px;
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
}

.confirm-actions {
  display: flex;
  gap: 10px;
}

.confirm-btn {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: filter 0.15s ease, transform 0.05s ease;
}

.confirm-btn:hover {
  filter: brightness(0.95);
}

.confirm-btn:active {
  transform: translateY(1px);
}

.confirm-btn--cancel {
  background: #f1f5f9;
  color: #475569;
}

.confirm-btn--cancel:hover {
  background: #e2e8f0;
}

.confirm-btn--danger {
  background: #ef4444;
  color: white;
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.3);
}

.confirm-btn--warning {
  background: #f59e0b;
  color: white;
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.3);
}

.confirm-btn--info {
  background: #3b82f6;
  color: white;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3);
}

/* Transitions */
.confirm-fade-enter-active,
.confirm-fade-leave-active {
  transition: opacity 0.2s ease;
}
.confirm-fade-enter-from,
.confirm-fade-leave-to {
  opacity: 0;
}

.confirm-scale-enter-active {
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease;
}
.confirm-scale-leave-active {
  transition: transform 0.15s ease, opacity 0.15s ease;
}
.confirm-scale-enter-from {
  transform: scale(0.9);
  opacity: 0;
}
.confirm-scale-leave-to {
  transform: scale(0.95);
  opacity: 0;
}
</style>
