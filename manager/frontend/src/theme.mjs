import { STORAGE_KEYS, writePreference } from "./preferences.mjs";
import { THEME_MODES, applyThemeMode, normalizeThemeMode } from "./theme-core.mjs";

export function createThemeController({ document, storage, initialMode, t }) {
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  let mode = normalizeThemeMode(initialMode);

  function apply() {
    return applyThemeMode(mode, {
      documentElement: document.documentElement,
      matchMedia: window.matchMedia.bind(window)
    });
  }

  function setTheme(nextMode) {
    mode = normalizeThemeMode(nextMode);
    writePreference(storage, STORAGE_KEYS.theme, mode);
    apply();
  }

  function bindSwitcher(select) {
    select.innerHTML = THEME_MODES.map(
      (themeMode) => `<option value="${themeMode}">${t(`preferences.themes.${themeMode}`)}</option>`
    ).join("");
    select.value = mode;
    select.onchange = () => setTheme(select.value);
  }

  media.addEventListener?.("change", () => {
    if (mode === "system") {
      apply();
    }
  });

  apply();

  return {
    get mode() {
      return mode;
    },
    apply,
    setTheme,
    bindSwitcher
  };
}
