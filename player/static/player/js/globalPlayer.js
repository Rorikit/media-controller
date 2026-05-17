class GlobalPlayerManager {
    constructor() {
        if (window.globalPlayer) {
            return window.globalPlayer;
        }

        this.storageKey = 'mediaController.globalPlayer';
        this.audio = document.querySelector('[data-global-audio]');
        this.currentTrack = null;
        this.currentIndex = -1;
        this.queue = [];
        this.isSeeking = false;

        if (!this.audio) {
            return;
        }

        this.restoreState();
        this.bindAudio();
        this.bindControls();
        this.bindNavigation();
        this.setStatus('Плеер готов');
        this.syncUi();
        window.globalPlayer = this;
    }

    formatTime(seconds) {
        if (!Number.isFinite(seconds)) {
            return '0:00';
        }
        const minutes = Math.floor(seconds / 60);
        const rest = Math.floor(seconds % 60).toString().padStart(2, '0');
        return `${minutes}:${rest}`;
    }

    getTrackFromCard(card) {
        return {
            title: card.dataset.title || 'Без названия',
            artist: card.dataset.artist || 'Неизвестный исполнитель',
            src: card.dataset.src || '',
            cover: card.dataset.cover || '',
        };
    }

    collectQueue() {
        return Array.from(document.querySelectorAll('[data-track]'))
            .filter((card) => !card.hidden)
            .map((card) => this.getTrackFromCard(card));
    }

    bindAudio() {
        this.audio.addEventListener('loadedmetadata', () => {
            const savedTime = Number(this.pendingTime || 0);
            if (savedTime && this.audio.duration) {
                this.audio.currentTime = Math.min(savedTime, this.audio.duration - 1);
                this.pendingTime = 0;
            }
            this.syncUi();
        });
        this.audio.addEventListener('timeupdate', () => {
            this.syncUi();
            this.saveState();
        });
        this.audio.addEventListener('play', () => {
            this.setStatus('');
            this.syncUi();
            this.saveState();
        });
        this.audio.addEventListener('pause', () => {
            this.syncUi();
            this.saveState();
        });
        this.audio.addEventListener('ended', () => this.next());
        this.audio.addEventListener('error', () => {
            this.setStatus('Аудиофайл не найден или не может быть воспроизведён.');
            this.syncUi();
        });
        window.addEventListener('beforeunload', () => this.saveState());
    }

    bindControls() {
        document.addEventListener('click', (event) => {
            const card = event.target.closest('[data-track]');
            if (!card || event.target.closest('form') || event.target.closest('select')) {
                return;
            }

            const cards = Array.from(document.querySelectorAll('[data-track]')).filter((item) => !item.hidden);
            this.queue = cards.map((item) => this.getTrackFromCard(item));
            this.currentIndex = cards.indexOf(card);
            this.playTrack(this.queue[this.currentIndex]);
        });

        document.addEventListener('click', (event) => {
            if (event.target.closest('[data-global-play], [data-play]')) {
                this.toggle();
            }
            if (event.target.closest('[data-global-prev], [data-prev]')) {
                this.previous();
            }
            if (event.target.closest('[data-global-next], [data-next]')) {
                this.next();
            }
        });

        document.addEventListener('input', (event) => {
            if (event.target.matches('[data-global-volume], [data-volume]')) {
                this.audio.volume = Number(event.target.value);
                this.syncUi();
                this.saveState();
            }
            if (event.target.matches('[data-global-progress], [data-progress]')) {
                this.isSeeking = true;
                if (this.audio.duration) {
                    this.audio.currentTime = (Number(event.target.value) / 100) * this.audio.duration;
                }
            }
        });

        document.addEventListener('change', (event) => {
            if (event.target.matches('[data-global-progress], [data-progress]')) {
                this.isSeeking = false;
                this.saveState();
            }
        });
    }

    bindNavigation() {
        document.addEventListener('click', (event) => {
            const link = event.target.closest('a[href]');
            if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || !this.shouldHandleLink(link)) {
                return;
            }
            event.preventDefault();
            this.navigate(link.href);
        });

        document.addEventListener('submit', (event) => {
            const form = event.target.closest('form');
            if (!form || !this.shouldHandleForm(form)) {
                return;
            }
            event.preventDefault();
            if (document.body.dataset.staticExport === 'true') {
                this.setStatus('На GitHub Pages плейлисты доступны только для просмотра. Редактирование работает в локальной Django-версии.');
                return;
            }
            this.submitForm(form);
        });

        window.addEventListener('popstate', () => this.navigate(window.location.href, false));
    }

    shouldHandleLink(link) {
        const url = new URL(link.href, window.location.href);
        return url.origin === window.location.origin
            && !link.target
            && !url.pathname.startsWith('/admin/')
            && !url.pathname.startsWith('/media/')
            && !url.pathname.startsWith('/static/');
    }

    shouldHandleForm(form) {
        const url = new URL(form.action || window.location.href, window.location.href);
        return url.origin === window.location.origin && !url.pathname.startsWith('/admin/');
    }

    async navigate(url, push = true) {
        try {
            const response = await fetch(url, {headers: {'X-Requested-With': 'fetch'}});
            const html = await response.text();
            this.replacePage(html, response.url, push);
        } catch {
            window.location.href = url;
        }
    }

    async submitForm(form) {
        try {
            const response = await fetch(form.action || window.location.href, {
                method: form.method || 'POST',
                body: new FormData(form),
                headers: {'X-Requested-With': 'fetch'},
            });
            const html = await response.text();
            this.replacePage(html, response.url, true);
        } catch {
            form.submit();
        }
    }

    replacePage(html, url, push) {
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const nextShell = doc.querySelector('.app-shell');
        const shell = document.querySelector('.app-shell');
        if (!nextShell || !shell) {
            window.location.href = url;
            return;
        }

        shell.innerHTML = nextShell.innerHTML;
        document.title = doc.title;
        if (push && window.location.href !== url) {
            window.history.pushState({}, '', url);
        }
        if (window.initPageEnhancements) {
            window.initPageEnhancements();
        }
        this.syncUi();
    }

    playTrack(track) {
        if (!track) {
            this.setStatus('Нет доступных треков для воспроизведения.');
            return;
        }

        this.currentTrack = track;
        this.setStatus('Загружаю трек...');

        if (!track.src) {
            this.audio.removeAttribute('src');
            this.audio.load();
            this.setStatus('У выбранного трека нет аудиофайла.');
            this.syncUi();
            return;
        }

        const nextSrc = new URL(track.src, window.location.href).href;
        if (this.audio.src !== nextSrc) {
            this.audio.src = nextSrc;
            this.audio.load();
        }

        this.highlightActiveTrack();
        this.syncUi();
        this.saveState();
        this.audio.play().catch((error) => {
            this.setStatus(`Не удалось запустить аудио: ${error.name}`);
            this.syncUi();
        });
    }

    toggle() {
        if (!this.currentTrack) {
            this.queue = this.collectQueue();
            this.currentIndex = 0;
            this.playTrack(this.queue[0]);
            return;
        }

        if (this.audio.paused) {
            this.audio.play().catch((error) => {
                this.setStatus(`Не удалось продолжить воспроизведение: ${error.name}`);
            });
        } else {
            this.audio.pause();
        }
    }

    next() {
        if (!this.queue.length) {
            this.queue = this.collectQueue();
        }
        if (!this.queue.length) {
            return;
        }
        this.currentIndex = (this.currentIndex + 1 + this.queue.length) % this.queue.length;
        this.playTrack(this.queue[this.currentIndex]);
    }

    previous() {
        if (!this.queue.length) {
            this.queue = this.collectQueue();
        }
        if (!this.queue.length) {
            return;
        }
        this.currentIndex = (this.currentIndex - 1 + this.queue.length) % this.queue.length;
        this.playTrack(this.queue[this.currentIndex]);
    }

    setStatus(message) {
        document.querySelectorAll('[data-player-status], [data-bar-status]').forEach((item) => {
            item.textContent = message;
        });
    }

    updateCover(img, placeholder, cover) {
        if (!img || !placeholder) {
            return;
        }
        if (cover) {
            img.src = cover;
            img.hidden = false;
            placeholder.hidden = true;
        } else {
            img.removeAttribute('src');
            img.hidden = true;
            placeholder.hidden = false;
        }
    }

    syncUi() {
        const title = this.currentTrack ? this.currentTrack.title : 'Выберите трек';
        const artist = this.currentTrack ? this.currentTrack.artist : 'Музыка продолжит играть при переходах';
        const cover = this.currentTrack ? this.currentTrack.cover : '';
        const current = this.audio.currentTime || 0;
        const total = this.audio.duration || 0;
        const percent = total ? (current / total) * 100 : 0;
        const isPlaying = !this.audio.paused;

        document.querySelectorAll('[data-current-title], [data-bar-title]').forEach((item) => {
            item.textContent = title;
        });
        document.querySelectorAll('[data-current-artist], [data-bar-artist]').forEach((item) => {
            item.textContent = artist;
        });
        document.querySelectorAll('[data-current-time], [data-bar-current]').forEach((item) => {
            item.textContent = this.formatTime(current);
        });
        document.querySelectorAll('[data-duration], [data-bar-duration]').forEach((item) => {
            item.textContent = this.formatTime(total);
        });
        document.querySelectorAll('[data-global-progress], [data-progress]').forEach((item) => {
            if (!this.isSeeking) {
                item.value = percent;
            }
        });
        document.querySelectorAll('[data-global-volume], [data-volume]').forEach((item) => {
            item.value = this.audio.volume;
        });
        document.querySelectorAll('[data-global-play], [data-play]').forEach((button) => {
            button.textContent = isPlaying ? '⏸' : '▶';
        });
        document.querySelectorAll('[data-vinyl]').forEach((vinyl) => {
            vinyl.classList.toggle('playing', isPlaying);
        });
        document.querySelectorAll('[data-vinyl-cover]').forEach((img) => {
            this.updateCover(img, img.parentElement.querySelector('[data-vinyl-placeholder]'), cover);
        });
        this.updateCover(
            document.querySelector('[data-bar-cover-img]'),
            document.querySelector('[data-bar-cover-placeholder]'),
            cover,
        );
        this.highlightActiveTrack();
    }

    highlightActiveTrack() {
        document.querySelectorAll('[data-track]').forEach((card) => {
            card.classList.toggle('active', Boolean(this.currentTrack && card.dataset.src === this.currentTrack.src));
        });
    }

    saveState() {
        localStorage.setItem(this.storageKey, JSON.stringify({
            currentTrack: this.currentTrack,
            currentIndex: this.currentIndex,
            queue: this.queue,
            currentTime: this.audio.currentTime || 0,
            volume: this.audio.volume,
            paused: this.audio.paused,
        }));
    }

    restoreState() {
        let state = {};
        try {
            state = JSON.parse(localStorage.getItem(this.storageKey) || '{}');
        } catch {
            state = {};
        }

        this.queue = state.queue || [];
        this.currentIndex = Number.isInteger(state.currentIndex) ? state.currentIndex : -1;
        this.currentTrack = state.currentTrack || null;
        this.pendingTime = Number(state.currentTime || 0);
        this.audio.volume = Number(state.volume || 0.8);

        if (this.currentTrack && this.currentTrack.src) {
            this.audio.src = new URL(this.currentTrack.src, window.location.href).href;
            this.audio.load();
        }
    }
}

function bootGlobalPlayer() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => new GlobalPlayerManager(), {once: true});
    } else {
        new GlobalPlayerManager();
    }
}

bootGlobalPlayer();
