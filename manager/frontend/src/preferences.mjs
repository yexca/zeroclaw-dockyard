export const STORAGE_KEYS = {
  language: "zeroclaw.webui.language",
  theme: "zeroclaw.webui.theme"
};

export const DEFAULT_PREFERENCES = {
  language: "en",
  theme: "system"
};

export function readPreference(storage, key, fallback) {
  try {
    return storage?.getItem(key) || fallback;
  } catch (_error) {
    return fallback;
  }
}

export function writePreference(storage, key, value) {
  try {
    storage?.setItem(key, value);
  } catch (_error) {
    // Preference persistence should not block the local control surface.
  }
}

export async function loadDefaultPreferences(fetcher = fetch) {
  try {
    const response = await fetcher("/api/webui/defaults");
    if (!response.ok) {
      return DEFAULT_PREFERENCES;
    }

    const data = await response.json();
    return {
      language: data.default_language || DEFAULT_PREFERENCES.language,
      theme: data.default_theme || DEFAULT_PREFERENCES.theme
    };
  } catch (_error) {
    return DEFAULT_PREFERENCES;
  }
}
