<template>
  <section class="view-stack">
    <PageHeader :title="t('dashboard.title')" :description="t('dashboard.subtitle')">
      <UiButton variant="primary" @click="refreshDashboard"><RefreshCw />{{ t("actions.refresh") }}</UiButton>
    </PageHeader>

    <div class="metric-grid">
      <UiCard :title="t('dashboard.metrics.configuredAgents')"><strong class="metric-value">{{ store.agents.length }}</strong></UiCard>
      <UiCard :title="t('dashboard.metrics.runningAgents')"><strong class="metric-value">{{ runningCount }}</strong></UiCard>
      <UiCard :title="t('dashboard.metrics.needsAttention')"><strong class="metric-value">{{ attentionCount }}</strong></UiCard>
      <UiCard :title="t('dashboard.metrics.needsRebuild')"><strong class="metric-value">{{ rebuildCount }}</strong></UiCard>
    </div>

    <p v-if="dashboardError" class="field-error">{{ dashboardError }}</p>
    <p v-else-if="dashboardLoading && !dashboardAgents.length" class="empty-text">{{ t("status.loading") }}</p>

    <div class="runtime-groups">
      <UiCard v-for="group in runtimeGroups" :key="group.key" :title="group.title" :description="group.description">
        <div class="agent-chip-list">
          <RouterLink v-for="agent in group.agents" :key="`${group.key}-${agent.id}`" class="agent-status-chip" :to="agentRoute(agent.id)">
            <span>
              <strong>{{ agent.id }}</strong>
              <small>{{ agent.mapped_port || agent.image || "-" }}</small>
            </span>
            <mark :class="statusClass(agent.state)">{{ agent.state }}</mark>
            <mark v-if="agent.needs_rebuild" class="bad">{{ t("observability.rebuild") }}</mark>
          </RouterLink>
          <p v-if="!group.agents.length" class="empty-text">{{ t("dashboard.emptyGroup") }}</p>
        </div>
      </UiCard>
    </div>

    <UiCard :title="t('dashboard.runtimeRows')" :description="t('dashboard.runtimeRowsHelp')">
      <div class="data-table">
        <div class="data-row data-row--head">
          <span>{{ t("dashboard.table.agent") }}</span>
          <span>{{ t("dashboard.table.status") }}</span>
          <span>{{ t("dashboard.table.image") }}</span>
          <span>{{ t("dashboard.table.actions") }}</span>
        </div>
        <div v-for="agent in dashboardAgents" :key="agent.id || agent.name" class="data-row">
          <span>
            <strong>{{ agent.id || agent.name }}</strong>
            <small v-if="agent.needs_rebuild" class="inline-warning">{{ t("observability.rebuild") }}</small>
          </span>
          <span><mark :class="statusClass(agent.state)">{{ agent.state || t("common.unknown") }}</mark></span>
          <span>{{ agent.image || "-" }}</span>
          <span class="inline-actions">
            <UiButton icon :aria-label="t('actions.start')" @click="control(agent.id, 'start')"><Play /></UiButton>
            <UiButton icon :aria-label="t('actions.stop')" @click="control(agent.id, 'stop')"><Square /></UiButton>
            <UiButton icon :aria-label="t('actions.restart')" @click="control(agent.id, 'restart')"><RotateCw /></UiButton>
            <RouterLink class="icon-link" :aria-label="t('actions.logs')" :to="agentRoute(agent.id)"><ScrollText /></RouterLink>
          </span>
        </div>
        <p v-if="!dashboardAgents.length && !dashboardLoading" class="empty-text">{{ emptyDashboardText }}</p>
      </div>
    </UiCard>

    <div class="split-panels">
      <UiCard :title="t('dashboard.recentLogs')" :description="t('dashboard.recentLogsHelp')">
        <div class="log-summary-list">
          <p v-if="logsLoading" class="empty-text">{{ t("status.loading") }}</p>
          <div v-for="summary in logSummaries" :key="summary.id" class="log-summary-row">
            <strong>{{ summary.id }}</strong>
            <pre>{{ summary.text }}</pre>
          </div>
          <p v-if="!logsLoading && !logSummaries.length" class="empty-text">{{ t("dashboard.logsEmpty") }}</p>
        </div>
      </UiCard>

      <UiCard :title="t('history.title')" :description="t('history.subtitle')">
        <div class="history-list">
          <div v-for="entry in pagedHistoryEntries" :key="`${entry.timestamp}-${entry.operation}-${entry.agent_id}`" class="history-row">
            <mark :class="entry.status === 'ok' ? 'good' : 'bad'">{{ entry.status || "ok" }}</mark>
            <div>
              <strong>{{ entry.operation }}</strong>
              <small>{{ entry.agent_id || t("common.none") }} / {{ formatTime(entry.timestamp) }}</small>
            </div>
          </div>
          <div v-if="historyPageCount > 1" class="pagination-row">
            <UiButton :disabled="historyPage <= 1" @click="historyPage -= 1">{{ t("pagination.previous") }}</UiButton>
            <span>{{ t("pagination.pageOf", { page: historyPage, pages: historyPageCount }) }}</span>
            <UiButton :disabled="historyPage >= historyPageCount" @click="historyPage += 1">{{ t("pagination.next") }}</UiButton>
          </div>
          <p v-if="!historyEntries.length" class="empty-text">{{ t("history.empty") }}</p>
        </div>
      </UiCard>
    </div>

    <UiCard :title="t('dashboard.validation')">
      <div class="button-row">
        <UiButton @click="validate"><ShieldCheck />{{ t("dashboard.validateConfig") }}</UiButton>
      </div>
      <template v-if="store.validation">
        <div class="validation-summary">
          <mark :class="validationSummary.valid ? 'good' : 'bad'">{{ validationSummary.valid ? t("validation.valid") : t("validation.invalid") }}</mark>
          <span>{{ t("validation.errorCount", { count: validationSummary.errors }) }}</span>
          <span>{{ t("validation.warningCount", { count: validationSummary.warnings }) }}</span>
        </div>
        <div v-if="validationIssues.length" class="issue-list">
          <div v-for="issue in validationIssues" :key="`${issue.level}:${issue.code}:${issue.field}:${issue.message}`" class="issue-row">
            <mark :class="issue.level === 'error' ? 'bad' : ''">{{ t(`validationLevels.${issue.level}`) }}</mark>
            <div>
              <strong>{{ issue.message }}</strong>
              <small>{{ issue.field || issue.code }} / {{ issue.code }}</small>
            </div>
            <RouterLink v-if="issueTarget(issue)" class="issue-link" :to="issueTarget(issue).to">{{ issueTarget(issue).label }}</RouterLink>
          </div>
        </div>
        <p v-else class="empty-text">{{ t("messages.validationPassed") }}</p>
        <details class="raw-disclosure">
          <summary>{{ t("validation.rawResult") }}</summary>
          <pre class="code-block">{{ JSON.stringify(store.validation, null, 2) }}</pre>
        </details>
      </template>
    </UiCard>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import { Play, RefreshCw, RotateCw, ScrollText, ShieldCheck, Square } from "@lucide/vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { useI18n } from "../composables/useI18n.js";
