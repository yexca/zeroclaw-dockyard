import { reactive } from "vue";

const state = reactive({
  current: null,
  queue: []
});

let nextId = 1;

function openDialog(options) {
  return new Promise((resolve) => {
    const request = {
      id: nextId++,
      type: options.type || "alert",
      titleKey: options.titleKey || "",
      message: options.message || "",
      defaultValue: options.defaultValue || "",
      resolve
    };
    if (state.current) {
      state.queue.push(request);
    } else {
      state.current = request;
    }
  });
}

function closeDialog(result) {
  const current = state.current;
  if (!current) return;
  state.current = state.queue.shift() || null;
  current.resolve(result);
}

export function useDialog() {
  return {
    state,
    alert(message, options = {}) {
      return openDialog({ ...options, type: "alert", message });
    },
    confirm(message, options = {}) {
      return openDialog({ ...options, type: "confirm", message });
    },
    prompt(message, defaultValue = "", options = {}) {
      return openDialog({ ...options, type: "prompt", message, defaultValue });
    },
    closeDialog
  };
}
