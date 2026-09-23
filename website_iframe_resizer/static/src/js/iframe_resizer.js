odoo.define('website_iframe_resizer.resizer', function (require) {
    'use strict';

    require('web.dom_ready');
    const selector = 'iframe.js_wir_iframe, .js_wir_container iframe';
    const pendingSelector = 'iframe.js_wir_pending';
    const initialized = new WeakSet();
    const options = {
        checkOrigin: false,
        scrolling: false,
        enablePublicMethods: true,
        closedCallback: function () {},
        initCallback: function () {},
        messageCallback: function () {},
        resizedCallback: function () {},
    };
    let configured = false;
    let started = false;

    function initialize() {
        const pending = Array.from(document.querySelectorAll(selector))
            .filter(iframe => !initialized.has(iframe));
        if (!pending.length && configured) {
            return;
        }
        pending.forEach(iframe => iframe.classList.add('js_wir_pending'));
        try {
            window.iFrameResize(options, pendingSelector);
            pending.forEach(iframe => initialized.add(iframe));
            configured = true;
        } finally {
            pending.forEach(iframe => iframe.classList.remove('js_wir_pending'));
        }
    }

    function start() {
        if (started) {
            return;
        }
        started = true;
        initialize();
        const observer = new MutationObserver(function (mutations) {
            if (mutations.some(mutation => mutation.addedNodes.length)) {
                initialize();
            }
        });
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true,
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start, {once: true});
    } else {
        start();
    }
    return {initialize: initialize};
});
