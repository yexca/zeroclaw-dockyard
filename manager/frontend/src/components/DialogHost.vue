<template>
  <Teleport to="body">
    <div v-if="dialog" ref="overlayRef" class="dialog-overlay" tabindex="-1" @keydown.esc.prevent="cancel">
      <section class="dialog-panel" role="dialog" aria-modal="true" :aria-labelledby="titleId">
        <header class="dialog-header">
          <h2 :id="titleId">{{ title }}</h2>
          <UiButton :aria-label="t('actions.close')" icon @click="cancel"><X /></UiButton>
        </header>

        <p class="dialog-message">{{ dialog.message }}</p>

        <form v-if="dialog.type === 'prompt'" class="dialog-form" @submit.prevent="submit">
          <input ref="inputRef" v-model="inputValue" type="text" />
        </form>

        <footer class="dialog-actions">
          <UiButton v-if="dialog.type !== 'alert'" @click="cancel">{{ t("actions.cancel") }}</UiButton>
          <UiButton :variant="primaryVariant" @click="submit">{{ primaryLabel }}</UiButton>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { X } from "@lucide/vue";
import UiButton from "./UiButton.vue";
import { useDialog } from "../composables/useDialog.js";
import { useI18n } from "../composables/useI18n.js";

const { state, closeDialog } = useDialog();
const { t } = useI18n();
const overlayRef = ref(null);
const inputRef = ref(null);
const inputValue = ref("");

const dialog = computed(() => state.current);
const titleId = computed(() => `dialog-title-${dialog.value?.id || "current"}`);
const title = computed(() => {
  if (dialog.value?.titleKey) return t(dialog.value.titleKey);
  if (dialog.value?.type === "confirm") return t("dialog.confirmTitle");
  if (dialog.value?.type === "prompt") return t("dialog.promptTitle");
  return t("dialog.alertTitle");
});
const primaryLabel = computed(() => (dialog.value?.type === "alert" ? t("actions.close") : t("actions.confirm")));
const primaryVariant = computed(() => (dialog.value?.type === "confirm" ? "danger" : "primary"));

watch(
  dialog,
  async (nextDialog) => {
    inputValue.value = nextDialog?.defaultValue || "";
    await nextTick();
    if (nextDialog?.type === "prompt") {
      inputRef.value?.focus();
      inputRef.value?.select();
    } else {
      overlayRef.value?.focus();
    }
  },
  { immediate: true }
);

function cancel() {
  if (!dialog.value) return;
  closeDialog(dialog.value.type === "confirm" ? false : null);
}

function submit() {
  if (!dialog.value) return;
  if (dialog.value.type === "confirm") {
    closeDialog(true);
  } else if (dialog.value.type === "prompt") {
    closeDialog(inputValue.value);
  } else {
    closeDialog(true);
  }
}
</script>
