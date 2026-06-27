<template>
  <section class="view-stack">
    <PageHeader title="Skills" description="Manage runtime skill settings and bundle metadata.">
      <UiButton v-if="selectedTab === 'runtime'" variant="primary" @click="save"><Save />Save settings</UiButton>
    </PageHeader>

    <div class="segment-tabs page-tabs">
      <button v-for="tab in tabs" :key="tab.id" :class="{ active: selectedTab === tab.id }" @click="selectedTab = tab.id">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="selectedTab === 'runtime'" class="tab-panel">
      <UiCard title="Runtime settings" description="Global runtime behavior for skill loading and Open Skills.">
        <div class="form-grid">
          <label class="check-row form-field--wide">
            <input v-model="skills.allow_scripts" type="checkbox" />
            <span>Allow skill scripts</span>
          </label>
          <label class="check-row form-field--wide">
            <input v-model="skills.open_skills_enabled" type="checkbox" />
            <span>Open Skills enabled</span>
          </label>
          <FormField v-model="skills.registry_url" label="Registry URL" wide />
          <FormField v-model="skills.prompt_injection_mode" label="Prompt injection mode" />
        </div>
      </UiCard>
    </div>

    <div v-else-if="selectedTab === 'bundles'" class="tab-panel">
      <UiCard title="Bundles">
        <template #actions>
          <UiButton @click="newBundle"><Plus />Bundle</UiButton>
        </template>
        <div class="item-list">
          <button v-for="bundle in bundles" :key="bundle.id" :class="{ active: selectedBundleId === bundle.id }" @click="selectBundle(bundle)">
            <strong>{{ bundle.id }}</strong>
            <span>{{ bundle.directory }}</span>
          </button>
        </div>
        <form v-if="bundleDraft" class="form-grid bundle-form" @submit.prevent="saveBundle">
          <FormField v-model="bundleDraft.id" label="ID" />
          <FormField v-model="bundleDraft.directory" label="Directory" />
          <FormField v-model="bundleInclude" label="Include" textarea wide />
          <FormField v-model="bundleExclude" label="Exclude" textarea wide />
          <div class="button-row form-field--wide">
            <UiButton variant="primary" type="submit"><Save />Save bundle</UiButton>
            <UiButton v-if="!bundleDraft._draft" variant="danger" @click="deleteBundle"><Trash2 />Delete</UiButton>
          </div>
        </form>
      </UiCard>
    </div>

    <div v-else-if="selectedTab === 'library'" class="tab-panel">
      <UiCard title="Skill library" description="Edit canonical SKILL.md content in the selected bundle.">
        <template #actions>
          <UiButton :disabled="!selectedBundleId" @click="newSkill"><Plus />Skill</UiButton>
        </template>
        <div class="skill-library-layout">
          <div class="item-list">
            <button v-for="skill in skillsList" :key="skill.name" :class="{ active: selectedSkillName === skill.name }" @click="selectSkill(skill.name)">
              <strong>{{ skill.name }}</strong>
              <span>{{ skill.description || "No description" }}</span>
            </button>
            <p v-if="!skillsList.length" class="empty-text">No skills loaded for this bundle.</p>
          </div>
          <form v-if="skillDraft" class="form-grid" @submit.prevent="saveSkillDoc">
            <FormField v-model="skillDraft.name" label="Name" />
            <FormField v-model="skillDraft.description" label="Description" />
            <FormField v-model="skillDraft.category" label="Category" />
            <FormField v-model="skillTags" label="Tags" />
            <FormField v-model="skillDraft.content" label="SKILL.md body" textarea wide />
            <div class="button-row form-field--wide">
              <UiButton variant="primary" type="submit"><Save />Save skill</UiButton>
              <UiButton v-if="!skillDraft._draft" variant="danger" @click="deleteSkillDoc"><Trash2 />Archive</UiButton>
            </div>
          </form>
          <p v-else class="empty-text">Select or create a skill.</p>
        </div>
      </UiCard>
    </div>

    <div v-else class="tab-panel">
      <UiCard title="Support files" description="References, scripts, and assets for the selected skill.">
        <p class="empty-text">Support file editing is next in this Vue migration. Select Library for SKILL.md editing for now.</p>
      </UiCard>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { Plus, Save, Trash2 } from "@lucide/vue";
