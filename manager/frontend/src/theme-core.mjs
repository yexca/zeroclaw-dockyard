export const THEME_MODES = ["light", "dark", "system"];
export const DEFAULT_THEME_MODE = "system";

export function normalizeThemeMode(mode) {
  return THEME_MODES.includes(mode) ? mode : DEFAULT_THEME_MODE;
}

export function resolveTheme(mode, matchMedia = globalThis.matchMedia) {
  const normalized = normalizeThemeMode(mode);
  if (normalized !== "system") {
    return normalized;
  }

  return matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyThemeMode(mode, options = {}) {
  const documentElement = options.documentElement || globalThis.document?.documentElement;
  const matchMedia = options.matchMedia || globalThis.matchMedia;
  const normalized = normalizeThemeMode(mode);
  const resolved = resolveTheme(normalized, matchMedia);

  if (documentElement) {
    documentElement.dataset.themeMode = normalized;
    documentElement.dataset.theme = resolved;
    documentElement.style.colorScheme = resolved;
  }

  return { mode: normalized, resolved };
}
