'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const library = fs.readFileSync(path.join(root,
    'static/src/lib/iframeResizer/iframeResizer.js'), 'utf8');
const service = fs.readFileSync(path.join(root,
    'static/src/js/iframe_resizer.js'), 'utf8');

function fixture(readyState = 'complete') {
    const frames = [];
    const listeners = {};
    const domListeners = {};
    const observers = [];
    const document = {
        readyState,
        documentElement: {},
        getElementById: id => frames.find(frame => frame.id === id) || null,
        addEventListener: (name, callback) => {domListeners[name] = callback;},
        querySelectorAll: selector => frames.filter(frame => {
            if (selector === 'iframe') {
                return true;
            }
            if (selector === 'iframe.js_wir_pending') {
                return frame.classes.has('js_wir_pending');
            }
            return frame.classes.has('js_wir_iframe') || frame.container;
        }),
    };
    const window = {
        addEventListener: (name, callback) => {
            (listeners[name] ||= []).push(callback);
        },
        scrollTo: () => {},
    };
    let exported;
    const context = vm.createContext({
        window, document,
        MutationObserver: class {
            constructor(callback) { this.callback = callback; }
            observe() { observers.push(this); }
        },
        odoo: {define: (name, factory) => { exported = factory(() => {}); }},
    });
    function frame(id, marked = true, container = false) {
        const classes = new Set(marked ? ['js_wir_iframe'] : []);
        const messages = [];
        const loads = [];
        const element = {
            id, classes, container, messages, loads,
            tagName: 'IFRAME', src: 'https://supplier.example/frame', style: {},
            classList: {
                add: name => classes.add(name),
                remove: name => classes.delete(name),
            },
            contentWindow: {postMessage: message => messages.push(message)},
            addEventListener: (name, callback) => loads.push(callback),
        };
        frames.push(element);
        return element;
    }
    return {
        frame, listeners, observers,
        loadLibrary: () => vm.runInContext(library, context),
        loadService: () => vm.runInContext(service, context),
        initialize: () => exported.initialize(),
        resize: () => window.iFrameResize({checkOrigin: false}, 'iframe'),
        ready: () => domListeners.DOMContentLoaded(),
        mutation: addedNodes => observers.forEach(observer =>
            observer.callback([{addedNodes}])),
        message: (id, type = 'message', height = 0) => {
            const event = {
                data: `[iFrameSizer]${id}:${height}:200:${type}:hello`,
                origin: 'https://supplier.example',
            };
            listeners.message.forEach(callback => callback(event));
        },
    };
}

test('two vendor copies reproduce the reported missing callback', () => {
    const page = fixture();
    page.frame('nexmart');
    page.loadLibrary();
    page.loadLibrary();
    page.resize();
    assert.equal(page.listeners.message.length, 2);
    assert.throws(() => page.message('nexmart'),
        /messageCallback is not a function/);
});

test('one shared service handles messages and resizes both integrations', () => {
    const page = fixture();
    const nexmart = page.frame('nexmart');
    const raiz = page.frame('raiz', false, true);
    const unrelated = page.frame('unrelated', false);
    page.loadLibrary();
    page.loadService();
    assert.equal(page.listeners.message.length, 1);
    for (const frame of [nexmart, raiz]) {
        assert.equal(frame.loads.length, 1);
        assert.equal(frame.messages.length, 1);
        assert.match(frame.messages[0], /:32:true:true:/);
        page.message(frame.id);
        page.message(frame.id, 'init', 420);
        assert.equal(frame.style.height, '420px');
        assert.equal(frame.scrolling, 'no');
    }
    assert.equal(unrelated.loads.length, 0);
    page.initialize();
    page.mutation([{}]);
    assert.equal(nexmart.loads.length, 1);
    assert.equal(raiz.loads.length, 1);
});

test('waits for DOM and initializes late container frames once', () => {
    const page = fixture('loading');
    const nexmart = page.frame('nexmart');
    page.loadLibrary();
    page.loadService();
    assert.equal(nexmart.messages.length, 0);
    page.ready();
    const raiz = page.frame('raiz', false, true);
    page.mutation([raiz]);
    assert.equal(raiz.messages.length, 1);
    page.message('raiz', 'resize', 650);
    assert.equal(raiz.style.height, '650px');
    page.mutation([raiz]);
    page.mutation([]);
    assert.equal(raiz.loads.length, 1);
    assert.equal(nexmart.loads.length, 1);
});

test('empty initial DOM can receive an asynchronous provider iframe', () => {
    const page = fixture();
    page.loadLibrary();
    page.loadService();
    assert.equal(page.observers.length, 1);
    const raiz = page.frame('raiz', false, true);
    page.message('raiz');
    page.mutation([raiz]);
    page.message('raiz', 'resize', 300);
    assert.equal(raiz.style.height, '300px');
    assert.equal(raiz.loads.length, 1);
});
