/* The paper strip under the top-bar links. The strip itself is in paper.js.
 *
 * These are real page links, so the travel IS the transition: the click is
 * held, the strip crosses, then the browser navigates and the next page draws
 * with the strip already resting there. Modified and middle clicks are left
 * alone, and with no JS the links behave normally.
 */
(function () {
    'use strict';

    var nav = document.querySelector('.topbar .nav-fold');
    if (!nav) return;

    var links = [].slice.call(nav.querySelectorAll('a'));
    if (links.length < 2) return;

    var still = window.matchMedia('(prefers-reduced-motion: reduce)');

    function current() {
        return nav.querySelector('a.contrast') || links[0];
    }

    var strip = PaperStrip(nav, links, {
        label: function (a) { return a; },
        current: current,
        pad: 8,
        rest: '--ink-soft'
    });

    nav.addEventListener('click', function (ev) {
        // Leave modified clicks to the browser: new tab, new window, download.
        if (ev.defaultPrevented || ev.button !== 0) return;
        if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;

        var link = ev.target.closest('a');
        if (!link || links.indexOf(link) === -1) return;
        if (link === current() || still.matches) return;

        ev.preventDefault();
        var href = link.href;
        strip.travel(null, link, function () {
            window.location.href = href;
        });
    });
})();
