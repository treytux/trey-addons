odoo.define('stock_barcodes_dummy_label.BasicController', function (require) {
    'use strict';

    const BasicController = require('web.BasicController');
    const WebClientObj = require('web.web_client');
    const BarcodesDummyLabel = require('stock_barcodes_dummy_label.BarcodesDummyLabel');

    BasicController.include(BarcodesDummyLabel);
    BasicController.include({
        init: function() {
            this._super.apply(this, arguments);
            this._is_valid_barcode_model = this._isAllowedBarcodeModel(
                this.initialState.model
            );
            if (this._is_valid_barcode_model) {
                this._channel_dummy_label_sound = `barcodes_dummy_label_sound-${this.initialState.data.id}`;
                if (this.call('bus_service', 'isMasterTab')) {
                    this.call(
                        'bus_service',
                        'addChannel',
                        this._channel_dummy_label_sound,
                    )
                }
            }
        },
        destroy: function() {
            this._super.apply(this, arguments);
            if (this._is_valid_barcode_model) {
                if (this.$sound_ok) {
                    this.$sound_ok.remove();
                }
                if (this.$sound_error) {
                    this.$sound_error.remove();
                }
            }
        },
        onBusNotificationSound: function(notifications) {
            for (const notif of notifications) {
                const [channel, message] = notif;
                if (channel === 'barcodes_dummy_label_sound-' + this.initialState.data.id) {
                    if (message.sound === 'ok') {
                        this.$sound_ok[0].play();
                    } else if (message.sound === 'error') {
                        this.$sound_error[0].play();
                    }
                }
            }
        },
        on_detach_callback: function() {
            this._super.apply(this, arguments);
            if (this._is_valid_barcode_model) {
                this.call(
                    "bus_service",
                    "off",
                    "notification",
                    this,
                    this.onBusNotificationSound,
                );
            }
        },
        on_attach_callback: function() {
            this._super.apply(this, arguments);
            if (this._is_valid_barcode_model) {
                this._appendDummyLabelSounds();
                this.call(
                    "bus_service",
                    "on",
                    "notification",
                    this,
                    this.onBusNotificationSound,
                );
            }
        },
        _appendDummyLabelSounds: function() {
            this.$sound_ok = $("<audio>", {
                src: "/stock_barcodes_dummy_label/static/src/sounds/bell.wav",
                preload: "auto",
            });
            this.$sound_ok.appendTo('body');
            this.$sound_error = $("<audio>", {
                src: "/stock_barcodes_dummy_label/static/src/sounds/error.wav",
                preload: "auto",
            });
            this.$sound_error.appendTo('body');
        },
    });
});
