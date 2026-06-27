import { ref } from "vue";
import enMessages from "../locales/en.json";
import zhCNMessages from "../locales/zh-CN.json";
import { DEFAULT_LOCALE, SUPPORTED_LOCALES, getMessage, normalizeLocale } from "../i18n.mjs";
import { readPreference, STORAGE_KEYS, writePreference } from "../preferences.mjs";

const catalogs = {
  en: enMessages,
  "zh-CN": zhCNMessages
};

const locale = ref(
  normalizeLocale(readPreference(globalThis.localStorage, STORAGE_KEYS.language, DEFAULT_LOCALE))
);

function messagesFor(nextLocale) {
  return catalogs[normalizeLocale(nextLocale)] || catalogs[DEFAULT_LOCALE];
}

function interpolate(message, params) {
  if (!params || typeof message !== "string") {
    return message;
  }
  return message.replace(/\{([A-Za-z0-9_]+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(params, key) ? String(params[key]) : match
  );
}

function syncDocument() {
  if (!globalThis.document) {
    return;
  }
  document.documentElement.lang = locale.value;
  document.title = t("app.title");
}

export function t(key, params = {}) {
  const message = getMessage(messagesFor(locale.value), key) ?? getMessage(catalogs[DEFAULT_LOCALE], key) ?? key;
  return interpolate(message, params);
}

export function setLocale(nextLocale) {
  locale.value = normalizeLocale(nextLocale);
  writePreference(globalThis.localStorage, STORAGE_KEYS.language, locale.value);
  syncDocument();
}

export function useI18n() {
  syncDocument();

  return {
    locale,
    supportedLocales: SUPPORTED_LOCALES,
    setLocale,
    t
  };
}
