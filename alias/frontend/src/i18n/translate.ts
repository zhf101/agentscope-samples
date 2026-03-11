import { DEFAULT_LOCALE, Locale, messages } from "./messages";

const getStoredLocale = (): Locale => {
  try {
    const saved = localStorage.getItem("language");
    if (saved === "zh" || saved === "en") return saved;
  } catch {
    // ignore storage errors
  }
  return DEFAULT_LOCALE;
};

const formatMessage = (
  template: string,
  params?: Record<string, string | number>,
) => {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    const value = params[key];
    return value === undefined || value === null ? `{${key}}` : String(value);
  });
};

export const translate = (
  key: string,
  params?: Record<string, string | number>,
) => {
  const locale = getStoredLocale();
  const template = messages[locale]?.[key] ?? messages.en[key] ?? key;
  return formatMessage(template, params);
};
