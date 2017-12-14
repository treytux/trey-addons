(function() {
    'use strict';
    var instance = openerp;
    var website = openerp.website;
    var _t = openerp._t;
    website.ready().done(function() {
        website.website_sale_checkout_agent = {};
        website.website_sale_checkout_agent.Addresses = openerp.Widget.extend({
            dom_ready: $.Deferred(),
            ready: function(){
                return this.dom_ready.then(function() {}).promise();
            },
            init: function (parent, options) {
                this.dom_ready.resolve();
                var self = this;
                this._super(parent);
                var $partner = $('select[name="partner_id"]');
                var $notes = $('textarea[name="note"]');
                self.hide_show_confirm_button($partner.val(), $notes.val())
                $partner.on('change', function(){
                    self.update_addresses($(this).val());
                    self.hide_show_confirm_button(
                        $(this).val(), $notes.val());
                });
                $notes.on('change', function(){
                    self.hide_show_confirm_button(
                        $partner.val(), $(this).val());
                });
            },
            update_addresses: function (partner_id) {
                var $billing = $('.js_wsca_billing_address'),
                    $billing_id = $('select[name="partner_invoice_id"]'),
                    $shipping = $('.js_wsca_shipping_address'),
                    $shipping_id = $('select[name="partner_shipping_id"]');
                if(partner_id == '' || partner_id == 'new-customer'){
                    $billing.addClass('hidden');
                    $shipping.addClass('hidden');
                } else {
                    $billing.removeClass('hidden');
                    $billing_id.find('option').hide().attr('disabled', 'disabled');
                    $billing_id.find('option[data-partner_id="' + partner_id + '"]').show().removeAttr('disabled');
                    $billing_id.find('option:not([disabled])').first().attr('selected', 'selected');
                    $shipping.removeClass('hidden');
                    $shipping_id.find('option').hide().attr('disabled', 'disabled');
                    $shipping_id.find('option[data-partner_id="' + partner_id + '"]').show().removeAttr('disabled');
                    $shipping_id.find('option:not([disabled])').first().attr('selected', 'selected');
                }
            },
            hide_show_confirm_button: function(partner, notes, button) {
                var $button = $('button[form="wsca_confirm"]');
                if (partner == 'new-customer'){
                    if (notes == '') {
                        $button.attr('disabled', 'disabled');
                        $('p[name="info-fill-notes"]').css('color', 'red');
                        $('p[name="info-fill-notes"]').show();
                    } else {
                        $button.removeAttr('disabled');
                        $('p[name="info-fill-notes"]').hide();
                    }
                } else {
                    $button.removeAttr('disabled');
                    $('p[name="info-fill-notes"]').hide();
                }
            },
        });

        openerp.website.if_dom_contains('.js_wsca_agent_checkout', function(){
            var website_sale_checkout_agent_addresses = new website.website_sale_checkout_agent.Addresses();
        });
    });
}());
