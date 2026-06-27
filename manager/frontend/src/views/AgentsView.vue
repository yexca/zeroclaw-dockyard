<template>
  <section class="view-stack">
    <PageHeader :title="t('agents.title')" :description="t('agents.subtitle')">
      <UiButton variant="primary" @click="createAgent"><Plus />{{ t("agents.newAgent") }}</UiButton>
    </PageHeader>

    <div class="agent-workbench">
      <UiCard :title="t('agents.list')" :description="t('agents.listHelp')">
        <div class="item-list">
          <button v-for="agent in store.agents" :key="itemId(agent)" :class="{ active: selectedId === itemId(agent) }" @click="selectAgent(agent)">
            <strong>{{ itemId(agent) }}</strong>
            <span>{{ agent.llm_profile || t("agents.noLlm") }} / {{ agent.matrix_profile || t("agents.noMatrix") }}</span>
          </button>
          <p v-if="!store.agents.length" class="empty-text">{{ t("agents.emptyList") }}</p>
        </div>
      </UiCard>

      <UiCard :title="t('agents.details')" :description="draft?._draft ? t('agents.unsaved') : t('agents.detailsHelp')">
        <form v-if="draft" class="form-grid" @submit.prevent="save">
          <FormField v-model="draft.id" :label="t('agents.agentId')" />
          <FormField v-model="draft.host_port" :label="t('fields.hostPort')" type="number" />
          <FormField v-model="draft.llm_profile" :label="t('fields.llmProfile')" :options="profileOptions('llm')" />
          <FormField v-model="draft.vision_profile" :label="t('fields.visionProfile')" :options="profileOptions('vision', true)" />
          <FormField v-model="draft.matrix_profile" :label="t('fields.matrixProfile')" :options="profileOptions('matrix')" />
          <FormField v-model="draft.mcp_profile" :label="t('fields.mcpProfile')" :options="profileOptions('mcp', true)" />
          <FormField v-model="draft.prompt_template" :label="t('fields.promptTemplate')" :options="templateOptions" />
          <FormField v-model="imagePreset" :label="t('fields.imagePreset')" :options="imageOptions" wide />
          <FormField v-model="draft.image" :label="t('fields.dockerImage')" wide />
          <FormField v-model="externalPeers" :label="t('fields.externalPeers')" textarea wide />
          <FormField v-model="skillBundles" :label="t('fields.skillBundles')" textarea wide />
          <details class="advanced-disclosure form-field--wide">
            <summary>{{ t("fields.advanced") }}</summary>
            <div class="form-grid nested-form">
              <label class="check-row form-field--wide">
                <input v-model="draft.enabled" type="checkbox" />
                <span>{{ t("fields.enabled") }}</span>
              </label>
              <FormField v-model="draft.template_apply_mode" :label="t('fields.templateApplyMode')" :options="templateModeOptions" />
              <FormField v-model="draft.storage_driver" :label="t('fields.storageDriver')" :options="storageOptions" />
              <FormField v-model="draft.container_name" :label="t('fields.containerName')" />
              <FormField v-model="envOverrides" :label="t('fields.environment')" textarea wide />
            </div>
          </details>
          <details class="advanced-disclosure form-field--wide">
            <summary>{{ t("fields.proactiveSettings") }}</summary>
            <div class="form-grid nested-form">
              <label class="check-row form-field--wide">
                <input v-model="proactive.enabled" type="checkbox" />
                <span>{{ t("fields.enabled") }}</span>
              </label>
              <FormField v-model="proactive.target" :label="t('fields.proactiveTarget')" />
              <FormField v-model="proactive.channel" :label="t('fields.proactiveChannel')" />
              <FormField v-model="proactive.timezone" :label="t('fields.proactiveTimezone')" />
              <FormField v-model="proactive.quiet_hours" :label="t('fields.proactiveQuietHours')" />
              <FormField v-model="proactive.random_min_minutes" :label="t('fields.proactiveRandomMinMinutes')" type="number" />
              <FormField v-model="proactive.random_max_minutes" :label="t('fields.proactiveRandomMaxMinutes')" type="number" />
              <FormField v-model="proactive.poll_seconds" :label="t('fields.proactivePollSeconds')" type="number" />
              <FormField v-model="proactive.agent_url" :label="t('fields.proactiveAgentUrl')" />
              <FormField v-model="proactive.prompt" :label="t('agents.wakePrompt')" textarea wide />
            </div>
          </details>
          <div class="button-row form-field--wide">
            <UiButton variant="primary" type="submit"><Save />{{ t("actions.save") }}</UiButton>
            <UiButton v-if="!draft._draft" @click="control('start')"><Play />{{ t("actions.start") }}</UiButton>
            <UiButton v-if="!draft._draft" @click="control('stop')"><Square />{{ t("actions.stop") }}</UiButton>
            <UiButton v-if="!draft._draft" @click="control('restart')"><RotateCw />{{ t("actions.restart") }}</UiButton>
            <UiButton v-if="!draft._draft" variant="danger" @click="resetMatrix"><RefreshCcw />{{ t("actions.resetMatrixState") }}</UiButton>
            <UiButton v-if="!draft._draft" variant="danger" @click="remove"><Trash2 />{{ t("actions.delete") }}</UiButton>
          </div>
        </form>
        <p v-else class="empty-text">{{ t("agents.empty") }}</p>
      </UiCard>

      <UiCard :title="t('agents.runtime')" :description="t('agents.runtimeHelp')">
        <template v-if="draft && !draft._draft">
          <div class="runtime-actions">
            <UiButton @click="loadStatus"><Activity />{{ t("runtimeTabs.status") }}</UiButton>
            <label class="inline-select">
              <span>{{ t("dashboard.tail") }}</span>
              <input v-model.number="logTail" type="number" min="1" max="2000" />
            </label>
            <UiButton @click="loadLogs"><ScrollText />{{ t("runtimeTabs.logs") }}</UiButton>
            <UiButton @click="loadPreview"><FileCode2 />{{ t("runtimeTabs.config") }}</UiButton>
            <UiButton @click="loadEnv"><Braces />{{ t("runtimeTabs.env") }}</UiButton>
            <UiButton @click="downloadLogs"><Download />{{ t("actions.downloadLogs") }}</UiButton>
          </div>
          <div class="runtime-actions">
            <label class="inline-select">
              <span>{{ t("agents.applyMode") }}</span>
              <select v-model="applyTemplateMode">
                <option v-for="option in templateModeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </label>
            <UiButton @click="applyTemplate"><FileCheck2 />{{ t("actions.applyTemplate") }}</UiButton>
            <UiButton @click="runAgentAction('publish')"><Upload />{{ t("actions.publish") }}</UiButton>
            <UiButton @click="runAgentAction('sync-to-runtime')"><ArrowUpFromLine />{{ t("actions.syncToRuntime") }}</UiButton>
            <UiButton @click="runAgentAction('sync-from-runtime')"><ArrowDownToLine />{{ t("actions.syncFromRuntime") }}</UiButton>
          </div>
          <div class="segment-tabs">
            <button v-for="tab in runtimeTabs" :key="tab" :class="{ active: runtimeTab === tab }" @click="runtimeTab = tab">{{ t(`runtimeTabs.${tab}`) }}</button>
          </div>
          <div v-if="runtimeTab === 'status'" class="runtime-summary">
            <div v-for="(value, key) in statusSummary" :key="key">
              <span>{{ key }}</span>
              <strong>{{ value }}</strong>
            </div>
          </div>
          <pre v-else-if="runtimeTab === 'logs'" class="code-block">{{ logsText }}</pre>
          <pre v-else-if="runtimeTab === 'config'" class="code-block">{{ configText }}</pre>
          <pre v-else-if="runtimeTab === 'env'" class="code-block">{{ envText }}</pre>
          <pre v-else class="code-block">{{ resultText }}</pre>
        </template>
        <p v-else class="empty-text">{{ t("agents.saveBeforeRuntime") }}</p>
      </UiCard>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import {
  Activity,
  ArrowDownToLine,
  ArrowUpFromLine,
  Braces,
  Download,
  FileCheck2,
  FileCode2,
  Plus,
  Play,
  RefreshCcw,
  RotateCw,
  Save,
  ScrollText,
  Square,
  Trash2,
  Upload
} from "@lucide/vue";
import FormField from "../components/FormField.vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { useDialog } from "../composables/useDialog.js";
import { useI18n } from "../composables/useI18n.js";
import { clone, itemId } from "../lib/api.js";
import { useManagerStore } from "../stores/manager.js";

