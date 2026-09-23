/** @odoo-module **/

import publicWidget from 'web.public.widget';
import {loadJS} from '@web/core/assets';

const GOOGLE_TRANSLATE_URL =
    'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';

let googleTranslateLoad;

function initializeGoogleTranslate() {
    if (!window.google || !window.google.translate) {
        return;
    }
    document.querySelectorAll('.wgt_widget').forEach((element) => {
        if (element.dataset.googleTranslateInitialized) {
            return;
        }
        new window.google.translate.TranslateElement({
            pageLanguage: element.dataset.pageLanguage,
            includedLanguages: element.dataset.includedLanguages,
            layout: window.google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false,
        }, element.id);
        element.dataset.googleTranslateInitialized = 'true';
    });
}

window.googleTranslateElementInit = initializeGoogleTranslate;

publicWidget.registry.GoogleTranslate = publicWidget.Widget.extend({
    selector: '.wgt_widget',
    disabledInEditableMode: false,

    start() {
        const result = this._super(...arguments);
        googleTranslateLoad = googleTranslateLoad || loadJS(GOOGLE_TRANSLATE_URL);
        return Promise.resolve(result).then(() => googleTranslateLoad)
            .then(() => initializeGoogleTranslate())
            .catch(() => undefined);
    },
});
