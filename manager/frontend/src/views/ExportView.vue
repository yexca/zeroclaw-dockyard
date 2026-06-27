<template>
  <section class="view-stack">
    <PageHeader :title="t('export.title')" :description="t('export.subtitle')">
      <UiButton variant="primary" @click="runExport"><FileArchive />{{ t("actions.export") }}</UiButton>
    </PageHeader>

    <UiCard :title="t('export.options')">
      <label class="check-row">
        <input v-model="includeSecrets" type="checkbox" />
        <span>{{ t("export.includeSecrets") }}</span>
      </label>
      <pre v-if="result" class="code-block">{{ JSON.stringify(result, null, 2) }}</pre>
    </UiCard>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { FileArchive } from "@lucide/vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { useI18n } from "../composables/useI18n.js";
import { useManagerStore } from "../stores/manager.js";

const store = useManagerStore();
const { t } = useI18n();
const includeSecrets = ref(false);
const result = ref(null);

async function runExport() {
  result.value = await store.exportConfig(includeSecrets.value);
}
</script>
