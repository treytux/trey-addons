/** @odoo-module **/

import options from 'web_editor.snippets.options';

function getVimeoId(url) {
    if (!url) {
        return '';
    }
    const cleanUrl = url.trim();
    const playerMatch = cleanUrl.match(/vimeo\.com\/video\/([^?&#/]+)/i);
    if (playerMatch && playerMatch[1]) {
        return playerMatch[1];
    }
    const urlMatch = cleanUrl.match(/vimeo\.com\/([^?&#/]+)/i);
    return urlMatch && urlMatch[1] ? urlMatch[1] : '';
}

function getVimeoEmbedUrl(videoId) {
    return `//player.vimeo.com/video/${videoId}`;
}

function getVimeoThumbnailUrl(videoId) {
    return `https://vumbnail.com/${videoId}.jpg`;
}

options.registry.LiteVimeoEmbed = options.Class.extend({
    onBuilt() {
        this._updateLiteVimeo();
    },

    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        if (params.attributeName === 'vimeoUrl') {
            this._updateLiteVimeo();
        }
    },

    _updateLiteVimeo() {
        const targetEl = this.$target[0];
        const videoId = getVimeoId(targetEl.dataset.vimeoUrl || '');
        if (!videoId) {
            return;
        }
        targetEl.dataset.vimeoUrl = getVimeoEmbedUrl(videoId);
        const oldLiteEl = targetEl.querySelector('lite-vimeo');
        const newLiteEl = document.createElement('lite-vimeo');
        newLiteEl.setAttribute('videoid', videoId);
        newLiteEl.setAttribute(
            'style',
            'background-color: #000; background-image: url('
            + `'${getVimeoThumbnailUrl(videoId)}'); background-size: cover; `
            + 'background-position: center; position: absolute; top: 0; '
            + 'left: 0; width: 100%; height: 100%;'
        );
        if (oldLiteEl) {
            oldLiteEl.replaceWith(newLiteEl);
        } else {
            const playerEl = targetEl.querySelector('.s_lite_vimeo_embed_player');
            if (!playerEl) {
                return;
            }
            playerEl.append(newLiteEl);
        }
    },
});

export default {
    LiteVimeoEmbed: options.registry.LiteVimeoEmbed,
};
