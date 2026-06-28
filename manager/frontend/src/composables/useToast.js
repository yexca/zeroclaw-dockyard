import { reactive } from "vue";

const DEFAULT_DURATION = {
  success: 5000,
  error: 20000,
  info: 5000
};

const state = reactive({
  toasts: []
});

let nextId = 1;

export function useToast() {
  function push(message, options = {}) {
    const variant = options.variant || "info";
    const durationMs = Number(options.durationMs || DEFAULT_DURATION[variant] || DEFAULT_DURATION.info);
    const toast = {
      id: nextId++,
      message: String(message || ""),
      title: options.title || "",
      variant,
      durationMs,
      createdAt: Date.now()
    };
    state.toasts.push(toast);
    globalThis.setTimeout?.(() => dismiss(toast.id), durationMs);
    return toast.id;
  }

  function dismiss(id) {
    const index = state.toasts.findIndex((toast) => toast.id === id);
    if (index >= 0) state.toasts.splice(index, 1);
  }

  return {
    state,
    success(message, options = {}) {
      return push(message, { ...options, variant: "success" });
    },
    error(message, options = {}) {
      return push(message, { ...options, variant: "error" });
    },
    info(message, options = {}) {
      return push(message, { ...options, variant: "info" });
    },
    dismiss
  };
}
