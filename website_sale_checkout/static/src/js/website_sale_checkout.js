(function() {
    'use strict';
    var instance = openerp;
    var website = openerp.website;
    var _t = openerp._t;
    website.ready().done(function() {
        website.website_sale_checkout = {};
        website.website_sale_checkout.Addresses = openerp.Widget.extend({
            dom_ready: $.Deferred(),
            ready: function(){
                return this.dom_ready.then(function() {}).promise();
            },
            init: function (parent, options) {
                this.dom_ready.resolve();
                var self = this;
                this._super(parent);

                var $show_form = $('input[name="show_form"]'),
                    $show_form_shipping = $('input[name="show_form_shipping"]'),
                    $shipping_selected = $("select[name='shipping_id'] :selected"),
                    shipping_form = $('.js_shipping input').not('.js_wsc_hidden'),
                    billing_form = $('.form-group').not('.js_shipping .form-group').not('.js_wsc_hidden').not('.hidden'),
                    $country_id = $('select[name="country_id"]'),
                    $state_id = $('select[name="state_id"]'),
                    $shipping_state_id = $('select[name="shipping_state_id"]'),
                    $shipping_country_id = $('select[name="shipping_country_id"]'),
                    billing_form_error = false;

                function show_billing_summary() {
                    billing_form.addClass('hidden');
                    $('.js_wsc_address_static_invoice').removeClass('hidden');
                    $('.js_wsc_address_edit').removeClass('hidden');
                }

                function show_shipping_summary(reverse=false) {
                    var $shipping_selected = $("select[name='shipping_id'] :selected");
                    $('.js_shipping').addClass('hidden');
                    $('.js_wsc_address_static_shipping').removeClass('hidden');
                    $.each($shipping_selected.data(), function(index, value) {
                        $('.js_wsc_' + index).html(value);
                    });
                    if (reverse){
                        $('.js_shipping').removeClass('hidden');
                        $('.js_wsc_address_static_shipping').addClass('hidden');
                    }
                 }

                function error_billing() {
                    var check_billing = false
                    $(billing_form).each(function(){
                        $(this).parent('div.form-group').removeClass('has-error');
                        if ($(this).hasClass('has-error')){
                            check_billing = true;
                        }
                    });
                    return check_billing;
                }

                function error_shipping() {
                    var check_shipping = false;
                    if ($(shipping_form).parent().hasClass('has-error')){
                        check_shipping = true;
                    }
                    return check_shipping;
                }

                billing_form_error = error_billing()
                // Settings shipping selector
                $shipping_selected.parent().on('change', function(){
                    $('.js_shipping input').attr('readonly', false);
                    $('.js_shipping select').attr('disabled', false);
                });
                $('.js_shipping input').attr('readonly', false);
                $('.js_shipping select').attr('disabled', false);

                $country_id.on('change', function(){
                    $state_id.val('');
                });

                $shipping_country_id.on('change', function(){
                    $shipping_state_id.val('');
                });

                // Init values
                if(billing_form_error == false && $show_form.val() === "1"){
                    show_billing_summary();
                }

                error_shipping()
                if (($shipping_selected.val() != 0) && ($shipping_selected.val() != -1) && (error_shipping() === false)){
                    show_shipping_summary();
                }

                // Edit button summaries
                $('.js_wsc_address_edit').on('click', function(e){
                    e.preventDefault();
                    var address_type = $(this).data('address_type')
                    if(address_type == 'invoice'){
                        $('.js_wsc_address_static_invoice').addClass('hidden');
                        $(this).addClass('hidden');
                        billing_form.removeClass('hidden');
                    }else{
                        $('.js_wsc_address_static_shipping').addClass('hidden');
                        $(this).addClass('hidden');
                        $('.js_shipping').removeClass('hidden');
                    }
                });

                // Onchange billing input
                $(billing_form).each(function(){
                    $(this).change(function (event) {
                        if ($(this).parent().hasClass('has-error')){
                            $(this).parent().removeClass('has-error');
                        }
                    })
                });

                // Onchange shipping input
                $(shipping_form).each(function(){
                    $(this).change(function (event) {
                        if ($(this).parent().hasClass('has-error')){
                            $(this).parent().removeClass('has-error');
                        }
                        if ($(this).val() == ''){
                            $(this).parent().addClass('has-error');
                        }
                    })
                });

                // selector_shipping NEVER should be hidden
                var selector_shipping_is_hidden = $('.oe_shipping.page-header.col-lg-12').next().hasClass('hidden');
                selector_shipping_is_hidden ? $('.oe_shipping.page-header.col-lg-12').next().removeClass('hidden') : false;

                // Onchange shipping selection
                $shipping_selected.parent().on('change', function(){
                    var turnOff = true;
                    if ((parseInt($(this).val()) != -1)&&(error_billing() == false)){
                        show_billing_summary();
                    }
                    if ((parseInt($(this).val()) == 0)&&(error_billing() == false)){
                        show_shipping_summary(turnOff);
                    }
                    if (($(this).val() != 0)&&($(this).val() != -1)){
                        if (error_shipping() == false){
                            show_shipping_summary();
                        }
                        if($(this).val() != -1){
                            show_shipping_summary();
                        }
                    }
                    if ($(this).val() == -1){
                            shipping_form.parent().removeClass('has-error');
                            $shipping_country_id.val('');
                            $shipping_state_id.val('');
                            show_shipping_summary(turnOff);
                    }
                })
            },
        });

        openerp.website.if_dom_contains('.js_wsc_address_static', function(){
            var website_sale_checkout_addresses = new website.website_sale_checkout.Addresses();
        });
    });
}());
