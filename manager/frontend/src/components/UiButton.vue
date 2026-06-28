<template>
  <button
    class="ui-button"
    :class="[`ui-button--${variant}`, { 'ui-button--icon': icon, 'ui-button--loading': loading }]"
    :type="type"
    :disabled="disabled || loading"
    :title="resolvedTitle"
    :aria-busy="loading ? 'true' : undefined"
    v-bind="buttonAttrs"
  >
    <slot />
  </button>
</template>

<script setup>
import { computed, useAttrs } from "vue";

defineOptions({ inheritAttrs: false });

const props = defineProps({
  variant: { type: String, default: "secondary" },
  type: { type: String, default: "button" },
  icon: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  tooltip: { type: String, default: "" }
});

const attrs = useAttrs();
const resolvedTitle = computed(() => props.tooltip || attrs.title || attrs["aria-label"] || "");
const buttonAttrs = computed(() => {
  const { title: _title, disabled: _disabled, ...rest } = attrs;
  return rest;
});
</script>
