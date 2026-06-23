import { STORAGE_KEYS, writePreference } from "./preferences.mjs";

export const SUPPORTED_LOCALES = ["en", "zh-CN"];
export const DEFAULT_LOCALE = "en";

export function normalizeLocale(locale) {
  if (SUPPORTED_LOCALES.includes(locale)) {
    return locale;
  }

  const language = locale?.split("-")[0];
  return SUPPORTED_LOCALES.find((supported) => supported.split("-")[0] === language) || DEFAULT_LOCALE;
}

export function getMessage(messages, key) {
  return key.split(".").reduce((current, part) => current?.[part], messages);
}

export async function loadLocale(locale, fetcher = fetch) {
  const normalized = normalizeLocale(locale);
  const response = await fetcher(`/src/locales/${normalized}.json`);
  if (!response.ok) {
    throw new Error(`Unable to load locale: ${normalized}`);
  }
  return { locale: normalized, messages: await response.json() };
}

export function createI18n({ document, storage, initialLocale, fetcher = fetch }) {
  let locale = normalizeLocale(initialLocale);
  let messages = {};

  function t(key) {
    return getMessage(messages, key) || key;
  }

  function translateDocument() {
    document.documentElement.lang = locale;
    document.querySelectorAll("[data-i18n]").forEach((element) => {
      element.textContent = t(element.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-title]").forEach((element) => {
      element.title = t(element.dataset.i18nTitle);
    });
    document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
      element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
    });
  }

  async function setLocale(nextLocale) {
    const loaded = await loadLocale(nextLocale, fetcher);
    locale = loaded.locale;
    messages = loaded.messages;
    writePreference(storage, STORAGE_KEYS.language, locale);
    translateDocument();
  }

  async function init() {
    await setLocale(locale);
  }

  function bindLanguageSwitcher(select, onLocaleChanged) {
    select.innerHTML = SUPPORTED_LOCALES.map(
      (supportedLocale) =>
        `<option value="${supportedLocale}">${t(`preferences.languages.${supportedLocale}`)}</option>`
    ).join("");
    select.value = locale;
    select.onchange = async () => {
      await setLocale(select.value);
      bindLanguageSwitcher(select, onLocaleChanged);
      await onLocaleChanged?.();
    };
  }

  return {
    get locale() {
      return locale;
    },
    init,
    setLocale,
    t,
    translateDocument,
    bindLanguageSwitcher
  };
}
