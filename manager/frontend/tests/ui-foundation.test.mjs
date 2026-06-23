import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";

const testDir = dirname(fileURLToPath(import.meta.url));
const frontendDir = resolve(testDir, "..");

async function readJson(relativePath) {
  return JSON.parse(await readFile(resolve(frontendDir, relativePath), "utf8"));
}

function flattenKeys(value, prefix = "") {
  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    if (child && typeof child === "object" && !Array.isArray(child)) {
      return flattenKeys(child, path);
    }
    return [path];
  });
}

const en = await readJson("src/locales/en.json");
const zhCN = await readJson("src/locales/zh-CN.json");

assert.deepEqual(flattenKeys(zhCN).sort(), flattenKeys(en).sort(), "Locale files must expose the same keys");

const themeCore = await import(pathToFileURL(resolve(frontendDir, "src/theme-core.mjs")));
const i18n = await import(pathToFileURL(resolve(frontendDir, "src/i18n.mjs")));
const preferences = await import(pathToFileURL(resolve(frontendDir, "src/preferences.mjs")));
const documentElement = { dataset: {}, style: {} };
const darkMedia = (query) => ({ matches: query === "(prefers-color-scheme: dark)" });

assert.deepEqual(
  themeCore.applyThemeMode("system", { documentElement, matchMedia: darkMedia }),
  { mode: "system", resolved: "dark" },
  "System mode should resolve from prefers-color-scheme"
);
assert.equal(documentElement.dataset.themeMode, "system");
assert.equal(documentElement.dataset.theme, "dark");

themeCore.applyThemeMode("light", { documentElement, matchMedia: darkMedia });
assert.equal(documentElement.dataset.theme, "light", "Explicit light mode should override system");

assert.equal(i18n.normalizeLocale("zh-Hans-CN"), "zh-CN", "Chinese locale should normalize to zh-CN");
assert.equal(i18n.normalizeLocale("fr-FR"), "en", "Unsupported locales should fall back to English");
assert.equal(themeCore.normalizeThemeMode("neon"), "system", "Unknown theme mode should fall back to system");

const defaults = await preferences.loadDefaultPreferences(async () => ({
  ok: true,
  async json() {
    return { data: { default_language: "zh-CN", default_theme: "dark" } };
  }
}));
assert.deepEqual(defaults, { language: "zh-CN", theme: "dark" }, "WebUI defaults should load from API payload");

console.log("ui foundation tests passed");
