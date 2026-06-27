<template>
  <section class="view-stack">
    <PageHeader :title="title" :description="description">
      <UiButton variant="primary" @click="createProfile"><Plus />{{ t("profiles.newProfile") }}</UiButton>
    </PageHeader>

    <div class="editor-layout">
      <UiCard :title="t('profiles.title')" :description="t('profiles.listHelp')">
        <div class="item-list">
          <button
            v-for="profile in profiles"
            :key="itemId(profile)"
            class="profile-list-item"
            :class="{ active: selectedId === itemId(profile) }"
            @click="selectProfile(profile)"
          >
            <span>
              <strong>{{ itemId(profile) }}</strong>
              <small>{{ profile.model || profile.homeserver || profile.url || profile.provider_family || t("profiles.profile") }}</small>
            </span>
            <mark :class="profileUsage(itemId(profile)).length ? 'good' : ''">
              {{ profileUsage(itemId(profile)).length ? t("profiles.usedCount", { count: profileUsage(itemId(profile)).length }) : t("common.unused") }}
            </mark>
          </button>
          <p v-if="!profiles.length" class="empty-text">{{ t("profiles.emptyList") }}</p>
        </div>
      </UiCard>

      <UiCard :title="t('profiles.details')" :description="t('profiles.detailsHelp')">
        <section v-if="draft" class="profile-usage-panel">
          <div>
            <strong>{{ t("profiles.usedBy") }}</strong>
            <span>{{ currentUsage.length ? t("profiles.agentCount", { count: currentUsage.length }) : t("profiles.noUsage") }}</span>
          </div>
          <div v-if="currentUsage.length" class="file-chip-grid">
            <button v-for="usage in currentUsage" :key="`${usage.id}-${usage.field}`" class="file-chip profile-usage-chip" type="button">
              {{ usage.id }} / {{ usage.field }}
            </button>
          </div>
        </section>
        <form v-if="draft" class="form-grid" @submit.prevent="save">
          <FormField v-model="draft.id" :label="t('fields.id')" />
          <template v-if="kind === 'llm' || kind === 'vision'">
            <FormField v-model="draft.provider_family" :label="t('fields.provider')" />
            <FormField v-model="draft.provider_alias" :label="t('fields.providerAlias')" />
            <FormField v-model="draft.model" :label="t('fields.model')" />
            <FormField v-model="draft.base_url" :label="t('fields.baseUrl')" />
            <FormField v-model="draft.api_key" :label="t('fields.apiKey')" type="password" />
            <FormField v-model="draft.wire_api" :label="t('fields.wireApi')" :options="wireOptions" />
            <FormField v-model="draft.timeout_secs" :label="t('fields.timeout')" type="number" />
            <template v-if="kind === 'vision'">
              <details class="advanced-disclosure form-field--wide">
                <summary>{{ t("fields.multimodalLimits") }}</summary>
                <div class="form-grid nested-form">
                  <FormField v-model="draft.max_images" :label="t('fields.maxImages')" type="number" />
                  <FormField v-model="draft.max_image_size_mb" :label="t('fields.maxImageSizeMb')" type="number" />
                  <FormField v-model="draft.max_image_turns" :label="t('fields.maxImageTurns')" type="number" />
                  <label class="check-row form-field--wide">
                    <input v-model="draft.allow_remote_fetch" type="checkbox" />
                    <span>{{ t("fields.allowRemoteFetch") }}</span>
                  </label>
                </div>
              </details>
            </template>
            <template v-else>
              <details class="advanced-disclosure form-field--wide">
                <summary>{{ t("profiles.llmAdvanced") }}</summary>
                <div class="form-grid nested-form">
                  <FormField v-model="draft.temperature" :label="t('fields.temperature')" type="number" />
                  <FormField v-model="draft.max_tokens" :label="t('fields.maxTokens')" type="number" />
                  <FormField v-model="fallbackModels" :label="t('fields.fallbackModels')" textarea wide />
                  <FormField v-model="extraHeaders" :label="t('fields.extraHeaders')" textarea wide />
                  <FormField v-model="providerExtra" :label="t('fields.providerExtra')" textarea wide />
                  <FormField v-model="pricing" :label="t('fields.pricing')" textarea wide />
                  <label class="check-row form-field--wide">
                    <input v-model="draft.requires_openai_auth" type="checkbox" />
                    <span>{{ t("fields.requiresOpenaiAuth") }}</span>
                  </label>
                  <label class="check-row form-field--wide">
                    <input v-model="draft.merge_system_into_user" type="checkbox" />
                    <span>{{ t("fields.mergeSystemIntoUser") }}</span>
                  </label>
                </div>
              </details>
            </template>
          </template>
          <template v-else-if="kind === 'matrix'">
            <FormField v-model="draft.homeserver" :label="t('fields.homeserver')" />
            <FormField v-model="draft.user_id" :label="t('fields.matrixUser')" />
            <FormField v-model="draft.device_id" :label="t('fields.deviceId')" />
            <FormField v-model="draft.password" :label="t('fields.password')" type="password" />
            <FormField v-model="draft.recovery_key" :label="t('fields.recoveryKey')" type="password" />
            <FormField v-model="allowedRooms" :label="t('fields.allowedRooms')" textarea wide />
            <details class="advanced-disclosure form-field--wide" open>
              <summary>{{ t("fields.matrixBehavior") }}</summary>
              <div class="form-grid nested-form">
                <label class="check-row form-field--wide"><input v-model="draft.mention_only" type="checkbox" /><span>{{ t("fields.mentionOnly") }}</span></label>
                <label class="check-row form-field--wide"><input v-model="draft.reply_in_thread" type="checkbox" /><span>{{ t("fields.replyInThread") }}</span></label>
                <label class="check-row form-field--wide"><input v-model="draft.ack_reactions" type="checkbox" /><span>{{ t("fields.ackReactions") }}</span></label>
                <label class="check-row form-field--wide"><input v-model="draft.interrupt_on_new_message" type="checkbox" /><span>{{ t("fields.interruptOnNewMessage") }}</span></label>
                <FormField v-model="draft.stream_mode" :label="t('fields.streamMode')" :options="streamOptions" />
                <FormField v-model="draft.multi_message_delay_ms" :label="t('fields.multiMessageDelayMs')" type="number" />
                <FormField v-model="draft.channel_debounce_ms" :label="t('fields.channelDebounceMs')" type="number" />
                <FormField v-model="draft.access_token" :label="t('fields.accessToken')" type="password" wide />
              </div>
            </details>
            <details class="advanced-disclosure form-field--wide">
              <summary>{{ t("profiles.matrixAdvanced") }}</summary>
              <div class="form-grid nested-form">
                <FormField v-model="draft.draft_update_interval_ms" :label="t('fields.draftUpdateIntervalMs')" type="number" />
                <FormField v-model="draft.approval_timeout_secs" :label="t('fields.approvalTimeoutSecs')" type="number" />
                <FormField v-model="excludedTools" :label="t('fields.excludedTools')" textarea wide />
                <FormField v-model="draft.reply_min_interval_secs" :label="t('fields.replyMinIntervalSecs')" type="number" />
                <FormField v-model="draft.reply_queue_depth_max" :label="t('fields.replyQueueDepthMax')" type="number" />
                <FormField v-model="draft.host_ip" :label="t('fields.hostIp')" />
              </div>
            </details>
          </template>
          <template v-else>
            <FormField v-model="draft.url" :label="t('fields.url')" />
            <FormField v-model="draft.command" :label="t('fields.command')" />
          </template>
          <div class="form-field form-field--wide">
            <span>{{ t("profiles.advancedJson") }}</span>
            <small>{{ t("profiles.advancedJsonHelp") }}</small>
            <JsonEditor v-model="draft" />
          </div>
          <div class="button-row form-field--wide">
            <UiButton variant="primary" type="submit"><Save />{{ t("actions.save") }}</UiButton>
            <UiButton v-if="kind === 'llm'" type="button" @click="testProfile"><PlugZap />{{ t("actions.testConnection") }}</UiButton>
            <UiButton v-if="!draft._draft" variant="danger" @click="remove"><Trash2 />{{ t("actions.delete") }}</UiButton>
          </div>
        </form>
        <p v-else class="empty-text">{{ t("profiles.empty") }}</p>
      </UiCard>
    </div>

    <div v-if="testResult" class="split-panels">
      <UiCard v-if="testResult" :title="t('profiles.testResult')">
        <pre class="code-block">{{ JSON.stringify(testResult, null, 2) }}</pre>
      </UiCard>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { PlugZap, Plus, Save, Trash2 } from "@lucide/vue";