const store = useManagerStore();
const { t } = useI18n();
const dialog = useDialog();
const selectedId = ref("");
const draft = ref(null);
const runtimeTab = ref("status");
const runtimeTabs = ["status", "logs", "config", "env", "result"];
const runtimeStatus = ref(null);
const runtimeLogs = ref(null);
const runtimeConfig = ref(null);
const runtimeEnv = ref(null);
const runtimeResult = ref(null);
const applyTemplateMode = ref("keep");
const logTail = ref(200);
const DEFAULT_ZEROCLAW_IMAGE = "ghcr.io/zeroclaw-labs/zeroclaw:v0.8.1-debian";
const templateModeOptions = [
  { label: t("templateApply.keep"), value: "keep" },
  { label: t("templateApply.missing"), value: "missing" },
  { label: t("templateApply.overwrite"), value: "overwrite" },
  { label: t("templateApply.merge"), value: "merge" }
];
const storageOptions = [
  { label: t("common.default"), value: "" },
  { label: t("agents.storage.volume"), value: "volume" },
  { label: t("agents.storage.bind"), value: "bind" }
];

const imageOptions = computed(() => {
  const recommended = store.images?.recommended || {
    official: DEFAULT_ZEROCLAW_IMAGE,
    python: "zeroclaw-python:v0.8.1-debian",
    root: "zeroclaw-root:v0.8.1-debian"
  };
  return [
    { label: t("images.custom"), value: "__custom__" },
    { label: t("images.official"), value: recommended.official },
    { label: t("images.python"), value: recommended.python },
    { label: t("images.root"), value: recommended.root }
  ];
});

