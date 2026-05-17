class LastFmUi {
    constructor() {
        this.root = document.querySelector('[data-lastfm-root]');
        this.currentKey = '';
        this.bindSearch();
        window.addEventListener('global-player-track-change', (event) => {
            this.loadTrack(event.detail.track);
        });
        if (window.globalPlayer?.currentTrack) {
            this.loadTrack(window.globalPlayer.currentTrack);
        }
    }

    bindSearch() {
        document.addEventListener('submit', (event) => {
            const form = event.target.closest('[data-lastfm-search-form]');
            if (!form) {
                return;
            }
            event.preventDefault();
            const input = form.querySelector('[data-lastfm-search-input]');
            this.search(input.value.trim());
        });
    }

    async loadTrack(track) {
        if (!track || !track.artist || !track.title) {
            this.setStatus('Запустите трек, чтобы загрузить данные Last.fm.');
            return;
        }
        if (document.body.dataset.staticExport === 'true') {
            this.setStatus('Last.fm API доступен в локальной Django-версии. На GitHub Pages backend endpoint недоступен.');
            return;
        }

        const key = `${track.artist}::${track.title}`;
        if (key === this.currentKey) {
            return;
        }
        this.currentKey = key;
        this.setStatus('Загружаю данные Last.fm...');

        try {
            const params = new URLSearchParams({artist: track.artist, track: track.title});
            const response = await fetch(`/api/lastfm/track/?${params.toString()}`);
            const payload = await response.json();
            if (!payload.ok) {
                this.setStatus(payload.message || 'Информация Last.fm недоступна.');
                this.clearPanels();
                return;
            }
            this.renderTrack(payload.data);
        } catch {
            this.setStatus('Не удалось подключиться к Last.fm endpoint.');
            this.clearPanels();
        }
    }

    async search(query) {
        const results = document.querySelector('[data-lastfm-results]');
        if (!results) {
            return;
        }
        if (!query) {
            results.innerHTML = '<p class="empty-state">Введите запрос для поиска.</p>';
            return;
        }
        if (document.body.dataset.staticExport === 'true') {
            results.innerHTML = '<p class="empty-state">Поиск Last.fm доступен в локальной Django-версии.</p>';
            return;
        }

        results.innerHTML = '<p class="empty-state">Ищу в Last.fm...</p>';
        try {
            const response = await fetch(`/api/lastfm/search/?${new URLSearchParams({q: query}).toString()}`);
            const payload = await response.json();
            if (!payload.ok) {
                results.innerHTML = `<p class="empty-state">${payload.message || 'Поиск недоступен.'}</p>`;
                return;
            }
            const items = payload.data.results || [];
            results.innerHTML = items.length
                ? items.map((item) => this.searchResultTemplate(item)).join('')
                : '<p class="empty-state">Ничего не найдено.</p>';
        } catch {
            results.innerHTML = '<p class="empty-state">Не удалось выполнить поиск Last.fm.</p>';
        }
    }

    renderTrack(data) {
        const track = data.track || {};
        const artist = data.artist || {};
        const image = track.image || artist.image || '';
        this.setStatus('Данные Last.fm загружены.');
        this.show('[data-lastfm-content]', true);
        this.text('[data-lastfm-title]', track.title || 'Без названия');
        this.text('[data-lastfm-artist]', track.artist || artist.artist || 'Неизвестный исполнитель');
        this.text('[data-lastfm-summary]', this.stripHtml(track.summary || artist.summary || 'Описание недоступно.'));
        this.text('[data-lastfm-listeners]', track.listeners ? `Слушателей: ${track.listeners}` : '');
        this.text('[data-lastfm-playcount]', track.playcount ? `Прослушиваний: ${track.playcount}` : '');
        this.renderImage(image);
        this.renderTags(track.tags || artist.tags || []);
        this.renderSimilar(data.similar_artists || []);
        this.renderTopTracks(data.top_tracks || []);
        if (image && window.globalPlayer) {
            window.globalPlayer.applyExternalCover(image);
        }
    }

    clearPanels() {
        this.show('[data-lastfm-content]', false);
        this.html('[data-lastfm-similar]', '');
        this.html('[data-lastfm-top-tracks]', '<p class="empty-state">Список появится после выбора трека.</p>');
    }

    renderImage(src) {
        const image = document.querySelector('[data-lastfm-image]');
        const placeholder = document.querySelector('[data-lastfm-image-placeholder]');
        if (!image || !placeholder) {
            return;
        }
        if (src) {
            image.src = src;
            image.hidden = false;
            placeholder.hidden = true;
        } else {
            image.removeAttribute('src');
            image.hidden = true;
            placeholder.hidden = false;
        }
    }

    renderTags(tags) {
        this.html('[data-lastfm-tags]', tags.length
            ? tags.slice(0, 6).map((tag) => `<span>${this.escape(tag)}</span>`).join('')
            : '<span>жанры не найдены</span>');
    }

    renderSimilar(artists) {
        this.html('[data-lastfm-similar]', artists.length
            ? `<h3>Похожие исполнители</h3><div class="lastfm-tags">${artists.map((item) => `<span>${this.escape(item.name)}</span>`).join('')}</div>`
            : '');
    }

    renderTopTracks(tracks) {
        this.html('[data-lastfm-top-tracks]', tracks.length
            ? tracks.map((item) => `
                <article class="lastfm-top-item">
                    <strong>${this.escape(item.title)}</strong>
                    <span>${item.playcount ? `Прослушиваний: ${this.escape(item.playcount)}` : this.escape(item.artist || '')}</span>
                    <button class="ghost-button" type="button" data-lastfm-fill="${this.escape(`${item.artist} ${item.title}`)}">Показать информацию</button>
                </article>
            `).join('')
            : '<p class="empty-state">Популярные треки не найдены.</p>');

        document.querySelectorAll('[data-lastfm-fill]').forEach((button) => {
            button.onclick = () => {
                const input = document.querySelector('[data-lastfm-search-input]');
                if (input) {
                    input.value = button.dataset.lastfmFill;
                    this.search(input.value);
                }
            };
        });
    }

    searchResultTemplate(item) {
        const image = item.image
            ? `<img src="${this.escape(item.image)}" alt="">`
            : '<span></span>';
        return `
            <article class="lastfm-result">
                <div class="lastfm-result-image">${image}</div>
                <div>
                    <strong>${this.escape(item.title)}</strong>
                    <span>${this.escape(item.artist)}</span>
                    <small>${item.listeners ? `Слушателей: ${this.escape(item.listeners)}` : ''}</small>
                </div>
            </article>
        `;
    }

    setStatus(message) {
        this.text('[data-lastfm-status]', message);
    }

    text(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value || '';
        }
    }

    html(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.innerHTML = value;
        }
    }

    show(selector, visible) {
        const element = document.querySelector(selector);
        if (element) {
            element.hidden = !visible;
        }
    }

    stripHtml(value) {
        return String(value || '').replace(/<[^>]+>/g, '');
    }

    escape(value) {
        return String(value || '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }
}

function bootLastFm() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => new LastFmUi(), {once: true});
    } else {
        new LastFmUi();
    }
}

bootLastFm();
