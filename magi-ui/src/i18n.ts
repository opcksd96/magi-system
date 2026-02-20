import i18next from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translations
import jp from '../locales/jp.json';

const resources = {
  en: {
    translation: {
      "command": "COMMAND",
      "projection": "PROJECTION",
      "system_status": "SYSTEM STATUS",
      "initializing": "INITIALIZING...",
      "waiting": "WAITING",
      "online": "ONLINE",
      "offline": "OFFLINE",
      "processing": "PROCESSING",
      "execute": "EXECUTE",
      "dismiss": "DISMISS",
      "passed": "PASSED",
      "rejected": "REJECTED",
      "enter_query": "ENTER QUERY FOR MAGI ANALYSIS...",
      "decision_report": "DECISION REPORT",
      "main_ruling": "MAIN RULING",
      "reason": "REASON",
      "appendix": "APPENDIX",
      "telemetry_tkn": "TKN",
      "telemetry_time": "TIME"
    }
  },
  jp: { translation: jp }
};

export async function initI18n() {
  await i18next
    .use(LanguageDetector)
    .init({
      resources,
      fallbackLng: 'en',
      interpolation: { escapeValue: false }
    });
}

export function translateUI() {
  const elements = document.querySelectorAll('[data-i18n]');
  elements.forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key) {
      el.textContent = i18next.t(key);
    }
  });

  const Placeholders = document.querySelectorAll('[data-i18n-attr]');
  Placeholders.forEach(el => {
    const attr = el.getAttribute('data-i18n-attr');
    const key = el.getAttribute('data-i18n-key');
    if (attr && key) {
      el.setAttribute(attr, i18next.t(key));
    }
  });
}

export { i18next };