import FormField from "../components/FormField.vue";
import JsonEditor from "../components/JsonEditor.vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { useDialog } from "../composables/useDialog.js";
import { useI18n } from "../composables/useI18n.js";
import { clone, itemId } from "../lib/api.js";
import { useManagerStore } from "../stores/manager.js";

const route = useRoute();
const store = useManagerStore();
const { t } = useI18n();
const dialog = useDialog();
const selectedId = ref("");
const draft = ref(null);
const testResult = ref(null);
const wireOptions = [
  { label: t("profiles.wire.chatCompletions"), value: "chat_completions" },
  { label: t("profiles.wire.responses"), value: "responses" }
];
const streamOptions = [
  { label: t("profiles.stream.multiMessage"), value: "multi_message" },
  { label: t("profiles.stream.edit"), value: "edit" },
  { label: t("common.disabled"), value: "disabled" }
];

const kind = computed(() => route.params.kind || "llm");
const profiles = computed(() => store.profiles[kind.value] || []);
const title = computed(() => t(`${kind.value}.title`));
const description = computed(() => {
  if (kind.value === "matrix") return t("matrix.subtitle");
  if (kind.value === "vision") return t("vision.subtitle");
  if (kind.value === "mcp") return t("mcp.subtitle");
  return t("llm.subtitle");
});

