/* Veila analytics — delegated gtag event hooks.
 *
 * Inline scripts on the main reading app + daily card pages fire their
 * own events via window.veilaFire(name, params). This file handles the
 * site-wide cross-page events:
 *   - related_card_clicked   (any anchor in .related-cards-grid)
 *   - language_switched      (any anchor in .lang-toggle)
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

  document.addEventListener('click', function (e) {
    var rc = e.target.closest && e.target.closest('.related-cards-grid a');
    if (rc) {
      fire('related_card_clicked', {
        target_card: slugFromHref(rc.getAttribute('href')),
        source_page: location.pathname
      });
      return;
    }
    var lt = e.target.closest && e.target.closest('.lang-toggle a');
    if (lt) {
      fire('language_switched', {
        to_lang: (lt.textContent || '').trim().toLowerCase(),
        source_page: location.pathname,
        method: lt.getAttribute('href') ? 'navigate' : 'inline'
      });
      return;
    }
  }, { capture: false });
})();
