/* A strip of paper under the selected section tab.
 *
 * The bar has no panel of its own; it is the page. The selected tab is the
 * one place the paper stands off it, a low arch the width of the label. On
 * a switch the strip travels as a wave: the edge it moves toward rises
 * first and steepest, and the edge it leaves lays back down along a long
 * tail, so the page closes up behind it.
 *
 * The strip is a height field h(x), 0 where the page is flat, drawn on a
 * canvas behind the labels. The canvas is clear wherever h is 0, so the
 * page grain shows through it. Light comes from the upper right, as it
 * does on the emblem: faces turned right catch it, the shadow falls below
 * and a little to the left.
 */
function startSectionTabs() {
    'use strict';

    var nav = document.getElementById('sectabs');
    if (!nav) return;

    var tabs = [].slice.call(nav.querySelectorAll('.sectab'));
    if (tabs.length < 2) return;

    var labels = tabs.map(function (t) { return t.querySelector('span'); });
    var still = window.matchMedia('(prefers-reduced-motion: reduce)');

    var LIFT = 1.6;    // px the strip rises at full height
    var PAD = 22;      // paper either side of a label
    var SHOULDER = 18; // half-width of the strip's edge at rest; wide, so the ends ramp rather than wall
    var BLEED = 18;    // canvas reaches past the bar so the shadow isn't cut

    var cv = document.createElement('canvas');
    cv.className = 'sectabs-paper';
    cv.setAttribute('aria-hidden', 'true');
    nav.insertBefore(cv, nav.firstChild);
    var ctx = cv.getContext('2d');

    function rgb(css) {
        var m = css.match(/[\d.]+/g) || [0, 0, 0];
        return [+m[0], +m[1], +m[2], m[3] === undefined ? 1 : +m[3]];
    }
    function token(name) {
        var probe = document.createElement('span');
        probe.style.color = 'var(' + name + ')';
        nav.appendChild(probe);
        var c = rgb(getComputedStyle(probe).color);
        nav.removeChild(probe);
        return c;
    }
    var mute = token('--ink-mute');
    var ink = token('--ink');

    var W = 0, H = 0, dpr = 1, top = 0, bot = 0;
    var state = { c: 0, w: 0, wave: 0, dir: 1, trail: 0 };
    var anim = null;

    function size() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        W = nav.clientWidth + 2 * BLEED;
        H = nav.clientHeight + 2 * BLEED;
        cv.width = Math.round(W * dpr);
        cv.height = Math.round(H * dpr);
        cv.style.width = W + 'px';
        cv.style.height = H + 'px';
        cv.style.left = -BLEED + 'px';
        cv.style.top = -BLEED + 'px';
        top = BLEED + 2;
        bot = BLEED + nav.clientHeight - 2;
    }

    // Where the strip sits under a tab: centred on it, as wide as its label.
    function bridge(tab) {
        var label = labels[tabs.indexOf(tab)];
        return {
            c: tab.offsetLeft + tab.offsetWidth / 2,
            w: Math.min(tab.offsetWidth - 4, label.offsetWidth + 2 * PAD)
        };
    }

    function smooth(t) {
        t = t < 0 ? 0 : t > 1 ? 1 : t;
        return t * t * (3 - 2 * t);
    }

    // Height of the paper at x (bar coordinates), 0 to about 1.3.
    function height(x) {
        var s = state;
        var half = s.w / 2;
        var front = SHOULDER * (1 - 0.35 * s.wave);
        var back = SHOULDER + s.trail * s.wave;
        var eL = s.dir > 0 ? back : front;
        var eR = s.dir > 0 ? front : back;
        var up = smooth((x - (s.c - half - eL)) / (2 * eL));
        var down = smooth(((s.c + half + eR) - x) / (2 * eR));
        if (up === 0 || down === 0) return 0;
        var u = (x - s.c) / half;
        var arch = 1 - 0.35 * Math.min(1, u * u);
        var lean = 1 + 0.35 * s.wave * s.dir * Math.max(-1.6, Math.min(1, u));
        return up * down * arch * lean;
    }

    function paint() {
        var step = 1 / dpr;
        var n = Math.ceil(W / step) + 1;
        var hs = new Float32Array(n);
        var x, i, any = false;
        for (i = 0; i < n; i++) {
            hs[i] = height(i * step - BLEED);
            if (hs[i] > 0) any = true;
        }

        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, W, H);

        if (any) {
            // Cast shadow, kept below the paper's lower edge so it never
            // shows through the clear paper. The canvas shadow is used for
            // the blur because Safari has no canvas filter.
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(0, H);
            for (i = 0; i < n; i++) ctx.lineTo(i * step, bot - hs[i] * LIFT);
            ctx.lineTo(W, H);
            ctx.closePath();
            ctx.clip();

            var OFF = 10000;
            ctx.shadowColor = 'rgba(30, 20, 10, 0.18)';
            ctx.shadowBlur = 8 * dpr;
            ctx.shadowOffsetX = OFF * dpr;
            ctx.shadowOffsetY = 0;
            ctx.fillStyle = '#000';
            // Zero thickness where the page is flat, so nothing shows there.
            ctx.beginPath();
            ctx.moveTo(-OFF, bot - 2);
            for (i = 0; i < n; i++) {
                x = i * step - hs[i] * 1.5;
                ctx.lineTo(x - OFF, bot - 2 + hs[i] * 4.5);
            }
            ctx.lineTo(W - OFF, bot - 2);
            ctx.closePath();
            ctx.fill();
            ctx.restore();

            // The paper itself: a little lighter where it stands off the
            // page, lit or shaded by its slope, a bright crest along the top
            // and a fine dark line where its lower edge has thickness.
            for (i = 0; i < n; i++) {
                var h = hs[i];
                if (h <= 0) continue;
                var y0 = top - h * LIFT;
                var y1 = bot - h * LIFT;
                var hn = Math.min(1, h);
                var slope = i > 0 && i < n - 1 ? (hs[i + 1] - hs[i - 1]) / (2 * step) * LIFT : 0;
                x = i * step;

                ctx.fillStyle = 'rgba(255, 255, 255,' + (0.16 * hn).toFixed(3) + ')';
                ctx.fillRect(x, y0, step, y1 - y0);

                var lit = -slope;
                if (lit > 0) {
                    ctx.fillStyle = 'rgba(255, 255, 255,' + Math.min(0.35, lit * 1.2).toFixed(3) + ')';
                } else {
                    ctx.fillStyle = 'rgba(30, 20, 10,' + Math.min(0.06, -lit * 0.25).toFixed(3) + ')';
                }
                ctx.fillRect(x, y0, step, y1 - y0);

                ctx.fillStyle = 'rgba(255, 255, 255,' + (0.6 * hn).toFixed(3) + ')';
                ctx.fillRect(x, y0, step, 1);
                ctx.fillStyle = 'rgba(30, 20, 10,' + (0.06 * hn).toFixed(3) + ')';
                ctx.fillRect(x, y1 - 1, step, 1);
            }
        }

        // Each label rides the paper under its own centre, and darkens from
        // muted to ink as the paper lifts it. The lift is the only mark.
        for (i = 0; i < labels.length; i++) {
            var mid = tabs[i].offsetLeft + tabs[i].offsetWidth / 2;
            var k = Math.min(1, height(mid));
            labels[i].style.transform = 'translateY(' + (-k * LIFT).toFixed(2) + 'px)';
            labels[i].style.color = 'rgba(' + mute.map(function (m, j) {
                var v = m + (ink[j] - m) * k;
                return j < 3 ? Math.round(v) : v.toFixed(3);
            }).join(',') + ')';
        }
    }

    function settle(tab) {
        var b = bridge(tab);
        state.c = b.c;
        state.w = b.w;
        state.wave = 0;
        paint();
    }

    function travel(a, b) {
        if (anim) cancelAnimationFrame(anim);
        var dist = Math.abs(b.c - a.c);
        var dur = Math.min(700, Math.max(340, 260 + dist * 0.9));
        var t0 = performance.now();
        state.dir = b.c >= a.c ? 1 : -1;

        (function step(now) {
            var p = Math.min(1, (now - t0) / dur);
            var e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
            state.c = a.c + (b.c - a.c) * e;
            state.w = a.w + (b.w - a.w) * e;
            state.wave = Math.sin(Math.PI * p);
            // The tail is only as long as the ground already crossed, so the
            // page never lifts behind where the strip set out from.
            state.trail = Math.min(150, Math.abs(state.c - a.c) * 0.9);
            paint();
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

        var from = { c: state.c, w: state.w };
        if (still.matches) { settle(tab); return; }
        travel(from, bridge(tab));
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

    function reset() {
        if (anim) { cancelAnimationFrame(anim); anim = null; }
        size();
        settle(nav.querySelector('.sectab.on'));
    }

    reset();
    // Fonts load after first paint and change the label widths under the strip.
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(reset);
    }
    window.addEventListener('resize', reset);
}

document.addEventListener('DOMContentLoaded', startSectionTabs);