const imagePreset = computed({
  get: () => {
    const match = imageOptions.value.find((option) => option.value === draft.value?.image);
    return match ? match.value : "__custom__";
  },
  set: (value) => {
    if (value !== "__custom__") draft.value.image = value;
  }
});

watch(
  () => store.agents,
  (agents) => {
    if (!draft.value && agents.length) selectAgent(agents[0]);
  },
  { immediate: true }
);

const externalPeers = computed({
  get: () => (draft.value?.matrix?.external_peers || draft.value?.external_peers || []).join("\n"),
  set: (value) => {
    const peers = value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (!draft.value.matrix) draft.value.matrix = {};
    draft.value.matrix.external_peers = peers;
    delete draft.value.external_peers;
  }
});

const skillBundles = computed({
  get: () => (draft.value?.skill_bundles || []).join("\n"),
  set: (value) => (draft.value.skill_bundles = value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean))
});

const envOverrides = computed({
  get: () => {
    const env = draft.value?.environment || draft.value?.env || {};
    return Object.entries(env).map(([key, value]) => `${key}=${value}`).join("\n");
  },
  set: (value) => {
    draft.value.environment = Object.fromEntries(
      value
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const index = line.indexOf("=");
          return index >= 0 ? [line.slice(0, index).trim(), line.slice(index + 1)] : [line, ""];
        })
    );
  }
});

