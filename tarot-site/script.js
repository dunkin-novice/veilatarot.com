/**
 * Tarot of the Day - Client-side logic
 * Handles locale switching, tarot draws, and rendering results.
 */
(function () {
  const LOCALE_STORAGE_KEY = "tarot-site-locale";
  const DEFAULT_LOCALE = "en";
  const SUPPORTED_LOCALES = ["en", "th"];
  const localeState = {
    current: DEFAULT_LOCALE,
    messages: {},
  };

  const cardState = {
    cards: [],
  };

  const conclusions = {
    en: {
      positive: [
        "Together, the cards reveal renewal and gentle confidence.",
        "A wave of harmony rises as you align with your heart’s truth.",
        "You are stepping into a rhythm of joy and purposeful motion.",
      ],
      neutral: [
        "Let today unfold at its own pace; observe each sign with calm curiosity.",
        "Balance is achieved through mindful choices and quiet reflection.",
      ],
      cautious: [
        "Patience will serve you; let things unfold naturally.",
        "Be aware of resistance—growth asks for small steps first.",
      ],
      ambiguous: [
        "The path splits in mist; trust your senses to choose the moment.",
        "Not everything is visible yet—listen closely to subtle cues.",
      ],
      certain: [
        "Momentum is yours; your intention echoes loudly in the world.",
        "The pattern is clear—act with assurance and compassion.",
      ],
    },
    th: {
      positive: [
        "ไพ่ทั้งสามใบสะท้อนถึงพลังใหม่และความสมดุลที่ค่อย ๆ ก่อตัวขึ้นในใจของคุณ.",
        "หนทางข้างหน้ากำลังเปิดออกด้วยพลังแห่งศรัทธาและความสงบ.",
        "วันนี้เป็นเวลาที่คุณจะได้ก้าวอย่างมั่นใจไปสู่ความหวังใหม่.",
      ],
      neutral: [
        "ปล่อยให้วันนี้ดำเนินไปอย่างสงบ รับฟังสัญญาณเล็ก ๆ ด้วยหัวใจที่นิ่ง.",
        "ความสมดุลเกิดจากการเลือกอย่างมีสติและการไตร่ตรอง.",
      ],
      cautious: [
        "อย่าเร่งผลลัพธ์ ปล่อยให้สิ่งต่าง ๆ เติบโตตามเวลา.",
        "ไพ่เตือนให้ก้าวอย่างระมัดระวัง แต่ยังคงเชื่อในตัวเอง.",
      ],
      ambiguous: [
        "เส้นทางยังถูกปกคลุมด้วยหมอก ใช้สัญชาตญาณนำทาง.",
        "ยังมีเรื่องราวที่ซ่อนอยู่ จงตั้งใจฟังเสียงกระซิบของหัวใจ.",
      ],
      certain: [
        "แรงผลักดันอยู่ในมือคุณแล้ว จงใช้เจตนาที่ชัดเจนให้เกิดผล.",
        "คำตอบชัดเจน จงลงมือด้วยความมั่นใจและเมตตา.",
      ],
    },
  };

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
    let initialLang = storedLang || (SUPPORTED_LOCALES.includes(browserLang) ? browserLang : DEFAULT_LOCALE);

    await switchLang(initialLang);
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
      return;
    }

    if (!localeState.messages[lang]) {
      try {
        const response = await fetch(`locales/${lang}.json`);
        if (!response.ok) throw new Error(`Locale file not found: ${lang}`);
        const messages = await response.json();
        localeState.messages[lang] = messages;
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
      if (key && messages[key]) {
        if (node.tagName.toLowerCase() === "input" || node.tagName.toLowerCase() === "textarea") {
          node.placeholder = messages[key];
        } else if (node.tagName.toLowerCase() === "button" || node.tagName.toLowerCase() === "a") {
          node.textContent = messages[key];
        } else {
          node.textContent = messages[key];
        }
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
      const response = await fetch("data/cards.json");
      if (!response.ok) throw new Error("Unable to load card data");
      const cards = await response.json();
      cardState.cards = cards;
    } catch (error) {
      console.error(error);
    }
  }

  /**
   * Draw three unique cards and render the reading.
   */
  async function drawThree() {
    if (cardState.cards.length === 0) {
      await loadCards();
    }
    const available = [...cardState.cards];
    const drawn = [];

    for (let i = 0; i < 3 && available.length; i += 1) {
      const index = Math.floor(Math.random() * available.length);
      const [card] = available.splice(index, 1);
      const orientation = Math.random() > 0.5 ? "upright" : "reversed";
      drawn.push({ ...card, orientation });
    }

    const tone = randomTone();
    renderReading(drawn, tone, localeState.current);
  }

  /**
   * Select a random tone label from the available options.
   * @returns {string}
   */
  function randomTone() {
    const tones = Object.keys(conclusions.en);
    const index = Math.floor(Math.random() * tones.length);
    return tones[index];
  }

  /**
   * Render cards and conclusion to the DOM.
   * @param {Array} cards
   * @param {string} tone
   * @param {string} lang
   */
  function renderReading(cards, tone, lang) {
    const container = document.getElementById("cards-container");
    const conclusionEl = document.getElementById("conclusion");
    if (!container || !conclusionEl) return;

    container.innerHTML = "";

    const orientationLabels = {
      en: { upright: "Upright", reversed: "Reversed" },
      th: { upright: "ไพ่ตั้งตรง", reversed: "ไพ่กลับหัว" },
    };

    cards.forEach((card, idx) => {
      const cardEl = document.createElement("article");
      cardEl.className = "card";
      cardEl.style.animationDelay = `${idx * 0.1}s`;

      const title = document.createElement("h3");
      title.textContent = card.name;

      const orientation = document.createElement("div");
      orientation.className = "orientation";
      orientation.textContent = orientationLabels[lang]?.[card.orientation] || card.orientation;

      const archetype = document.createElement("div");
      archetype.className = "archetype";
      archetype.textContent = card.archetype?.[lang] || "";

      const meaning = document.createElement("p");
      meaning.textContent = card.meanings?.[card.orientation]?.[lang] || "";

      cardEl.append(title, orientation, archetype, meaning);
      container.appendChild(cardEl);
    });

    const conclusionText = makeConclusion(cards, tone, lang);
    conclusionEl.innerHTML = "";

    const heading = document.createElement("h2");
    heading.dataset.i18n = "conclusion";
    heading.textContent = localeState.messages[lang]?.conclusion || "Conclusion";

    const body = document.createElement("p");
    body.textContent = conclusionText;

    conclusionEl.append(heading, body);

    // Re-apply translations for the heading in case language switched post-render.
    applyTranslations();
  }

  /**
   * Generate a conclusion sentence based on tone and locale.
   * @param {Array} cards
   * @param {string} tone
   * @param {string} lang
   * @returns {string}
   */
  function makeConclusion(cards, tone, lang) {
    const localeConclusions = conclusions[lang] || conclusions[DEFAULT_LOCALE];
    const toneSet = localeConclusions[tone] || localeConclusions[randomTone()];
    if (!toneSet || toneSet.length === 0) {
      return "";
    }
    const index = Math.floor(Math.random() * toneSet.length);
    return toneSet[index];
  }

  /**
   * If a reading is currently displayed, re-render it when language changes.
   */
  function rerenderReadingIfNeeded() {
    const container = document.getElementById("cards-container");
    if (!container || container.children.length === 0) return;

    const cards = Array.from(container.children).map((cardEl) => {
      const name = cardEl.querySelector("h3")?.textContent || "";
      return cardState.cards.find((card) => card.name === name);
    });

    if (cards.some((card) => !card)) return;

    const existingCards = Array.from(container.children).map((cardEl) => {
      const name = cardEl.querySelector("h3")?.textContent || "";
      const orientationText = cardEl.querySelector(".orientation")?.textContent || "";
      const orientation = orientationText.includes("Reverse") || orientationText.includes("กลับหัว") ? "reversed" : "upright";
      return { ...cardState.cards.find((card) => card.name === name), orientation };
    });

    const tone = randomTone();
    renderReading(existingCards, tone, localeState.current);
  }
})();