watch(kind, () => {
  selectedId.value = "";
  draft.value = null;
  testResult.value = null;
});

watch(
  profiles,
  (items) => {
    if (!draft.value && items.length) selectProfile(items[0]);
  },
  { immediate: true }
);

function selectProfile(profile) {
  selectedId.value = itemId(profile);
  draft.value = clone(profile);
  testResult.value = null;
}

function createProfile() {
  draft.value = { ...store.newProfile(kind.value), _draft: true };
  selectedId.value = "";
  testResult.value = null;
}

async function save() {
  const payload = clone(draft.value);
  delete payload._draft;
  await store.saveProfile(kind.value, payload);
  selectedId.value = itemId(payload);
  draft.value = payload;
}

async function remove() {
  if (!draft.value?._draft && await dialog.confirm(t("confirm.deleteProfileNamed", { kind: t(`${kind.value}.title`), id: itemId(draft.value) }))) {
    await store.deleteProfile(kind.value, itemId(draft.value));
    draft.value = null;
    selectedId.value = "";
  }
}

function lines(value) {
  return String(value || "").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function parseJsonField(value, fallback) {
  try {
    return JSON.parse(value || "null") ?? fallback;
  } catch (_error) {
    return fallback;
  }
}

function jsonComputed(key, fallback) {
  return computed({
    get: () => JSON.stringify(draft.value?.[key] ?? fallback, null, 2),
    set: (value) => (draft.value[key] = parseJsonField(value, fallback))
  });
}

const fallbackModels = computed({
  get: () => (draft.value?.fallback_models || draft.value?.fallback || []).join("\n"),
  set: (value) => (draft.value.fallback_models = lines(value))
});
const extraHeaders = jsonComputed("extra_headers", {});
const providerExtra = jsonComputed("provider_extra", {});
const pricing = jsonComputed("pricing", {});
const allowedRooms = computed({
  get: () => (draft.value?.allowed_rooms || []).join("\n"),
  set: (value) => (draft.value.allowed_rooms = lines(value))
});
const excludedTools = computed({
  get: () => (draft.value?.excluded_tools || []).join("\n"),
  set: (value) => (draft.value.excluded_tools = lines(value))
});

async function testProfile() {
  const payload = clone(draft.value);
  delete payload._draft;
  testResult.value = await store.testLlmProfile(payload);
}

function profileUsage(profileId) {
  const field = `${kind.value}_profile`;
  return store.agents
    .filter((agent) => agent[field] === profileId)
    .map((agent) => ({ id: itemId(agent), field }));
}

const currentUsage = computed(() => (draft.value ? profileUsage(itemId(draft.value)) : []));
</script>
