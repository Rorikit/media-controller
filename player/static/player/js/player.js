function initTrackSearch() {
    const searchInput = document.querySelector('[data-track-search]');
    const searchSummary = document.querySelector('[data-search-summary]');
    if (!searchInput) {
        return;
    }

    searchInput.oninput = () => {
        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        document.querySelectorAll('[data-track]').forEach((track) => {
            const haystack = `${track.dataset.title || ''} ${track.dataset.artist || ''}`.toLowerCase();
            const visible = haystack.includes(query);
            track.hidden = !visible;
            if (visible) {
                visibleCount += 1;
            }
        });

        if (searchSummary) {
            searchSummary.textContent = query
                ? `Найдено треков: ${visibleCount}`
                : 'Показаны все треки';
        }
    };
}

window.initPageEnhancements = function initPageEnhancements() {
    initTrackSearch();
};

document.addEventListener('DOMContentLoaded', () => {
    window.initPageEnhancements();
});
