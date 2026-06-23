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

console.log("ui foundation tests passed");
