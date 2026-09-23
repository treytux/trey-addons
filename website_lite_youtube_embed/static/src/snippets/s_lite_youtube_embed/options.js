/** @odoo-module **/

import options from 'web_editor.snippets.options';
function getYoutubeId(url) {
    if (!url) {
        return '';
    }
    const cleanUrl = url.trim();
    const embedMatch = cleanUrl.match(/youtube\.com\/embed\/([^?&#/]+)/i);
    if (embedMatch && embedMatch[1]) {
        return embedMatch[1];
    }
    const watchMatch = cleanUrl.match(/[?&]v=([^?&#/]+)/i);
    if (watchMatch && watchMatch[1]) {
        return watchMatch[1];
    }
    const shortMatch = cleanUrl.match(/youtu\.be\/([^?&#/]+)/i);
    return shortMatch && shortMatch[1] ? shortMatch[1] : '';
}
function getYoutubeEmbedUrl(videoId) {
    return `//www.youtube.com/embed/${videoId}?rel=0&autoplay=0`;
}
options.registry.LiteYoutubeEmbed = options.Class.extend({
    onBuilt() {
        this._updateLiteYoutube();
    },
    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        if (params.attributeName === 'youtubeUrl') {
            this._updateLiteYoutube();
        }
    },
    _updateLiteYoutube() {
        const targetEl = this.$target[0];
        const videoId = getYoutubeId(targetEl.dataset.youtubeUrl || '');
        if (!videoId) {
            return;
        }
        targetEl.dataset.youtubeUrl = getYoutubeEmbedUrl(videoId);
        const oldLiteEl = targetEl.querySelector('lite-youtube');
        const newLiteEl = document.createElement('lite-youtube');
        newLiteEl.setAttribute('videoid', videoId);
        newLiteEl.setAttribute(
            'style',
            'background-color: #000; position: absolute; top: 0; left: 0; '
            + 'width: 100%; height: 100%;'
        );
        if (oldLiteEl) {
            oldLiteEl.replaceWith(newLiteEl);
        } else {
            const playerEl = targetEl.querySelector('.s_lite_youtube_embed_player');
            if (!playerEl) {
                return;
            }
            playerEl.append(newLiteEl);
        }
    },
});
export default {
    LiteYoutubeEmbed: options.registry.LiteYoutubeEmbed,
};
