<template>
  <section class="view-stack">
    <PageHeader title="Docker Images" description="Inspect ZeroClaw runtime images and local derived variants.">
      <UiButton variant="primary" @click="store.loadImages"><RefreshCw />Refresh</UiButton>
    </PageHeader>

    <div class="button-row">
      <UiButton variant="primary" @click="runImageAction('pull-official')"><Download />Pull official</UiButton>
      <UiButton @click="runBuild('build-python')"><Hammer />Build Python image</UiButton>
      <UiButton variant="danger" @click="runBuild('build-root')"><ShieldAlert />Build root image</UiButton>
    </div>

    <UiCard title="Docker images">
      <div class="data-table">
        <div class="data-row data-row--head"><span>Reference</span><span>Status</span><span>ID</span><span>Size</span></div>
        <div v-for="image in rows" :key="image.reference || image.id" class="data-row">
          <span><strong>{{ image.reference || image.repo_tags?.[0] || "untagged" }}</strong></span>
          <span><mark :class="image.present === false ? 'bad' : 'good'">{{ image.present === false ? "missing" : "present" }}</mark></span>
          <span>{{ image.short_id || image.id || "-" }}</span>
          <span>{{ image.size || image.size_human || "-" }}</span>
        </div>
        <p v-if="!rows.length" class="empty-text">No image data loaded.</p>
      </div>
    </UiCard>

    <UiCard v-if="lastResult" title="Last image action">
      <pre class="code-block">{{ JSON.stringify(lastResult, null, 2) }}</pre>
    </UiCard>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { Download, Hammer, RefreshCw, ShieldAlert } from "@lucide/vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { useManagerStore } from "../stores/manager.js";

const store = useManagerStore();
const rows = computed(() => store.images?.images || store.images?.rows || []);
const lastResult = ref(null);

async function runImageAction(action, extra = {}) {
  lastResult.value = await store.imageAction(action, extra);
}

async function runBuild(action) {
  const kind = action === "build-root" ? "root-user" : "Python support";
  const ok = confirm(`Building the ${kind} image executes Dockerfile steps through the Docker daemon. Continue?`);
  if (!ok) return;
  await runImageAction(action, { acknowledge_risk: true });
}

onMounted(() => store.loadImages().catch((error) => store.setError(error)));
</script>
