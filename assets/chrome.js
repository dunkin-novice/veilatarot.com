/* Veila shared chrome — injects the three-vertical nav under .site-header.
   Idempotent: skips if a .vertical-nav already exists (e.g. the / and /th/ portals).
   Locale-aware: Thai link set + labels on /th/ pages. */
(function () {
  function init() {
    var header = document.querySelector('.site-header');
    if (!header) return;                         // no header → nothing to anchor to
    if (document.querySelector('.vertical-nav')) return; // already present (portals)

    var path = location.pathname;
    var isTh = path.indexOf('/th/') === 0;

    var L = isTh
      ? { love: 'ความรัก', career: 'การงาน', health: 'สุขภาพ', neu: 'ใหม่', soon: 'เร็ว ๆ นี้',
          loveHref: '/th/love-tarot/', careerHref: '/th/career/' }
      : { love: 'Love', career: 'Career', health: 'Health', neu: 'New', soon: 'Soon',
          loveHref: '/love-readings/', careerHref: '/career/' };

    // active vertical by path keyword
    var active = '';
    if (/love|relationship|heart/.test(path)) active = 'love';
    else if (/career|money|job|work/.test(path)) active = 'career';

    var nav = document.createElement('nav');
    nav.className = 'vertical-nav';
    nav.setAttribute('aria-label', 'Readings');
    nav.innerHTML =
      '<a href="' + L.loveHref + '"' + (active === 'love' ? ' aria-current="page"' : '') + '>' + L.love + '</a>' +
      '<a href="' + L.careerHref + '"' + (active === 'career' ? ' aria-current="page"' : '') + '>' +
        L.career + ' <span class="tag">' + L.neu + '</span></a>' +
      '<span class="vn-soon">' + L.health + ' <span class="tag">' + L.soon + '</span></span>';

    header.insertAdjacentElement('afterend', nav);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
