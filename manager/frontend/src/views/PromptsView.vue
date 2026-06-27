<template>
  <section class="view-stack">
    <PageHeader title="Prompt Templates" description="Edit reusable workspace prompt files as structured templates.">
      <UiButton variant="primary" @click="createTemplate"><Plus />New template</UiButton>
    </PageHeader>

    <div class="editor-layout">
      <UiCard title="Templates">
        <div class="item-list">
          <button v-for="template in store.templates" :key="itemId(template)" :class="{ active: selectedId === itemId(template) }" @click="selectTemplate(template)">
            <strong>{{ itemId(template) }}</strong>
            <span>{{ Object.keys(template.files || {}).length }} files</span>
          </button>
          <p v-if="!store.templates.length" class="empty-text">No templates yet.</p>
        </div>
      </UiCard>

      <UiCard title="Template details" description="Use JSON to preserve arbitrary prompt file mappings.">
        <form v-if="draft" class="form-grid" @submit.prevent="save">
          <FormField v-model="draft.id" label="Template ID" />
          <FormField v-model="draft.description" label="Description" wide />
          <div class="form-field form-field--wide">
            <span>Files</span>
            <div class="file-tabs">
              <button v-for="file in fileNames" :key="file" :class="{ active: selectedFile === file }" type="button" @click="selectedFile = file">
                {{ file }}
              </button>
              <button type="button" @click="addFile"><Plus />File</button>
            </div>
            <textarea v-if="selectedFile" v-model="draft.files[selectedFile]" class="template-editor-text" spellcheck="false" />
          </div>
          <div class="form-field form-field--wide">
            <details class="advanced-disclosure">
              <summary>Advanced JSON</summary>
              <JsonEditor v-model="draft" />
            </details>
          </div>
          <div class="button-row form-field--wide">
            <UiButton variant="primary" type="submit"><Save />Save</UiButton>
            <UiButton type="button" @click="aiFillOpen = !aiFillOpen"><Sparkles />AI fill</UiButton>
          </div>
        </form>
        <p v-else class="empty-text">Select or create a template.</p>
      </UiCard>
    </div>

    <UiCard v-if="draft && aiFillOpen" title="AI fill" description="Generate selected prompt files into this browser-side draft. Review before saving.">
      <form class="form-grid" @submit.prevent="runAiFill">
        <FormField v-model="aiFill.llm_profile" label="LLM profile" :options="llmOptions" />
        <FormField v-model="aiFill.description" label="Agent description" wide />
        <FormField v-model="aiFill.instruction" label="Generation instruction" textarea wide />
        <div class="form-field form-field--wide">
          <span>Target files</span>
          <div class="file-chip-grid">
            <label v-for="file in fileNames" :key="file" class="check-row file-chip">
              <input v-model="aiFill.files" :value="file" type="checkbox" />
              <span>{{ file }}</span>
            </label>
          </div>
        </div>
        <div class="form-field form-field--wide">
          <span>Reference files</span>
          <div class="file-chip-grid">
            <label v-for="file in fileNames" :key="file" class="check-row file-chip">
              <input v-model="aiFill.reference_files" :value="file" type="checkbox" />
              <span>{{ file }}</span>
            </label>
          </div>
        </div>
        <div class="button-row form-field--wide">
          <UiButton variant="primary" type="submit"><Sparkles />Generate</UiButton>
          <UiButton type="button" @click="aiFillOpen = false">Close</UiButton>
        </div>
      </form>
    </UiCard>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { Plus, Save, Sparkles } from "@lucide/vue";
import FormField from "../components/FormField.vue";
import JsonEditor from "../components/JsonEditor.vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { clone, itemId } from "../lib/api.js";
import { useManagerStore } from "../stores/manager.js";

const store = useManagerStore();
const selectedId = ref("");
const draft = ref(null);
const selectedFile = ref("");
const aiFillOpen = ref(false);
const aiFill = ref({
  llm_profile: "",
  instruction: "Generate concise, practical Markdown for the selected ZeroClaw prompt files. Preserve file roles and placeholders where useful. Return only the requested files.",
  description: "",
  files: [],
  reference_files: []
});

const fileNames = computed(() => Object.keys(draft.value?.files || {}));
const llmOptions = computed(() => store.profiles.llm.map((profile) => ({ label: itemId(profile), value: itemId(profile) })));

watch(
  () => store.templates,
  (templates) => {
    if (!draft.value && templates.length) selectTemplate(templates[0]);
  },
  { immediate: true }
);

function selectTemplate(template) {
  selectedId.value = itemId(template);
  draft.value = clone(template);
  selectedFile.value = Object.keys(draft.value.files || {})[0] || "";
  resetAiFill();
}

function createTemplate() {
  const next = store.templates.length + 1;
  draft.value = { id: `template-${next}`, description: "", files: { "AGENTS.md": "" }, _draft: true };
  selectedId.value = "";
  selectedFile.value = "AGENTS.md";
  resetAiFill();
}

async function save() {
  const payload = clone(draft.value);
  payload.files = payload.files || {};
  delete payload._draft;
  await store.saveTemplate(payload);
  selectedId.value = payload.id;
  draft.value = payload;
}

function addFile() {
  const name = prompt("File name", "USER.md");
  if (!name) return;
  if (!draft.value.files) draft.value.files = {};
  if (!(name in draft.value.files)) draft.value.files[name] = "";
  selectedFile.value = name;
  if (!aiFill.value.files.includes(name)) aiFill.value.files.push(name);
}

function resetAiFill() {
  const files = Object.keys(draft.value?.files || {});
  aiFill.value = {
    llm_profile: store.profiles.llm[0] ? itemId(store.profiles.llm[0]) : "",
    instruction: aiFill.value.instruction,
    description: draft.value?.description || "",
    files: files.slice(0, Math.min(files.length, 3)),
    reference_files: []
  };
}

async function runAiFill() {
  const currentFiles = Object.fromEntries(
    [...new Set([...aiFill.value.files, ...aiFill.value.reference_files])].map((file) => [file, draft.value.files?.[file] || ""])
  );
  const result = await store.aiFillTemplate({
    llm_profile: aiFill.value.llm_profile,
    instruction: aiFill.value.instruction,
    description: aiFill.value.description,
    files: aiFill.value.files,
    reference_files: aiFill.value.reference_files,
    current_files: currentFiles
  });
  for (const [file, content] of Object.entries(result.files || {})) {
    draft.value.files[file] = content;
    selectedFile.value = file;
  }
}
</script>
