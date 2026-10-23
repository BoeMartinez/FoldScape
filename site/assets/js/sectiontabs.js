/* Section tabs on the home page. They switch panels in place, so the paper
 * strip's crossing is the whole transition. The strip itself is in paper.js.
 */
function startSectionTabs() {
    'use strict';

    var nav = document.getElementById('sectabs');
    if (!nav) return;

    var tabs = [].slice.call(nav.querySelectorAll('.sectab'));
    if (tabs.length < 2) return;

    var still = window.matchMedia('(prefers-reduced-motion: reduce)');

    var strip = PaperStrip(nav, tabs, {
        label: function (tab) { return tab.querySelector('span'); },
        current: function () { return nav.querySelector('.sectab.on'); },
        pad: 22,
        fit: true,
        rest: '--ink-mute'
    });

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

        if (still.matches) { strip.settle(tab); return; }
        strip.travel(null, tab);
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
}

document.addEventListener('DOMContentLoaded', startSectionTabs);
