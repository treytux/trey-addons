(function () {
    'use strict';
    var website = openerp.website;

    website.website_sale_payment_method_discount = {};
    website.website_sale_payment_method_discount.Payment_method_discount = openerp.Widget.extend(
    {
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(
                function() {}).promise();
        },

        init: function (parent, options) {
            var self = this;
            this._super(parent);

            discount_method_inputs();

            function fake_update_order($cart_products, cart_total_span) {
                // window.location.reload();
                // @TODO Revisar si se puede hacer sin refrescar la pagina.
                var $cart_products = $('#cart_products').find('span.oe_currency_value'),
                    cart_total_span = $('#order_total').find('span.oe_currency_value');
                // Hidden discount row
                $($cart_products).each(function(){
                    if (parseFloat(this.innerText) < 0) {
                        $(this).closest('tr').addClass('hidden');
                    }
                })
                // Fake Update order total price
                var discount_acquired = 0,
                    cart_total = parseFloat($(cart_total_span)[0].innerText.replace(".", "").replace(",", "."));

                $($cart_products).each(function(){
                    var row_price = parseFloat(this.innerText.replace(",", "."));
                    discount_acquired = row_price < 0 ? Math.abs(row_price) : discount_acquired;
                });
                $(cart_total_span)[0].innerText = (cart_total + discount_acquired).toLocaleString() +',' + (cart_total + discount_acquired).toFixed(2).toLocaleString().split(".")[1]
            }

            function update_order(discount, action_discount, acquirer) {
                var response =  openerp.jsonRpc('/shop/payment/discount', 'call', {
                        acquirer: $(acquirer).val(),
                        action: action_discount
                }).then(function (response) {
                    update_payment_view(response);
                });
            }

            function update_payment_view(response) {
                if (response === 'Discount applied' || response === 'Discount deleted') {
                    window.location.reload();
                } else if (response === 'Has a discount applied'){
                } else if (response === 'Discount greater than the amount of the order'){

                } else {
                    console.log('Error: ', response);
                }
            }

            function discount_method_inputs () {
                var payment_list = $('.js_payment').find('ul.list-unstyled'),
                    $input_payments_methods = payment_list.find('input');

                $($input_payments_methods).change(function(){
                    var is_checked_and_payment_discount = $(this).attr('checked') && ($(this).attr('pay_method_discount') !== undefined),
                        discount = $(this).attr('pay_method_discount');
                    if(is_checked_and_payment_discount) {
                        update_order(discount, 'discount', this);
                    }else{
                        update_order(false, 'delete_discount', this);
                    }
                });
            }
        }
    });

    website.ready().done(function () {
        website.if_dom_contains('.js_payment', function ($el) {
            new website.website_sale_payment_method_discount.Payment_method_discount();
        });
    });
}());

