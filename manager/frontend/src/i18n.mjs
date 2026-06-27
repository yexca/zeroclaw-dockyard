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
