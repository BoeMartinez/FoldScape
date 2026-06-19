/**
 * FoldScape - Main JavaScript
 * Loads repos.json and renders the dashboard
 */

// Category colors — semantic / "what kids would pick"
const CATEGORY_COLORS = {
    'Infrastructure': '#2563eb',   // blueprint blue — pipes, structure, foundations
    'Core Methods':   '#16a34a',   // engine green — core, alive, running
    'Applications':   '#f97316',   // product orange — user-facing, polished output
    'Uncategorized':  '#94a3b8'    // neutral slate — the misc folder
};

// Load and render data
function init() {
    // Use embedded data from window.REPOS_DATA (set in index.html)
    if (window.REPOS_DATA) {
        renderDashboard(window.REPOS_DATA);
    } else {
        console.error('No data found. REPOS_DATA not embedded in page.');
        document.getElementById('top-table-body').innerHTML =
            '<tr><td colspan="4">Error: No data loaded.</td></tr>';
    }
}

function renderDashboard(repos) {
    // Update stats
    renderStats(repos);

    // Render category chart
    renderCategoryChart(repos);

    // Render top repos table
    renderTopRepos(repos);

    // Render trending table
    renderTrendingRepos(repos);

    // Update timestamp from actual data collection date
    const collectedAt = window.REPOS_METADATA?.collected_at;
    if (collectedAt) {
        document.getElementById('last-updated').textContent = new Date(collectedAt).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } else {
        document.getElementById('last-updated').textContent = 'Unknown';
    }
}

function renderStats(repos) {
    const total = repos.length;
    const trending = repos.filter(r => r.tracking?.trending).length;
    const totalStars = repos.reduce((sum, r) => sum + (r.metadata?.stars || 0), 0);

    document.getElementById('total-repos').textContent = total;
    document.getElementById('trending-count').textContent = trending;
    document.getElementById('total-stars').textContent = formatNumber(totalStars);
}

function renderCategoryChart(repos) {
    // Premium donut — radial gradients that follow the arc, depth, center anchor
    const categoryCounts = {};
    repos.forEach(repo => {
        const category = repo.classification?.category || 'Uncategorized';
        categoryCounts[category] = (categoryCounts[category] || 0) + 1;
    });

    const labels = Object.keys(categoryCounts);
    const data = Object.values(categoryCounts);
    const total = data.reduce((a, b) => a + b, 0);
    const colors = labels.map(label => CATEGORY_COLORS[label] || '#94a3b8');

    const canvas = document.getElementById('category-chart');
    const ctx = canvas.getContext('2d');

    function mixHex(a, b, t) {
        const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
        const ar = (pa >> 16) & 255, ag = (pa >> 8) & 255, ab = pa & 255;
        const br = (pb >> 16) & 255, bg = (pb >> 8) & 255, bb = pb & 255;
        const r = Math.round(ar + (br - ar) * t);
        const g = Math.round(ag + (bg - ag) * t);
        const c = Math.round(ab + (bb - ab) * t);
        return `rgb(${r}, ${g}, ${c})`;
    }

    // Shift lightness in HSL space — keeps hue and saturation intact (no muddying).
    // delta is in [-1, 1]; negative = darker, positive = lighter.
    function shadeHex(hex, delta) {
        const r = parseInt(hex.slice(1, 3), 16) / 255;
        const g = parseInt(hex.slice(3, 5), 16) / 255;
        const b = parseInt(hex.slice(5, 7), 16) / 255;
        const max = Math.max(r, g, b), min = Math.min(r, g, b);
        let h = 0, s, l = (max + min) / 2;
        if (max !== min) {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            switch (max) {
                case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                case g: h = (b - r) / d + 2; break;
                case b: h = (r - g) / d + 4; break;
            }
            h /= 6;
        } else { s = 0; }
        l = Math.max(0, Math.min(1, l + delta));
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        let r2, g2, b2;
        if (s === 0) { r2 = g2 = b2 = l; }
        else {
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r2 = hue2rgb(p, q, h + 1/3);
            g2 = hue2rgb(p, q, h);
            b2 = hue2rgb(p, q, h - 1/3);
        }
        return `rgb(${Math.round(r2*255)}, ${Math.round(g2*255)}, ${Math.round(b2*255)})`;
    }

    // Plugin: assign radial gradient per arc just before drawing.
    // Gradient sweeps from darker (inner) → richer (mid) → lighter (outer),
    // so every segment shows depth on its inner edge and shine on its outer edge.
    const radialFills = {
        id: 'radialFills',
        beforeDatasetsDraw(chart) {
            const meta = chart.getDatasetMeta(0);
            const arcs = meta.data;
            if (!arcs || !arcs.length) return;
            const first = arcs[0];
            if (!first.innerRadius || !first.outerRadius) return;
            const cx = first.x;
            const cy = first.y;
            const innerR = first.innerRadius;
            const outerR = first.outerRadius;
            const ctx = chart.ctx;

            arcs.forEach((arc, i) => {
                const hex = colors[i] || '#94a3b8';
                const g = ctx.createRadialGradient(cx, cy, innerR * 0.92, cx, cy, outerR * 1.04);
                g.addColorStop(0.00, hex);                    // brand hue at inner edge — no darkening
                g.addColorStop(1.00, shadeHex(hex, +0.10));   // gentle highlight toward outer edge
                arc.options.backgroundColor = g;
            });
        }
    };

    // Center-text plugin: total count + label in donut hole
    const centerText = {
        id: 'centerText',
        afterDraw(chart) {
            const { ctx, chartArea } = chart;
            if (!chartArea) return;
            const meta = chart.getDatasetMeta(0);
            const arcs = meta.data;
            if (!arcs.length) return;
            const cx = arcs[0].x;
            const cy = arcs[0].y;
            ctx.save();
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#0a0a0a';
            ctx.font = '300 2.4rem "Inter", system-ui, sans-serif';
            ctx.fillText(total, cx, cy - 8);
            ctx.fillStyle = '#9ca3af';
            ctx.font = '500 0.65rem "Inter", system-ui, sans-serif';
            ctx.fillText('TOTAL TOOLS', cx, cy + 22);
            ctx.restore();
        }
    };

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors, // overwritten by radialFills plugin after layout
                borderWidth: 0,
                hoverBorderWidth: 0,
                hoverOffset: 14,
                borderRadius: 8,
                spacing: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 18,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        boxWidth: 8,
                        boxHeight: 8,
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11,
                            weight: 500
                        },
                        color: '#52525b'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(10,10,10,0.92)',
                    titleFont: { family: "'Inter', sans-serif", size: 12, weight: 600 },
                    bodyFont:  { family: "'Inter', sans-serif", size: 12 },
                    padding: 12,
                    cornerRadius: 10,
                    displayColors: true,
                    boxPadding: 4
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1100,
                easing: 'easeOutQuart'
            }
        },
        plugins: [radialFills, centerText]
    });
}

