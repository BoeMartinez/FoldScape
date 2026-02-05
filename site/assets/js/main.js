/**
 * FoldScape - Main JavaScript
 * Loads repos.json and renders the dashboard
 */

// Category colors for chart
const CATEGORY_COLORS = {
    'Infrastructure': '#3b82f6',
    'Core Methods': '#22c55e',
    'Applications': '#f59e0b',
    'Uncategorized': '#94a3b8'
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

    // Update timestamp
    document.getElementById('last-updated').textContent = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function renderStats(repos) {
    const total = repos.length;
    const trending = repos.filter(r => r.tracking?.trending).length;
    const validated = repos.filter(r => r.domain_specific?.experimental_validation === true).length;
    const totalStars = repos.reduce((sum, r) => sum + (r.metadata?.stars || 0), 0);

    document.getElementById('total-repos').textContent = total;
    document.getElementById('trending-count').textContent = trending;
    document.getElementById('validated-count').textContent = validated;
    document.getElementById('total-stars').textContent = formatNumber(totalStars);
}

function renderCategoryChart(repos) {
    const categoryCounts = {};

    repos.forEach(repo => {
        const category = repo.classification?.category || 'Uncategorized';
        categoryCounts[category] = (categoryCounts[category] || 0) + 1;
    });

    const labels = Object.keys(categoryCounts);
    const data = Object.values(categoryCounts);
    const colors = labels.map(label => CATEGORY_COLORS[label] || '#94a3b8');

    const ctx = document.getElementById('category-chart').getContext('2d');

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            }
        }
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
        const gpu = repo.domain_specific?.gpu_requirement || '-';
        const trending = repo.tracking?.trending;

        return `
            <tr>
                <td>
                    <a href="${url}" target="_blank">${name}</a>
                    ${trending ? '<span class="trending-badge">TRENDING</span>' : ''}
                </td>
                <td><span class="category-badge ${categoryClass}">${category}</span></td>
                <td class="stars">${formatNumber(stars)}</td>
                <td>${gpu}</td>
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
