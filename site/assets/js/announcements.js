/* Announcements — entries with no repository, so no stars to rank by.
 *
 * Ordered by publication date, newest first. The collector already decided
 * relevance; this only draws what it kept.
 *
 * Built as DOM nodes rather than an HTML string on purpose: titles and
 * summaries come straight out of third-party feeds and carry ampersands,
 * quotes and the occasional stray bracket.
 */
function renderAnnouncements() {
    'use strict';

    var SHOWN = 12;

    var list = document.getElementById('announcements');
    if (!list) return;

    var items = (window.ANNOUNCEMENTS_DATA || []).slice();

    function when(item) {
        var raw = item.published || item.first_seen;
        var t = raw ? Date.parse(raw) : NaN;
        return isNaN(t) ? 0 : t;
    }

    items.sort(function (a, b) { return when(b) - when(a); });

    var count = document.getElementById('announce-count');
    if (count) count.textContent = items.length ? String(items.length) : '';

    list.textContent = '';

    if (!items.length) {
        var empty = document.createElement('p');
        empty.className = 'announce-empty';
        empty.textContent = 'No announcements collected yet';
        list.appendChild(empty);
        return;
    }

    function dateLabel(ms) {
        if (!ms) return '';
        var d = new Date(ms);
        var days = Math.floor((Date.now() - ms) / 86400000);
        if (days <= 0) return 'today';
        if (days === 1) return 'yesterday';
        if (days < 7) return days + 'd ago';
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    function draw(item) {
        var card = document.createElement('article');
        card.className = 'announce';

        var head = document.createElement('h3');
        var link = document.createElement('a');
        link.href = item.url || '#';
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = item.title || item.url || 'Untitled';
        head.appendChild(link);
        card.appendChild(head);

        var meta = document.createElement('p');
        meta.className = 'announce-meta';

        var source = document.createElement('span');
        source.className = 'announce-source';
        source.textContent = item.source || '';
        meta.appendChild(source);

        var label = dateLabel(when(item));
        if (label) {
            var date = document.createElement('span');
            date.className = 'announce-date';
            date.textContent = label;
            meta.appendChild(date);
        }

        card.appendChild(meta);
        list.appendChild(card);
    }

    items.slice(0, SHOWN).forEach(draw);

    // The tab counts every entry, so the rest are one tap away rather than
    // missing. They open in place, under the ones already shown.
    if (items.length > SHOWN) {
        var more = document.createElement('button');
        more.type = 'button';
        more.className = 'announce-more';
        more.textContent = 'Show all ' + items.length;
        more.addEventListener('click', function () {
            list.removeChild(more);
            items.slice(SHOWN).forEach(draw);
        });
        list.appendChild(more);
    }
}

/* The data tag is written into the page by embed_data.py, which decides its
 * own position, so waiting for the document is what makes this independent
 * of whether the tag lands above or below this file. */
document.addEventListener('DOMContentLoaded', renderAnnouncements);

