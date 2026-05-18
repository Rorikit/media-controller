class ThemeManager {
    constructor() {
        this.root = document.documentElement;
        this.fallbackColors = ['#33c27f', '#5b8cff', '#c06cff', '#ff8a5b', '#e05264'];
        this.currentColor = this.fallbackColors[0];
        this.bind();
        this.applyColor(this.currentColor);
    }

    bind() {
        window.addEventListener('global-player-track-change', (event) => {
            this.fromTrack(event.detail.track);
        });
        window.addEventListener('lastfm-metadata', (event) => {
            const {image, title, artist} = event.detail || {};
            this.fromCoverOrSeed(image, `${artist || ''}${title || ''}`);
        });
    }

    fromTrack(track) {
        if (!track) {
            return;
        }
        this.fromCoverOrSeed(track.cover, `${track.artist || ''}${track.title || ''}`);
    }

    fromCoverOrSeed(image, seed) {
        if (image) {
            this.extractColor(image)
                .then((color) => this.applyColor(color))
                .catch(() => this.applyColor(this.colorFromSeed(seed)));
            return;
        }
        this.applyColor(this.colorFromSeed(seed));
    }

    extractColor(src) {
        return new Promise((resolve, reject) => {
            const image = new Image();
            image.crossOrigin = 'anonymous';
            image.onload = () => {
                try {
                    const canvas = document.createElement('canvas');
                    const size = 32;
                    canvas.width = size;
                    canvas.height = size;
                    const context = canvas.getContext('2d', {willReadFrequently: true});
                    context.drawImage(image, 0, 0, size, size);
                    const data = context.getImageData(0, 0, size, size).data;
                    let r = 0;
                    let g = 0;
                    let b = 0;
                    let count = 0;
                    for (let i = 0; i < data.length; i += 4) {
                        const alpha = data[i + 3];
                        if (alpha < 120) {
                            continue;
                        }
                        const red = data[i];
                        const green = data[i + 1];
                        const blue = data[i + 2];
                        const brightness = (red + green + blue) / 3;
                        if (brightness < 24 || brightness > 232) {
                            continue;
                        }
                        r += red;
                        g += green;
                        b += blue;
                        count += 1;
                    }
                    if (!count) {
                        reject(new Error('No usable pixels'));
                        return;
                    }
                    resolve(this.rgbToHex(Math.round(r / count), Math.round(g / count), Math.round(b / count)));
                } catch (error) {
                    reject(error);
                }
            };
            image.onerror = reject;
            image.src = src;
        });
    }

    colorFromSeed(seed = '') {
        let hash = 0;
        for (const char of seed) {
            hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
        }
        return this.fallbackColors[hash % this.fallbackColors.length];
    }

    applyColor(hex) {
        const color = this.normalizeColor(hex);
        const rgb = this.hexToRgb(color);
        const soft = this.mix(rgb, {r: 255, g: 255, b: 255}, 0.18);
        const deep = this.mix(rgb, {r: 6, g: 8, b: 12}, 0.58);
        this.currentColor = color;

        requestAnimationFrame(() => {
            this.root.style.setProperty('--accent', color);
            this.root.style.setProperty('--accent-rgb', `${rgb.r}, ${rgb.g}, ${rgb.b}`);
            this.root.style.setProperty('--accent-soft', this.rgbToHex(soft.r, soft.g, soft.b));
            this.root.style.setProperty('--accent-deep', this.rgbToHex(deep.r, deep.g, deep.b));
            this.root.style.setProperty('--accent-glow', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.34)`);
            this.root.style.setProperty('--ambient-a', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.18)`);
            this.root.style.setProperty('--ambient-b', `rgba(${deep.r}, ${deep.g}, ${deep.b}, 0.72)`);
        });
    }

    normalizeColor(hex) {
        if (/^#[0-9a-f]{6}$/i.test(hex)) {
            return hex;
        }
        return this.fallbackColors[0];
    }

    hexToRgb(hex) {
        const value = hex.replace('#', '');
        return {
            r: parseInt(value.slice(0, 2), 16),
            g: parseInt(value.slice(2, 4), 16),
            b: parseInt(value.slice(4, 6), 16),
        };
    }

    rgbToHex(r, g, b) {
        return `#${[r, g, b].map((value) => value.toString(16).padStart(2, '0')).join('')}`;
    }

    mix(a, b, amount) {
        return {
            r: Math.round(a.r * (1 - amount) + b.r * amount),
            g: Math.round(a.g * (1 - amount) + b.g * amount),
            b: Math.round(a.b * (1 - amount) + b.b * amount),
        };
    }
}

function bootThemeManager() {
    if (window.themeManager) {
        return;
    }
    window.themeManager = new ThemeManager();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootThemeManager, {once: true});
} else {
    bootThemeManager();
}
