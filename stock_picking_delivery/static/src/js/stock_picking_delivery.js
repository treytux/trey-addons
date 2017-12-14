(function () {
    'use strict';

    var website = openerp.website;
    var _t = openerp._t;
    website.ready().done(function() {
        website.stock_picking_delivery = {};
        website.stock_picking_delivery.StockPickingDelivery = openerp.Widget.extend({
            dom_ready: $.Deferred(),
            ready: function(){
                return this.dom_ready.then(function() {}).promise();
            },
            init: function (parent, options) {
                this.dom_ready.resolve();
                var self = this;
                this._super(parent);
                var $send = $('.js_spd_send_refuse'),
                    $attachSelector = $('.js_spd_attach_selector');
                $attachSelector.on('change', function (event) {
                    self.on_attach(this);
                });
                $send.on('click', function (event) {
                    event.preventDefault();
                    self.on_click(this);
                });
            },
            on_attach: function (attachSelector) {
                var files = attachSelector.files,
                    $fileList = $('.js_spd_file_list');
                $fileList.empty();
                $fileList.addClass('hidden');
                if (files.length > 1) {
                    $fileList.removeClass('hidden');
                    for (var i = 0; i < files.length; i++) {
                        $fileList.append('<li>' + files[i].name + '</li>');
                    }
                }
            },
            on_click: function (button) {
                var $form = $(button).closest('form'),
                    $reason = $('textarea[name="reason"]'),
                    $reasonWrapper = $reason.closest('.form-group');
                if (!$reason.val()){
                    $reasonWrapper.addClass('has-error');
                }
                else {
                    $form.submit();
                }
            },
        });
        website.if_dom_contains('form[name="refuse_delivery"]', function(){
            var stock_picking_delivery = new website.stock_picking_delivery.StockPickingDelivery();
        });
    });
})();
