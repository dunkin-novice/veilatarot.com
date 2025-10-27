/**
 * Tarot of the Day - Client-side logic
 * Handles locale switching, tarot draws, and rendering results.
 */
(function () {
  const PRODUCTION_BASE_URL = "https://veilatarot.com";
  const LOCALE_STORAGE_KEY = "veilatarot-locale";
  const DEFAULT_LOCALE = "en";
  const SUPPORTED_LOCALES = ["en", "th"];
  const SPREAD_POSITIONS = ["past", "present", "future"];

  const localeState = {
    current: DEFAULT_LOCALE,
    messages: {},
  };

  const cardState = {
    cards: [],
    currentDraw: [],
  };

  const ASSET_BASE_URL = PRODUCTION_BASE_URL;
  const LOCALES_BASE_URL = `${ASSET_BASE_URL}/locales`;
  const CARDS_DATA_URL = `${ASSET_BASE_URL}/data/cards.json`;

  document.addEventListener("DOMContentLoaded", () => {
    initLocale().then(() => {
      bindLanguageButtons();
      highlightActiveLanguage();
      hydratePageSpecificFeatures();
    });
  });

  /**
   * Initialize locale from storage or browser settings, fetch translations.
   */
  async function initLocale() {
    const storedLang = localStorage.getItem(LOCALE_STORAGE_KEY);
    const browserLang = navigator.language?.slice(0, 2).toLowerCase();
    const preferred = storedLang || (SUPPORTED_LOCALES.includes(browserLang) ? browserLang : DEFAULT_LOCALE);
    await switchLang(preferred);
  }

  /**
   * Attach click listeners to language switcher buttons.
   */
  function bindLanguageButtons() {
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetLang = btn.dataset.lang;
        if (targetLang && SUPPORTED_LOCALES.includes(targetLang)) {
          switchLang(targetLang);
        }
      });
    });
  }

  /**
   * Switch current language, load translations if missing, and update UI.
   * @param {string} lang
   */
  async function switchLang(lang) {
    if (localeState.current === lang && localeState.messages[lang]) {
      applyTranslations();
      highlightActiveLanguage();
      rerenderReadingIfNeeded();
      return;
    }

    if (!localeState.messages[lang]) {
      try {
        const response = await fetch(`${LOCALES_BASE_URL}/${lang}.json`);
        if (!response.ok) throw new Error(`Locale file not found: ${lang}`);
        localeState.messages[lang] = await response.json();
      } catch (error) {
        console.error(error);
        if (lang !== DEFAULT_LOCALE) {
          return switchLang(DEFAULT_LOCALE);
        }
      }
    }

    localeState.current = lang;
    localStorage.setItem(LOCALE_STORAGE_KEY, lang);
    applyTranslations();
    highlightActiveLanguage();
    rerenderReadingIfNeeded();
  }

  /**
   * Apply translations to DOM nodes using data-i18n attribute.
   */
  function applyTranslations() {
    const messages = localeState.messages[localeState.current];
    if (!messages) return;

    document.querySelectorAll("[data-i18n]").forEach((node) => {
      const key = node.dataset.i18n;
      if (!key || !messages[key]) return;

      const tag = node.tagName.toLowerCase();
      if (tag === "input" || tag === "textarea") {
        node.placeholder = messages[key];
      } else {
        node.textContent = messages[key];
      }
    });

    document.documentElement.lang = localeState.current;
  }

  /**
   * Visually highlight the active language button.
   */
  function highlightActiveLanguage() {
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.lang === localeState.current);
    });
  }

  /**
   * Hydrate page-specific logic such as drawing cards on daily.html.
   */
  function hydratePageSpecificFeatures() {
    const drawBtn = document.getElementById("draw-btn");
    if (drawBtn) {
      loadCards();
      drawBtn.addEventListener("click", drawThree);
    }
  }

  /**
   * Fetch tarot card data if not already loaded.
   */
  async function loadCards() {
    if (cardState.cards.length > 0) return;
    try {
      const response = await fetch(CARDS_DATA_URL);
      if (!response.ok) throw new Error("Unable to load card data");
      const cards = await response.json();
      cardState.cards = normalizeCards(cards);
    } catch (error) {
      console.error(error);
    }
  }

  /**
   * Normalize card entries into a consistent structure that supports
   * position-aware meanings and bilingual names.
   * @param {Array} entries
   * @returns {Array}
   */
  function normalizeCards(entries = []) {
    if (!Array.isArray(entries)) return [];

    const hasModernShape = entries.some((entry) => entry && typeof entry === "object" && ("upright" in entry || "reversed" in entry));

    if (hasModernShape) {
      return entries
        .map((entry, index) => {
          if (!entry) return null;
          const id = Number.isFinite(entry.id) ? entry.id : index + 1;
          const nameEn = typeof entry.name_en === "string" && entry.name_en.trim() ? entry.name_en.trim() : (typeof entry.name === "string" ? entry.name.trim() : `Card ${id}`);
          const nameTh = typeof entry.name_th === "string" && entry.name_th.trim() ? entry.name_th.trim() : nameEn;
          return {
            id,
            names: { en: nameEn, th: nameTh },
            meanings: {
              upright: normalizeOrientationBlock(entry.upright),
              reversed: normalizeOrientationBlock(entry.reversed),
            },
          };
        })
        .filter(Boolean);
    }

    const grouped = new Map();
    entries.forEach((entry) => {
      if (!entry || typeof entry !== "object") return;
      const rawName = typeof entry.name === "string" ? entry.name.trim() : "";
      if (!rawName) return;
      if (!grouped.has(rawName)) {
        grouped.set(rawName, {
          id: Number.isFinite(entry.id) ? entry.id : grouped.size + 1,
          names: { en: rawName, th: rawName },
          meanings: {
            upright: createEmptyOrientationBlock(),
            reversed: createEmptyOrientationBlock(),
          },
        });
      }
      const target = grouped.get(rawName);
      const orientationKey = entry.orientation === "reversed" ? "reversed" : "upright";
      const meaning = normalizeMeaningValue({
        en: entry.en_meaning,
        th: entry.th_meaning,
      });
      SPREAD_POSITIONS.forEach((position) => {
        target.meanings[orientationKey][position] = meaning;
      });
    });

    return Array.from(grouped.values()).map((card, index) => ({
      id: card.id ?? index + 1,
      names: card.names,
      meanings: card.meanings,
    }));
  }

  /**
   * Normalize an orientation block so that each spread position has
   * bilingual meaning objects.
   * @param {object|string} block
   * @returns {object}
   */
  function normalizeOrientationBlock(block) {
    if (!block || (typeof block !== "object" && typeof block !== "string")) {
      const empty = createEmptyOrientationBlock();
      return empty;
    }

    const resolved = {};
    const fallback = typeof block === "string" ? normalizeMeaningValue(block) : null;

    SPREAD_POSITIONS.forEach((position) => {
      if (block && typeof block === "object" && Object.prototype.hasOwnProperty.call(block, position)) {
        resolved[position] = normalizeMeaningValue(block[position]);
      } else if (block && typeof block === "object" && Object.prototype.hasOwnProperty.call(block, "general")) {
        resolved[position] = normalizeMeaningValue(block.general);
      } else if (fallback) {
        resolved[position] = fallback;
      } else {
        resolved[position] = { en: "", th: "" };
      }
    });

    return resolved;
  }

  /**
   * Create an empty orientation block stub.
   * @returns {object}
   */
  function createEmptyOrientationBlock() {
    return SPREAD_POSITIONS.reduce((acc, position) => {
      acc[position] = { en: "", th: "" };
      return acc;
    }, {});
  }

  /**
   * Convert meaning values (string/object) into a bilingual object.
   * @param {string|object} value
   * @returns {{en: string, th: string}}
   */
  function normalizeMeaningValue(value) {
    if (typeof value === "string") {
      const trimmed = value.trim();
      return { en: trimmed, th: trimmed };
    }
    if (value && typeof value === "object") {
      const enRaw = value.en ?? value.en_meaning ?? value.enMeaning ?? value.text ?? value.value;
      const thRaw = value.th ?? value.th_meaning ?? value.thMeaning ?? value.localised;
      const en = typeof enRaw === "string" ? enRaw.trim() : enRaw != null ? String(enRaw).trim() : "";
      const th = typeof thRaw === "string" ? thRaw.trim() : thRaw != null ? String(thRaw).trim() : "";
      if (en || th) {
        return { en, th: th || en };
      }
    }
    return { en: "", th: "" };
  }

  /**
   * Draw three unique cards, assign spread positions, and render.
   */
  async function drawThree() {
    if (cardState.cards.length === 0) {
      await loadCards();
    }
    if (cardState.cards.length === 0) return;

    const available = [...cardState.cards];
    const drawn = [];

    for (let i = 0; i < SPREAD_POSITIONS.length; i += 1) {
      if (available.length === 0) break;
      const index = Math.floor(Math.random() * available.length);
      const [base] = available.splice(index, 1);
      if (!base) continue;
      const orientation = Math.random() >= 0.5 ? "upright" : "reversed";
      drawn.push({
        id: base.id,
        names: base.names,
        meanings: base.meanings,
        orientation,
        position: SPREAD_POSITIONS[i],
      });
    }

    cardState.currentDraw = drawn;
    renderReading(drawn, localeState.current);
  }

  /**
   * Render cards and the combined conclusion paragraph.
   * @param {Array} cards
   * @param {string} lang
   */
  function renderReading(cards, lang) {
    const container = document.getElementById("cards-container");
    const conclusionEl = document.getElementById("conclusion");
    if (!container || !conclusionEl) return;

    container.innerHTML = "";

    const orientationLabels = {
      en: { upright: "Upright", reversed: "Reversed" },
      th: { upright: "ไพ่ตั้งตรง", reversed: "ไพ่กลับหัว" },
    };

    const positionLabels = {
      en: { past: "Past", present: "Present", future: "Future", general: "Insight" },
      th: { past: "อดีต", present: "ปัจจุบัน", future: "อนาคต", general: "สารจากจักรวาล" },
    };

    cards.forEach((card, idx) => {
      const cardEl = document.createElement("article");
      cardEl.className = "card";
      cardEl.style.animationDelay = `${idx * 0.1}s`;

      const positionBadge = document.createElement("div");
      positionBadge.className = "position-badge";
      const positionText = positionLabels[lang]?.[card.position]
        || positionLabels[DEFAULT_LOCALE]?.[card.position]
        || card.position;
      positionBadge.textContent = positionText;

      const title = document.createElement("h3");
      title.textContent = getCardName(card, lang);

      const orientation = document.createElement("div");
      orientation.className = "orientation";
      orientation.textContent = orientationLabels[lang]?.[card.orientation]
        || orientationLabels[DEFAULT_LOCALE]?.[card.orientation]
        || card.orientation;

      const meaning = document.createElement("p");
      meaning.className = "meaning";
      meaning.textContent = getMeaningForCard(card, lang);

      cardEl.append(positionBadge, title, orientation, meaning);
      container.appendChild(cardEl);
    });

    const conclusionText = buildConclusion(cards, lang);
    conclusionEl.innerHTML = "";

    const heading = document.createElement("h2");
    heading.dataset.i18n = "conclusion";
    heading.textContent = localeState.messages[lang]?.conclusion
      || localeState.messages[DEFAULT_LOCALE]?.conclusion
      || "Conclusion";

    const body = document.createElement("p");
    body.textContent = conclusionText;

    conclusionEl.append(heading, body);
    applyTranslations();
  }

  /**
   * Resolve the best display name for the card in the current locale.
   * @param {object} card
   * @param {string} lang
   * @returns {string}
   */
  function getCardName(card, lang) {
    if (!card) return "";
    const names = card.names || {};
    const localized = typeof names[lang] === "string" ? names[lang].trim() : "";
    if (localized) return localized;
    const fallback = typeof names[DEFAULT_LOCALE] === "string" ? names[DEFAULT_LOCALE].trim() : "";
    if (fallback) return fallback;
    if (typeof card.name === "string" && card.name.trim()) return card.name.trim();
    return `Card ${card.id ?? ""}`.trim();
  }

  /**
   * Retrieve the meaning text for a card based on orientation and position.
   * @param {object} card
   * @param {string} lang
   * @returns {string}
   */
  function getMeaningForCard(card, lang) {
    if (!card) return "";
    const orientationSet = card.meanings?.[card.orientation] || {};
    const primary = orientationSet[card.position];
    const fallback = orientationSet.past || orientationSet.present || orientationSet.future;
    const meaning = extractLocalizedText(primary, lang) || extractLocalizedText(fallback, lang);
    return meaning;
  }

  /**
   * Extract a localized string from a meaning value.
   * @param {string|object} value
   * @param {string} lang
   * @returns {string}
   */
  function extractLocalizedText(value, lang) {
    if (!value) return "";
    if (typeof value === "string") {
      return value.trim();
    }
    if (typeof value === "object") {
      const direct = typeof value[lang] === "string" ? value[lang].trim() : "";
      if (direct) return direct;
      const fallback = typeof value[DEFAULT_LOCALE] === "string" ? value[DEFAULT_LOCALE].trim() : "";
      if (fallback) return fallback;
      const en = typeof value.en === "string" ? value.en.trim() : "";
      if (en) return en;
      const th = typeof value.th === "string" ? value.th.trim() : "";
      if (th) return th;
      const first = Object.values(value).find((text) => typeof text === "string" && text.trim());
      if (first) return first.trim();
    }
    return "";
  }

  /**
   * Build a gentle conclusion paragraph by combining summary sentences.
   * @param {Array} cards
   * @param {string} lang
   * @returns {string}
   */
  function buildConclusion(cards, lang) {
    const intro = {
      en: "This spread suggests ",
      th: "การตีความนี้ชี้ให้เห็นว่า ",
    };

    const fragments = cards
      .map((card) => extractSummarySentence(getMeaningForCard(card, lang)))
      .filter(Boolean);

    if (fragments.length === 0) {
      return (lang === "th"
        ? "การตีความนี้ชี้ให้เห็นว่าถึงเวลาหยุดพักและฟังเสียงในใจของคุณอีกครั้ง."
        : "This spread suggests taking a quiet moment to listen to your inner guidance.");
    }

    const joiner = lang === "th" ? " " : " ";
    const body = fragments.join(joiner).trim();
    const prefix = intro[lang] || intro[DEFAULT_LOCALE];
    const combined = `${prefix}${body}`.trim();
    return /[.!?…]$/.test(combined) ? combined : `${combined}.`;
  }

  /**
   * Extract the first complete sentence (or fallback to full text).
   * @param {string} text
   * @returns {string}
   */
  function extractSummarySentence(text) {
    if (!text) return "";
    const sanitized = text.replace(/\s+/g, " ").trim();
    if (!sanitized) return "";
    const match = sanitized.match(/[^.!?…]+[.!?…]?/);
    return match ? match[0].trim() : sanitized;
  }

  /**
   * Re-render the current reading when language changes.
   */
  function rerenderReadingIfNeeded() {
    if (!Array.isArray(cardState.currentDraw) || cardState.currentDraw.length === 0) return;
    renderReading(cardState.currentDraw, localeState.current);
  }
})();
