import { createI18n } from "./i18n.mjs";
import { loadDefaultPreferences, readPreference, STORAGE_KEYS } from "./preferences.mjs";
import { createThemeController } from "./theme.mjs";
import { loadStatus } from "./status.mjs";

async function main() {
  const defaults = await loadDefaultPreferences();
  const initialLanguage = readPreference(localStorage, STORAGE_KEYS.language, defaults.language);
  const initialTheme = readPreference(localStorage, STORAGE_KEYS.theme, defaults.theme);

  const i18n = createI18n({
    document,
    storage: localStorage,
    initialLocale: initialLanguage
  });
  await i18n.init();

  const languageSwitcher = document.querySelector("#language-switcher");

  const themeController = createThemeController({
    document,
    storage: localStorage,
    initialMode: initialTheme,
    t: i18n.t
  });
  themeController.bindSwitcher(document.querySelector("#theme-switcher"));

  i18n.bindLanguageSwitcher(languageSwitcher, async () => {
    themeController.bindSwitcher(document.querySelector("#theme-switcher"));
    await loadStatus({ document, t: i18n.t });
  });

  await loadStatus({ document, t: i18n.t });
}

main();
