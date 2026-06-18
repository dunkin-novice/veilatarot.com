/* Veila analytics — delegated gtag event hooks.
 *
 * Inline scripts on the main reading app + daily card pages fire their
 * own events via window.veilaFire(name, params). This file handles the
 * site-wide cross-page events:
 *   - related_card_clicked   (any anchor in .related-cards-grid)
 *   - language_switched      (any anchor in .lang-toggle)
 *   - meaning_viewed         (fired on card page load)
 *   - cta_clicked            (generic cta button clicks)
 *   - zodiac_intent_clicked  (zodiac love tarot clicks)
 *
 * All firing is defensive — does nothing if gtag is unavailable.
 */
(function () {
  function fire(name, params) {
    if (typeof window.gtag === 'function') {
      try { window.gtag('event', name, params || {}); } catch (e) {}
    }
  }
  window.veilaFire = fire;

  function slugFromHref(href) {
    if (!href) return '';
    var path = href.split('?')[0].split('#')[0];
    var parts = path.split('/').filter(Boolean);
    return parts[parts.length - 1] || '';
  }

  // 1. Page-load events
  var path = location.pathname;
  var lang = (document.documentElement.lang || 'en').slice(0, 2);
  
  if (path.indexOf('/cards/') !== -1) {
    var cardId = slugFromHref(path);
    if (cardId) {
      fire('meaning_viewed', {
        card_id: cardId,
        locale: lang,
        surface: 'web'
      });
    }
  }

  // 2. Click events
  document.addEventListener('click', function (e) {
    var rc = e.target.closest && e.target.closest('.related-cards-grid a');
    if (rc) {
      fire('related_card_clicked', {
        target_card: slugFromHref(rc.getAttribute('href')),
        source_page: path
      });
      return;
    }
    
    var lt = e.target.closest && e.target.closest('.lang-toggle a');
    if (lt) {
      fire('language_switched', {
        to_lang: (lt.textContent || '').trim().toLowerCase(),
        source_page: path,
        method: lt.getAttribute('href') ? 'navigate' : 'inline'
      });
      return;
    }

    var cta = e.target.closest && e.target.closest('.cta-btn, .btn');
    if (cta) {
      var href = cta.getAttribute('href') || '';
      
      // Special case: Zodiac Love Intent
      if (href.indexOf('/quick-love-reading/?q=zodiac-') !== -1) {
        var q = (href.split('q=')[1] || '').split('&')[0];
        fire('love_question_intent_cta_clicked', {
          intent_slug: q,
          lang: lang,
          source_page: path
        });
        return;
      }
      
      // Generic CTA
      fire('cta_clicked', {
        cta_label: (cta.textContent || '').trim().substring(0, 50),
        cta_href: href,
        source_page: path,
        locale: lang
      });
      return;
    }
  }, { capture: false });
})();
