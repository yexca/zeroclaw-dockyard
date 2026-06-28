<template>
  <Teleport to="body">
    <div class="toast-region" aria-live="polite" aria-atomic="false">
      <article v-for="toast in state.toasts" :key="toast.id" :class="['toast-card', `toast-card--${toast.variant}`]">
        <div>
          <strong>{{ toast.title || titleFor(toast.variant) }}</strong>
          <p>{{ toast.message }}</p>
        </div>
        <UiButton icon :aria-label="t('actions.close')" @click="dismiss(toast.id)"><X /></UiButton>
        <span class="toast-progress" :style="{ animationDuration: `${toast.durationMs}ms` }"></span>
      </article>
    </div>
  </Teleport>
</template>

<script setup>
import { X } from "@lucide/vue";
import UiButton from "./UiButton.vue";
import { useI18n } from "../composables/useI18n.js";
import { useToast } from "../composables/useToast.js";

const { t } = useI18n();
const { state, dismiss } = useToast();

function titleFor(variant) {
  if (variant === "error") return t("toast.error");
  if (variant === "success") return t("toast.success");
  return t("toast.info");
}
</script>
