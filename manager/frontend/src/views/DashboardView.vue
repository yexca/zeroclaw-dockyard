<template>
  <section class="view-stack">
    <PageHeader :title="t('dashboard.title')" :description="t('dashboard.subtitle')">
      <UiButton variant="primary" @click="store.loadDashboard"><RefreshCw />{{ t("actions.refresh") }}</UiButton>
    </PageHeader>

    <div class="metric-grid">
      <UiCard :title="t('dashboard.metrics.configuredAgents')"><strong class="metric-value">{{ store.agents.length }}</strong></UiCard>
      <UiCard :title="t('dashboard.metrics.runningAgents')"><strong class="metric-value">{{ runningCount }}</strong></UiCard>
      <UiCard :title="t('dashboard.metrics.profiles')"><strong class="metric-value">{{ profileCount }}</strong></UiCard>
      <UiCard :title="t('dashboard.metrics.skillBundles')"><strong class="metric-value">{{ store.skillBundles.length }}</strong></UiCard>
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
          <span><strong>{{ agent.id || agent.name }}</strong></span>
          <span><mark :class="statusClass(agent.state || agent.status)">{{ agent.state || agent.status || t("common.unknown") }}</mark></span>
          <span>{{ agent.image || "-" }}</span>
          <span class="inline-actions">
            <UiButton icon :aria-label="t('actions.start')" @click="store.controlAgent(agent.id || agent.name, 'start')"><Play /></UiButton>
            <UiButton icon :aria-label="t('actions.restart')" @click="store.controlAgent(agent.id || agent.name, 'restart')"><RotateCw /></UiButton>
          </span>
        </div>
        <p v-if="!dashboardAgents.length" class="empty-text">{{ t("dashboard.noRuntimeRows") }}</p>
      </div>
    </UiCard>

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
              <small>{{ issue.field || issue.code }} · {{ issue.code }}</small>
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
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { Play, RefreshCw, RotateCw, ShieldCheck } from "@lucide/vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { useI18n } from "../composables/useI18n.js";
import { issueSummary, issueTarget as targetForIssue, validationIssuesFromResult } from "../lib/validationIssues.mjs";
import { useManagerStore } from "../stores/manager.js";

const store = useManagerStore();
const { t } = useI18n();
const dashboardAgents = computed(() => store.dashboard?.agents || []);
const runningCount = computed(() => dashboardAgents.value.filter((agent) => String(agent.state || agent.status).includes("running")).length);
const profileCount = computed(() => Object.values(store.profiles).reduce((total, rows) => total + rows.length, 0));
const validationIssues = computed(() => validationIssuesFromResult(store.validation));
const validationSummary = computed(() => issueSummary(validationIssues.value));

function statusClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("running")) return "good";
  if (normalized.includes("error") || normalized.includes("exited")) return "bad";
  return "";
}

async function validate() {
  await store.validateConfig();
}

function issueTarget(issue) {
  return targetForIssue(issue, store.config);
}

onMounted(() => store.loadDashboard().catch((error) => store.setError(error)));
</script>