import { issueSummary, issueTarget as targetForIssue, validationIssuesFromResult } from "../lib/validationIssues.mjs";
import { useManagerStore } from "../stores/manager.js";

const store = useManagerStore();
const { t } = useI18n();
const dashboardLoading = ref(false);
const dashboardError = ref("");
const logsLoading = ref(false);
const logSummaries = ref([]);
const historyPage = ref(1);
const historyPageSize = 6;
const dashboardAgents = computed(() => (store.dashboard?.agents || []).map(normalizeDashboardRow));
const historyEntries = computed(() => store.dashboard?.history || []);
const historyPageCount = computed(() => Math.max(1, Math.ceil(historyEntries.value.length / historyPageSize)));
const pagedHistoryEntries = computed(() => {
  const start = (historyPage.value - 1) * historyPageSize;
  return historyEntries.value.slice(start, start + historyPageSize);
});
const runningAgents = computed(() => dashboardAgents.value.filter((agent) => agent.state === "running" || agent.state === "restarting"));
const attentionAgents = computed(() => dashboardAgents.value.filter((agent) => agent.needs_rebuild || ["error", "unhealthy", "missing"].includes(agent.state)));
const stoppedAgents = computed(() => dashboardAgents.value.filter((agent) => !runningAgents.value.includes(agent) && !attentionAgents.value.includes(agent)));
const runningCount = computed(() => runningAgents.value.length);
const attentionCount = computed(() => attentionAgents.value.length);
const rebuildCount = computed(() => dashboardAgents.value.filter((agent) => agent.needs_rebuild).length);
const validationIssues = computed(() => validationIssuesFromResult(store.validation));
const validationSummary = computed(() => issueSummary(validationIssues.value));
const runtimeGroups = computed(() => [
  { key: "attention", title: t("dashboard.groups.attention"), description: t("dashboard.groups.attentionHelp"), agents: attentionAgents.value },
  { key: "running", title: t("dashboard.groups.running"), description: t("dashboard.groups.runningHelp"), agents: runningAgents.value },
  { key: "stopped", title: t("dashboard.groups.stopped"), description: t("dashboard.groups.stoppedHelp"), agents: stoppedAgents.value }
]);
const emptyDashboardText = computed(() => {
  if (!store.agents.length) return t("dashboard.empty");
  if (store.dashboard?.skipped_uninitialized_agents) return t("dashboard.uninitialized", { count: store.dashboard.skipped_uninitialized_agents });
  return t("dashboard.noRuntimeRows");
});

