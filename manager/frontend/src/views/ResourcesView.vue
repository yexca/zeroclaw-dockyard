<template>
  <section class="view-stack">
    <PageHeader title="Docker Resources" description="Containers, networks, and volumes classified by manager ownership.">
      <UiButton variant="primary" @click="store.loadResources"><RefreshCw />Refresh</UiButton>
    </PageHeader>

    <div class="metric-grid">
      <UiCard v-for="group in groups" :key="group.kind" :title="group.title">
        <strong class="metric-value">{{ countRows(group.data) }}</strong>
        <p class="empty-text">{{ summary(group.data) }}</p>
      </UiCard>
    </div>

    <UiCard v-for="group in groups" :key="`${group.kind}-detail`" :title="group.title">
      <div class="resource-buckets">
        <details v-for="bucket in buckets" :key="bucket.id" class="advanced-disclosure resource-bucket" :open="bucket.id === 'conflicts'">
          <summary>{{ bucket.label }} · {{ rowsFor(group.data, bucket.id).length }}</summary>
          <div v-if="rowsFor(group.data, bucket.id).length" class="resource-row-list">
            <article v-for="row in rowsFor(group.data, bucket.id)" :key="resourceKey(group.kind, row)" class="resource-card">
              <div>
                <strong>{{ row.name || row.id || row.container_name || "unnamed" }}</strong>
                <span>{{ row.image || row.role || row.state || row.classification || bucket.label }}</span>
              </div>
              <div class="button-row">
                <UiButton v-if="canAdopt(bucket.id)" @click="runAction('adopt', group.kind, row)">Adopt</UiButton>
                <UiButton v-if="canIgnore(bucket.id)" @click="runAction('ignore', group.kind, row)">Ignore</UiButton>
                <UiButton v-if="bucket.id === 'ignored' || bucket.id === 'adopted'" @click="runAction('clear', group.kind, row)">Clear</UiButton>
                <UiButton v-if="bucket.id === 'legacy'" @click="migrate(group.kind, row)">Migrate</UiButton>
                <UiButton v-if="canDelete(bucket.id)" variant="danger" @click="deleteResource(group.kind, row)">Delete</UiButton>
              </div>
            </article>
          </div>
          <p v-else class="empty-text">No resources in this bucket.</p>
        </details>
      </div>
    </UiCard>

    <UiCard v-if="lastResult" title="Last resource action">
      <pre class="code-block">{{ JSON.stringify(lastResult, null, 2) }}</pre>
    </UiCard>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RefreshCw } from "@lucide/vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { useManagerStore } from "../stores/manager.js";

const store = useManagerStore();
const lastResult = ref(null);
const buckets = [
  { id: "expected", label: "Expected" },
  { id: "conflicts", label: "Conflicts" },
  { id: "orphans", label: "Orphans" },
  { id: "legacy", label: "Untracked" },
  { id: "adopted", label: "Adopted" },
  { id: "ignored", label: "Ignored" }
];

const groups = computed(() => [
  { kind: "container", title: "Containers", data: store.resources?.containers || {} },
  { kind: "volume", title: "Volumes", data: store.resources?.volumes || {} },
  { kind: "network", title: "Networks", data: store.resources?.networks || {} }
]);

function rowsFor(group, bucket) {
  return Array.isArray(group?.[bucket]) ? group[bucket] : [];
}

function countRows(group) {
  return buckets.reduce((total, bucket) => total + rowsFor(group, bucket.id).length, 0);
}

function summary(group) {
  return buckets.map((bucket) => `${bucket.label}: ${rowsFor(group, bucket.id).length}`).join(" · ");
}

function resourceName(row) {
  return row.name || row.id || row.container_name || row.volume_name || row.network_name || "";
}

function resourceKey(kind, row) {
  return `${kind}:${resourceName(row)}:${row.classification || row.state || ""}`;
}

function canAdopt(bucket) {
  return ["legacy", "orphans", "conflicts"].includes(bucket);
}

function canIgnore(bucket) {
  return ["legacy", "orphans", "conflicts"].includes(bucket);
}

function canDelete(bucket) {
  return ["orphans", "legacy", "conflicts"].includes(bucket);
}

async function runAction(action, kind, row, extra = {}) {
  lastResult.value = await store.resourceAction(action, { kind, name: resourceName(row) }, extra);
}

async function migrate(kind, row) {
  const target_name = prompt("Target resource name", `${resourceName(row)}-migrated`);
  if (!target_name) return;
  await runAction("migrate", kind, row, { target_name });
}

async function deleteResource(kind, row) {
  const name = resourceName(row);
  const typed = prompt(`Type ${name} to delete this ${kind}.`);
  if (typed !== name) return;
  await runAction("delete", kind, row);
}

onMounted(() => store.loadResources().catch((error) => store.setError(error)));
</script>
