/**
 * FoldScape - Tools Page JavaScript
 * Displays all repos with filtering and sorting
 */

let allRepos = [];
let filteredRepos = [];
let currentSort = { field: 'stars', dir: 'desc' };

function init() {
    if (window.REPOS_DATA && window.REPOS_DATA.length > 0) {
        allRepos = window.REPOS_DATA;
        populateLanguageFilter();
        applyFilters();
        setupEventListeners();
    } else {
        document.getElementById('tools-table-body').innerHTML =
            '<tr><td colspan="6">No data loaded.</td></tr>';
    }
}

function populateLanguageFilter() {
    const languages = new Set();
    allRepos.forEach(r => {
        if (r.metadata?.language) {
            languages.add(r.metadata.language);
        }
    });

    const select = document.getElementById('language-filter');
    Array.from(languages).sort().forEach(lang => {
        const option = document.createElement('option');
        option.value = lang;
        option.textContent = lang;
        select.appendChild(option);
    });
}

function setupEventListeners() {
    document.getElementById('search-input').addEventListener('input', applyFilters);
    document.getElementById('category-filter').addEventListener('change', applyFilters);
    document.getElementById('language-filter').addEventListener('change', applyFilters);

    document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const field = btn.dataset.sort;
            if (currentSort.field === field) {
                currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.field = field;
                currentSort.dir = 'desc';
            }

            document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('asc', 'desc'));
            btn.classList.add(currentSort.dir);

            applyFilters();
        });
    });
}

function applyFilters() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const categoryFilter = document.getElementById('category-filter').value;
    const languageFilter = document.getElementById('language-filter').value;

    filteredRepos = allRepos.filter(repo => {
        const name = (repo.metadata?.name || '').toLowerCase();
        const desc = (repo.metadata?.description || '').toLowerCase();
        const category = repo.classification?.category || 'Uncategorized';
        const language = repo.metadata?.language || '';

        const matchesSearch = !searchTerm || name.includes(searchTerm) || desc.includes(searchTerm);
        const matchesCategory = !categoryFilter || category === categoryFilter;
        const matchesLanguage = !languageFilter || language === languageFilter;

        return matchesSearch && matchesCategory && matchesLanguage;
    });

    sortRepos();
    renderTable();
    updateStats();
}

function sortRepos() {
    filteredRepos.sort((a, b) => {
        let aVal, bVal;

        switch (currentSort.field) {
            case 'name':
                aVal = (a.metadata?.name || '').toLowerCase();
                bVal = (b.metadata?.name || '').toLowerCase();
                break;
            case 'stars':
                aVal = a.metadata?.stars || 0;
                bVal = b.metadata?.stars || 0;
                break;
            case 'updated':
                aVal = a.metadata?.last_updated || '';
                bVal = b.metadata?.last_updated || '';
                break;
            default:
                return 0;
        }

        if (aVal < bVal) return currentSort.dir === 'asc' ? -1 : 1;
        if (aVal > bVal) return currentSort.dir === 'asc' ? 1 : -1;
        return 0;
    });
}

function renderTable() {
    const tbody = document.getElementById('tools-table-body');

    if (filteredRepos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No tools match your filters.</td></tr>';
        return;
    }

    tbody.innerHTML = filteredRepos.map(repo => {
        const name = repo.metadata?.name || repo.repo_id;
        const url = repo.metadata?.url || '#';
        const desc = repo.metadata?.description || 'No description';
        const stars = repo.metadata?.stars || 0;
        const category = repo.classification?.category || 'Uncategorized';
        const categoryClass = category.toLowerCase().replace(' ', '-');
        const language = repo.metadata?.language || '-';
        const updated = formatDate(repo.metadata?.last_updated);

        return `
            <tr>
                <td>
                    <a href="${url}" target="_blank" class="repo-name">${escapeHtml(name)}</a>
                </td>
                <td>
                    <div class="repo-desc" title="${escapeHtml(desc)}">${escapeHtml(desc)}</div>
                </td>
                <td class="stars">${formatNumber(stars)}</td>
                <td><span class="category-badge ${categoryClass}">${category}</span></td>
                <td><span class="lang-badge">${language}</span></td>
                <td>${updated}</td>
            </tr>
        `;
    }).join('');
}

function updateStats() {
    document.getElementById('showing-count').textContent = filteredRepos.length;
    document.getElementById('total-count').textContent = allRepos.length;

    const totalStars = filteredRepos.reduce((sum, r) => sum + (r.metadata?.stars || 0), 0);
    document.getElementById('total-stars').textContent = formatNumber(totalStars);
}

function formatNumber(num) {
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
}

function formatDate(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', init);