watch(historyEntries, () => {
  historyPage.value = 1;
});

watch(historyPageCount, (pages) => {
  if (historyPage.value > pages) historyPage.value = pages;
});

function normalizeDashboardRow(row) {
  const agent = row?.agent || row || {};
  const status = row?.status || row || {};
  return {
    ...agent,
    ...status,
    id: agent.id || status.agent_id || status.agent_name || "",
    name: agent.name || status.agent_name || agent.id || "",
    image: status.image || agent.image || "",
    state: status.normalized_state || status.state || "unknown",
    mapped_port: status.mapped_port || "",
    needs_rebuild: Boolean(status.needs_rebuild || status.needs_recreate),
    error: status.error || null
  };
}

function statusClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("running")) return "good";
  if (normalized.includes("error") || normalized.includes("exited") || normalized.includes("unhealthy") || normalized.includes("missing")) return "bad";
  return "";
}

async function refreshDashboard() {
  dashboardLoading.value = true;
  dashboardError.value = "";
  try {
    await store.loadDashboard();
    await loadRecentLogs();
  } catch (error) {
    dashboardError.value = error.message || String(error);
    store.setError(error);
  } finally {
    dashboardLoading.value = false;
  }
}

async function validate() {
  await store.validateConfig();
}

async function control(id, operation) {
  await store.controlAgent(id, operation);
  await refreshDashboard();
}

function issueTarget(issue) {
  return targetForIssue(issue, store.config);
}

async function loadRecentLogs() {
  const targets = [...attentionAgents.value, ...runningAgents.value].slice(0, 4);
  if (!targets.length) {
    logSummaries.value = [];
    return;
  }
  logsLoading.value = true;
  try {
    const rows = await Promise.all(
      targets.map(async (agent) => {
        try {
          const result = await store.getAgentLogs(agent.id, 12);
          const lines = result?.lines || [];
          return { id: agent.id, text: lines.slice(-6).join("\n") || t("dashboard.logsEmpty") };
        } catch (error) {
          return { id: agent.id, text: error.message || String(error) };
        }
      })
    );
    logSummaries.value = rows;
  } finally {
    logsLoading.value = false;
  }
}

function agentRoute(id) {
  return `/agents?agent=${encodeURIComponent(id || "")}`;
}

function formatTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString();
}

onMounted(() => refreshDashboard());
</script>