import FormField from "../components/FormField.vue";
import PageHeader from "../components/PageHeader.vue";
import UiButton from "../components/UiButton.vue";
import UiCard from "../components/UiCard.vue";
import { clone } from "../lib/api.js";
import { useManagerStore } from "../stores/manager.js";

const store = useManagerStore();
const skills = reactive({});
const bundles = computed(() => store.skillBundles);
const selectedTab = ref("runtime");
const tabs = [
  { id: "runtime", label: "Runtime settings" },
  { id: "bundles", label: "Bundles" },
  { id: "library", label: "Skill library" },
  { id: "support", label: "Support files" }
];
const selectedBundleId = ref("");
const bundleDraft = ref(null);
const skillsList = ref([]);
const selectedSkillName = ref("");
const skillDraft = ref(null);

const bundleInclude = computed({
  get: () => (bundleDraft.value?.include || []).join("\n"),
  set: (value) => (bundleDraft.value.include = lines(value))
});

const bundleExclude = computed({
  get: () => (bundleDraft.value?.exclude || []).join("\n"),
  set: (value) => (bundleDraft.value.exclude = lines(value))
});

const skillTags = computed({
  get: () => (skillDraft.value?.tags || []).join(", "),
  set: (value) => (skillDraft.value.tags = String(value || "").split(",").map((tag) => tag.trim()).filter(Boolean))
});

watch(
  () => store.skillsConfig,
  (value) => Object.assign(skills, clone(value || {})),
  { immediate: true, deep: true }
);

async function save() {
  const next = clone(store.config);
  next.skills = clone(skills);
  await store.saveConfig(next);
}

watch(
  bundles,
  (rows) => {
    if (!bundleDraft.value && rows.length) selectBundle(rows[0]);
  },
  { immediate: true }
);

function lines(value) {
  return String(value || "").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function selectBundle(bundle) {
  selectedBundleId.value = bundle.id;
  bundleDraft.value = clone(bundle);
  selectedSkillName.value = "";
  skillDraft.value = null;
  loadSkills();
}

function newBundle() {
  const next = bundles.value.length + 1;
  selectedBundleId.value = "";
  bundleDraft.value = { id: `bundle-${next}`, directory: `shared/skills/bundle-${next}`, include: [], exclude: [], _draft: true };
}

async function saveBundle() {
  const payload = clone(bundleDraft.value);
  delete payload._draft;
  await store.saveSkillBundle(payload);
  selectedBundleId.value = payload.id;
  bundleDraft.value = payload;
}

async function deleteBundle() {
  if (bundleDraft.value && confirm(`Delete skill bundle ${bundleDraft.value.id}?`)) {
    await store.deleteSkillBundle(bundleDraft.value.id);
    bundleDraft.value = null;
    selectedBundleId.value = "";
  }
}

async function loadSkills() {
  if (!selectedBundleId.value) return;
  const result = await store.listSkills(selectedBundleId.value);
  skillsList.value = result.skills || [];
}

async function selectSkill(name) {
  selectedSkillName.value = name;
  const doc = await store.readSkill(selectedBundleId.value, name);
  skillDraft.value = {
    name: doc.name || name,
    description: doc.description || "",
    category: doc.category || "",
    tags: doc.tags || [],
    content: doc.content || "",
    files: doc.files || []
  };
}

function newSkill() {
  selectedSkillName.value = "";
  skillDraft.value = {
    name: "new-skill",
    description: "",
    category: "",
    tags: [],
    content: "# new-skill\n\nDescribe when and how to use this skill.\n",
    _draft: true
  };
}

async function saveSkillDoc() {
  const payload = clone(skillDraft.value);
  delete payload._draft;
  if (skillDraft.value._draft) {
    await store.createSkill(selectedBundleId.value, payload);
  } else {
    await store.saveSkill(selectedBundleId.value, selectedSkillName.value, payload);
  }
  await loadSkills();
  selectedSkillName.value = payload.name;
  skillDraft.value = payload;
}

async function deleteSkillDoc() {
  if (!selectedSkillName.value || !confirm(`Archive skill ${selectedSkillName.value}?`)) return;
  await store.deleteSkill(selectedBundleId.value, selectedSkillName.value);
  selectedSkillName.value = "";
  skillDraft.value = null;
  await loadSkills();
}
</script>