const proactive = computed({
  get: () => {
    if (!draft.value.proactive) draft.value.proactive = {};
    return draft.value.proactive;
  },
  set: (value) => (draft.value.proactive = value)
});

const templateOptions = computed(() => [
  { label: t("common.none"), value: "" },
  ...store.templates.map((template) => ({ label: itemId(template), value: itemId(template) }))
]);

function profileOptions(kind, optional = false) {
  const values = (store.profiles[kind] || []).map((profile) => ({ label: itemId(profile), value: itemId(profile) }));
  return optional ? [{ label: t("common.none"), value: "" }, ...values] : values;
}

function selectAgent(agent) {
  selectedId.value = itemId(agent);
  draft.value = clone(agent);
  runtimeStatus.value = null;
  runtimeLogs.value = null;
  runtimeConfig.value = null;
  runtimeEnv.value = null;
  runtimeResult.value = null;
}

function createAgent() {
  draft.value = { ...store.newAgent(), _draft: true };
  selectedId.value = "";
}

async function save() {
  const payload = clone(draft.value);
  delete payload._draft;
  await store.saveAgent(payload);
  selectedId.value = payload.id;
  draft.value = payload;
}

async function remove() {
  if (!draft.value?._draft && await dialog.confirm(t("confirm.deleteAgentNamed", { id: draft.value.id }))) {
    await store.deleteAgent(draft.value.id);
    draft.value = null;
    selectedId.value = "";
  }
}

const statusSummary = computed(() => {
  const status = runtimeStatus.value || {};
  return {
    state: status.state || status.status || t("common.unknown"),
    health: status.health || "-",
    image: status.image || draft.value?.image || "-",
    mapped_port: status.mapped_port || status.port || draft.value?.host_port || "-",
    config_hash: status.config_hash || "-",
    latest_export: status.latest_export_time || "-"
  };
});

const logsText = computed(() => {
  if (!runtimeLogs.value) return t("dashboard.logsEmpty");
  return (runtimeLogs.value.lines || []).join("\n") || JSON.stringify(runtimeLogs.value, null, 2);
});

const configText = computed(() => formatRuntime(runtimeConfig.value, t("agents.noConfigPreview")));
const envText = computed(() => formatRuntime(runtimeEnv.value, t("agents.noEnvPreview")));
const resultText = computed(() => formatRuntime(runtimeResult.value, t("agents.noActionResult")));

function formatRuntime(value, empty) {
  if (!value) return empty;
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

async function loadStatus() {
  runtimeStatus.value = await store.getAgentStatus(draft.value.id);
  runtimeTab.value = "status";
}

async function loadLogs() {
  runtimeLogs.value = await store.getAgentLogs(draft.value.id, logTail.value);
  runtimeTab.value = "logs";
}

async function loadPreview() {
  runtimeConfig.value = await store.getAgentPreview(draft.value.id);
  runtimeTab.value = "config";
}

async function loadEnv() {
  runtimeEnv.value = await store.getAgentEnv(draft.value.id);
  runtimeTab.value = "env";
}

async function runAgentAction(action) {
  runtimeResult.value = await store.agentAction(draft.value.id, action);
  runtimeTab.value = "result";
  await loadStatus();
}

async function applyTemplate() {
  runtimeResult.value = await store.agentAction(draft.value.id, "apply-template", { mode: applyTemplateMode.value });
  runtimeTab.value = "result";
  await loadStatus();
}

async function control(operation) {
  await store.controlAgent(draft.value.id, operation);
  await loadStatus();
  if (operation !== "stop") await loadLogs();
}

function downloadLogs() {
  window.location.href = store.agentLogsDownloadUrl(draft.value.id, logTail.value);
}

async function resetMatrix() {
  if (!(await dialog.confirm(t("confirm.resetMatrixStateNamed", { id: draft.value.id })))) return;
  await runAgentAction("reset-matrix-state");
}

onMounted(() => {
  if (!store.images) store.loadImages().catch((error) => store.setError(error));
});
</script>
