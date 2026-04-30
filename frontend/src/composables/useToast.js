import { ref } from "vue";

const toasts = ref([]);

let idCounter = 0;

export function useToast() {
  function toast(options = {}) {
    const id = ++idCounter;
    const t = {
      id,
      message: typeof options === "string" ? options : options.message || "",
      type: options.type || "error", // 'success' | 'error' | 'warning' | 'info'
      duration: options.duration || 4000,
    };

    toasts.value.push(t);

    setTimeout(() => {
      removeToast(id);
    }, t.duration);
  }

  function removeToast(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  return { toasts, toast, removeToast };
}
