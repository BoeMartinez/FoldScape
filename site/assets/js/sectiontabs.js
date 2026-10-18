/* Travelling fold over the section tabs.
 *
 * Same mound as the top bar, but these tabs switch panels in place. Nothing
 * navigates, so the crossing plays in full and plays again every time — which
 * is the only condition under which the effect is actually visible. A dome of
 * white light is near-invisible at rest; it reads while it moves.
 */
function startSectionTabs() {
    'use strict';

    var nav = document.getElementById('sectabs');
    if (!nav) return;

    var tabs = [].slice.call(nav.querySelectorAll('.sectab'));
    if (tabs.length < 2) return;

    var labels = tabs.map(function (t) { return t.querySelector('span'); });
    var still = window.matchMedia('(prefers-reduced-motion: reduce)');

    var mound = document.createElement('span');
    var shade = document.createElement('span');
    mound.className = 'sectabs-mound';
    shade.className = 'sectabs-shadow';
    mound.setAttribute('aria-hidden', 'true');
    shade.setAttribute('aria-hidden', 'true');
    nav.insertBefore(shade, nav.firstChild);
    nav.insertBefore(mound, nav.firstChild);

    var anim = null;

    function box(tab) {
        return { x: tab.offsetLeft, w: tab.offsetWidth };
    }

    function paint(x, w, squash, lag) {
        mound.style.width = w + 'px';
        mound.style.transform = 'translateX(' + x + 'px) scale(' + (1 / squash) + ',' + squash + ')';
        shade.style.width = (w * 0.92) + 'px';
        shade.style.left = (x - lag + w * 0.04) + 'px';
        shade.style.top = (mound.offsetTop + mound.offsetHeight - 3) + 'px';
        shade.style.opacity = 1;
        mound.style.opacity = 1;

        // The paper bulges over the mound and settles behind it.
        var centre = x + w / 2;
        for (var i = 0; i < labels.length; i++) {
            var b = box(tabs[i]);
            var d = (b.x + b.w / 2) - centre;
            var sigma = Math.max(b.w * 0.6, 28);
            var lift = 2.4 * Math.exp(-(d * d) / (2 * sigma * sigma));
            labels[i].style.transform = 'translateY(' + (-lift).toFixed(2) + 'px)';
        }
    }

    function settle(tab) {
        var b = box(tab);
        paint(b.x, b.w, 1, 0);
    }

    function travel(a, b) {
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
            if (p < 1) { anim = requestAnimationFrame(step); } else { anim = null; }
        })(t0);
    }

    function show(tab) {
        var prev = nav.querySelector('.sectab.on');
        if (!prev || prev === tab) return;

        prev.classList.remove('on');
        prev.setAttribute('aria-selected', 'false');
        prev.tabIndex = -1;
        document.getElementById(prev.getAttribute('aria-controls')).hidden = true;

        tab.classList.add('on');
        tab.setAttribute('aria-selected', 'true');
        tab.tabIndex = 0;
        document.getElementById(tab.getAttribute('aria-controls')).hidden = false;

        if (still.matches) { settle(tab); return; }
        travel(box(prev), box(tab));
    }

    nav.addEventListener('click', function (ev) {
        var tab = ev.target.closest('.sectab');
        if (tab) show(tab);
    });

    // Left and right walk the tabs, as a tablist is expected to.
    nav.addEventListener('keydown', function (ev) {
        if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
        var i = tabs.indexOf(document.activeElement);
        if (i === -1) return;
        ev.preventDefault();
        var next = tabs[(i + (ev.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
        next.focus();
        show(next);
    });

    function reset() { settle(nav.querySelector('.sectab.on')); }

    reset();
    // Fonts load after first paint and change the tab widths under the mound.
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(reset);
    }
    window.addEventListener('resize', reset);
}

document.addEventListener('DOMContentLoaded', startSectionTabs);
