/* Travelling fold under the nav links.
 *
 * One mound, not a state each link owns. It rests under the current page and
 * travels to the link you pick. While it moves it squashes, its shadow lags
 * behind the direction of travel so it reads as having mass, and each label
 * lifts on a travelling bump as the mound passes under it.
 *
 * These are real page links, so the travel IS the transition: the click is
 * held, the mound crosses, then the browser navigates and the next page draws
 * with the mound already resting there. Modified and middle clicks are left
 * alone, and with no JS the links behave normally.
 */
(function () {
    'use strict';

    var nav = document.querySelector('.topbar .nav-fold');
    if (!nav) return;

    var links = [].slice.call(nav.querySelectorAll('a'));
    if (links.length < 2) return;

    var still = window.matchMedia('(prefers-reduced-motion: reduce)');
    var mound = document.createElement('span');
    var shade = document.createElement('span');
    mound.className = 'nav-mound';
    shade.className = 'nav-mound-shadow';
    mound.setAttribute('aria-hidden', 'true');
    shade.setAttribute('aria-hidden', 'true');
    nav.insertBefore(shade, nav.firstChild);
    nav.insertBefore(mound, nav.firstChild);

    var anim = null;

    function box(link) {
        return { x: link.offsetLeft + link.parentNode.offsetLeft, w: link.offsetWidth };
    }

    function paint(x, w, squash, lag) {
        mound.style.width = w + 'px';
        mound.style.transform = 'translateX(' + x + 'px) scale(' + (1 / squash) + ',' + squash + ')';
        shade.style.width = (w * 0.9) + 'px';
        shade.style.left = (x - lag + w * 0.05) + 'px';

        // The paper bulges over the mound and settles behind it.
        var centre = x + w / 2;
        for (var i = 0; i < links.length; i++) {
            var b = box(links[i]);
            var d = (b.x + b.w / 2) - centre;
            var sigma = Math.max(b.w * 0.6, 26);
            var lift = 2.8 * Math.exp(-(d * d) / (2 * sigma * sigma));
            links[i].style.transform = 'translateY(' + (-lift).toFixed(2) + 'px)';
        }
    }

    function settle(link) {
        var b = box(link);
        paint(b.x, b.w, 1, 0);
        mound.style.opacity = 1;
        shade.style.opacity = 1;
    }

    function travel(a, b, done) {
        if (anim) cancelAnimationFrame(anim);
        var dist = Math.abs((b.x + b.w / 2) - (a.x + a.w / 2));
        var dur = Math.min(620, Math.max(300, 240 + dist * 0.9));
        var dir = (b.x >= a.x) ? 1 : -1;
        var t0 = performance.now();

        (function step(now) {
            var p = Math.min(1, (now - t0) / dur);
            var e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
            var wave = Math.sin(Math.PI * p);
            paint(a.x + (b.x - a.x) * e, a.w + (b.w - a.w) * e, 1 - 0.16 * wave, dir * 6 * wave);
            if (p < 1) {
                anim = requestAnimationFrame(step);
            } else {
                anim = null;
                if (done) done();
            }
        })(t0);
    }

    function current() {
        return nav.querySelector('a.contrast') || links[0];
    }

    nav.addEventListener('click', function (ev) {
        // Leave modified clicks to the browser: new tab, new window, download.
        if (ev.defaultPrevented || ev.button !== 0) return;
        if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;

        var link = ev.target.closest('a');
        if (!link || links.indexOf(link) === -1) return;

        var from = current();
        if (link === from) return;
        if (still.matches) return;

        ev.preventDefault();
        var href = link.href;
        travel(box(from), box(link), function () {
            window.location.href = href;
        });
    });

    function reset() { settle(current()); }

    // Fonts load after first paint and change the link widths under the mound.
    reset();
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(reset);
    }
    window.addEventListener('resize', reset);
})();
