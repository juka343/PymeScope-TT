import { ref } from "vue";

const isOpen = ref(false);
const title = ref("");
const message = ref("");
const confirmText = ref("Eliminar");
const cancelText = ref("Cancelar");
const variant = ref("danger"); // 'danger' | 'warning' | 'info'

let resolvePromise = null;

export function useConfirm() {
  function confirm(options = {}) {
    title.value = options.title || "¿Estás seguro?";
    message.value = options.message || "";
    confirmText.value = options.confirmText || "Eliminar";
    cancelText.value = options.cancelText || "Cancelar";
    variant.value = options.variant || "danger";
    isOpen.value = true;

    return new Promise((resolve) => {
      resolvePromise = resolve;
    });
  }

  function handleConfirm() {
    isOpen.value = false;
    if (resolvePromise) resolvePromise(true);
  }

  function handleCancel() {
    isOpen.value = false;
    if (resolvePromise) resolvePromise(false);
  }

  return {
    isOpen,
    title,
    message,
    confirmText,
    cancelText,
    variant,
    confirm,
    handleConfirm,
    handleCancel,
  };
}