function renderTopRepos(repos) {
    const sorted = [...repos].sort((a, b) =>
        (b.metadata?.stars || 0) - (a.metadata?.stars || 0)
    );

    const top10 = sorted.slice(0, 10);
    const tbody = document.getElementById('top-table-body');

    tbody.innerHTML = top10.map(repo => {
        const name = repo.metadata?.name || repo.repo_id;
        const url = repo.metadata?.url || '#';
        const category = repo.classification?.category || 'Uncategorized';
        const categoryClass = category.toLowerCase().replace(' ', '-');
        const stars = repo.metadata?.stars || 0;
        const license = formatLicense(repo.metadata?.license);
        const age = formatAge(repo.metadata?.created_at);
        const trending = repo.tracking?.trending;

        return `
            <tr>
                <td>
                    <a href="${url}" target="_blank">${name}</a>
                    ${trending ? '<span class="trending-badge">TRENDING</span>' : ''}
                </td>
                <td><span class="category-badge ${categoryClass}">${category}</span></td>
                <td class="stars">${formatNumber(stars)}</td>
                <td>${license}</td>
                <td>${age}</td>
            </tr>
        `;
    }).join('');
}

function renderTrendingRepos(repos) {
    const trending = repos
        .filter(r => r.tracking?.trending || r.tracking?.star_velocity_7d > 10)
        .sort((a, b) => (b.tracking?.star_velocity_7d || 0) - (a.tracking?.star_velocity_7d || 0))
        .slice(0, 5);

    const tbody = document.getElementById('trending-table-body');

    if (trending.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">No trending repos this week</td></tr>';
        return;
    }

    tbody.innerHTML = trending.map(repo => {
        const name = repo.metadata?.name || repo.repo_id;
        const url = repo.metadata?.url || '#';
        const category = repo.classification?.category || 'Uncategorized';
        const categoryClass = category.toLowerCase().replace(' ', '-');
        const velocity = repo.tracking?.star_velocity_7d || 0;

        return `
            <tr>
                <td><a href="${url}" target="_blank">${name}</a></td>
                <td><span class="category-badge ${categoryClass}">${category}</span></td>
                <td class="stars">+${velocity} stars</td>
            </tr>
        `;
    }).join('');
}

function formatNumber(num) {
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
}

function formatLicense(license) {
    if (!license) return '—';
    // Shorten common license names
    const shortNames = {
        'MIT License': 'MIT',
        'Apache License 2.0': 'Apache 2.0',
        'GNU General Public License v3.0': 'GPL-3.0',
        'GNU General Public License v2.0': 'GPL-2.0',
        'BSD 3-Clause "New" or "Revised" License': 'BSD-3',
        'BSD 2-Clause "Simplified" License': 'BSD-2',
        'Mozilla Public License 2.0': 'MPL-2.0',
        'GNU Lesser General Public License v3.0': 'LGPL-3.0',
        'The Unlicense': 'Unlicense'
    };
    return shortNames[license] || license;
}

function formatAge(createdAt) {
    if (!createdAt) return '—';
    const created = new Date(createdAt);
    const now = new Date();
    const months = Math.floor((now - created) / (1000 * 60 * 60 * 24 * 30));

    if (months < 1) return '<1 mo';
    if (months < 12) return `${months} mo`;

    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;

    if (remainingMonths === 0) return `${years}y`;
    return `${years}y ${remainingMonths}mo`;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
