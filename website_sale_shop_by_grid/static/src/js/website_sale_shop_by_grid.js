(function () {
    'use strict';
    var website = openerp.website;
    var _t = openerp._t

    website.website_sale_shop_by_grid = {};

    website.website_sale_shop_by_grid.Grid = openerp.Widget.extend(
    {
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(
                function() {}).promise();
        },

        init: function (parent, options) {
            this._super(parent);
            var self = this,
                $ul = $('ul[data-attribute_value_ids]'),
                list = $ul.data('attribute_value_ids'),
                id = false,
                $button = $('#add_to_cart_grid'),
                products_qtys = $('#add_to_cart_grid').data('get_order_product_qty'),
                only_show_qty_in_cart = false,
                inputs_global = $('input[name="add_qty_grid"][data-oe-attribute_values]'),
                product_ids = [],
                line_id = [],
                add_qty = [],
                qty_available = [],
                product_in_cart_to_delete = [],
                qty_in_grid_to_delete = [];

            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.attributeName === "disabled") {
                        if ((mutation.target[mutation.attributeName]) === false) {
                            console.log('try again!');
                            mutation.target.setAttribute('disabled', 'disabled');
                        }
                    }
                });
            });

            var grid_type = 'two'
            $(inputs_global).each(function(){
                var input = this,
                    id = self.find_product(list, $(input).data('oe-attribute_values'));
                    // Checking grid type two with only one variable product attributte
                    if (id == false) {
                        id = self.check_undefined_product_id(
                            $(this).data('product_id'),
                            list,
                            $(this).data('oe-attribute_values'));
                    }
                if (inputs_global.length == 1){
                    id = $('ul[data-attribute_value_ids]').data('attribute_value_ids')[0][0];

                }

                // Anti-hack attr disable
                observer.observe(input, {
                    attributes: true
                });
                // Create grid with img and input products cart qtys
                if(id != false){
                    var img = $(input).closest('tr').find('img'),
                        cart_products = $('#add_to_cart_grid').data('get_order_product_qty');

                    $(input).attr('data-product_id', id);
                    $(img).attr('src', '/website/image/product.product/' + id + '/image_small');
                    $(img).removeClass('hidden');
                    // Input cart products qtys
                    if ((products_qtys) && (id in cart_products)) {
                        $(input).val(products_qtys[id])
                    }
                }

                $(input).change(function(){
                    check_input(this, input);
                });

                $(input).on('focus', function(){
                    if ($(this).parent().hasClass('has-error')) {
                        check_input(this, input);
                    }
                });
            });

            function check_input(each_input, input) {
                var input_product = each_input,
                    $error_div = $(input).parent(),
                    product_id = ($(input_product).data('product_id')),
                    input_qty = parseInt($(input_product).val()),
                    qty_available = parseInt($(input_product).data('qty_available')),
                    // Check values
                    limit = Number($(input_product).data('qty_available')) ? true : false,
                    input_okey = Number(input_qty),
                    add_qty = parseInt($(input_product).val()),
                    warning_label = $('.o_sbg_errors');

                if (input_okey) {
                    $($error_div).removeClass('has-error');
                    warning_label.addClass('hidden');

                    // Product stock control
                    if (limit) {
                        if (qty_available < input_qty) {
                            $($error_div).addClass('has-error');
                            warning_label.html(_t('Check available quantities for products marked in red.'));
                            warning_label.removeClass('hidden');
                            $(input).val(qty_available);
                        }else{
                            $($error_div).removeClass('has-error');
                            warning_label.addClass('hidden');
                        }
                    }

                }else{
                    // onBlur effect
                    if (isNaN(input_qty)) {
                        $(input_product).val(0)
                        $($error_div).removeClass('has-error');
                        warning_label.addClass('hidden');
                    }else{
                        $($error_div).addClass('has-error');

                        if (!(Number($(input).val()))) {
                            warning_label.html(_t('Please enter only number'));
                        }else{
                            warning_label.html(
                                _t('Check available quantities for products marked in red.'));
                            $(input).val(qty_available)
                        }
                        warning_label.removeClass('hidden');
                    }
                }
            }

            $button.on('click', function (e) {
                e.preventDefault();
                var $inputs = [],
                    product_id = [],
                    line_id = [],
                    add_qty = [];

                $('input[name="add_qty_grid"]').each(function(){
                    if(parseInt($(this).val()) != 0){

                        $inputs.push(this); }
                });

                // Control between inputs qtys and  Cart qtys
                $.each($inputs, function(index, value){
                    var cart_products = $('#add_to_cart_grid').data('get_order_product_qty'),
                        input_value = $(this).val(),
                        product_in_cart = false,
                        qty_to_add = 0,
                        product_id_push = undefined;

                    if (cart_products) {
                        product_in_cart = $(this).data('product_id') in cart_products ? true : false;
                    }

                    if (product_in_cart) {
                        var cart_qty = cart_products[$(this).data('product_id')];

                        if (cart_qty < input_value) {

                            qty_to_add = (-(cart_qty - input_value));

                        }else if (cart_qty > input_value) {
                            qty_to_add = ((input_value - cart_qty));

                        }else if (cart_qty == input_value) {
                            return;
                        }

                        product_id.push($(this).data('product_id'));
                        line_id.push(null);
                        add_qty.push(qty_to_add);

                    }else{
                        // Add new product to cart
                        product_id_push = self.check_undefined_product_id(
                            $(this).data('product_id'),
                            list,
                            $(this).data('oe-attribute_values'));
                        product_id.push(product_id_push);
                        line_id.push(null);
                        add_qty.push(parseInt($(this).val()));
                    }
                });
                if (product_id.length > 0 && add_qty.length > 0) {
                    $('.js_wssg_loading').removeClass('hidden');
                    $('.add_to_cart_grid').addClass('disabled');
                    $('.reset_grid').addClass('disabled');
                    openerp.jsonRpc('/shop/cart/update_json_multi', 'call', {
                        'product_id': product_id,
                        'line_id': line_id,
                        'add_qty': add_qty
                    }).then(function (data) {
                        window.location.href='/shop/cart';
                    });
                }
            });

            // Remove to Cart button
            $('a#reset_grid').on('click', function (e) {
                e.preventDefault();
                var cart_products = $('#add_to_cart_grid').data('get_order_product_qty'),
                    $inputs = $('input[name="add_qty_grid"]'),
                    product_id = [],
                    line_id = [],
                    add_qty = [],
                    product_in_cart = false,
                    qty_to_add = 0;

                $('.o_sbg_errors').addClass('hidden');

                $inputs.each(function(){
                    var $error_div = $(this).parent(),
                        input_value = $(this).val();

                    $error_div.removeClass('has-error');

                    if (cart_products) {
                        product_in_cart = $(this).data('product_id') in cart_products ? true : false;
                    }
                    // Delete qtys in cart
                    if (product_in_cart) {
                        var cart_qty = cart_products[$(this).data('product_id')];

                        qty_to_add = -cart_qty;
                        product_id.push($(this).data('product_id'));
                        line_id.push(null);
                        add_qty.push(qty_to_add);
                    }else{
                        // only erase qty
                        if(parseInt($(this).val()) != 0){
                            $(this).val(0);
                        }
                    }
                })
                if (product_id.length > 0 && add_qty.length > 0) {
                    $('.js_wssg_loading').removeClass('hidden');
                    $('.js_wssg_spinner').removeClass('hidden');
                    $('.add_to_cart_grid').addClass('disabled');
                    $('.reset_grid').addClass('disabled');
                    openerp.jsonRpc('/shop/cart/update_json_multi', 'call', {
                        'product_id': product_id,
                        'line_id': [],
                        'add_qty': add_qty
                    }).then(function (data) {
                        window.location.reload();
                    });
                }
            });
        },
        check_undefined_product_id: function check_undefined_product_id(product_id, list, value){
            if (product_id === undefined) {
                var a,
                    new_b;
                for(var i in list){
                    a = JSON.stringify(list[i][1].sort()[0]);
                    new_b = JSON.stringify(value.sort()[0]);
                    if(list[i][1].sort()[0] == value.sort()[0]){
                        return list[i][0];
                    }else{
                        if(list[i][1].sort()[0] == value[1]){
                            return list[i][0];
                        }
                    }
                }
                return false;
            }else{
                return product_id
            }
        },
        find_product: function find_product(list, value, grid=null){
            var a,
                b,
                grid = grid;
            for(var i in list){
                a = JSON.stringify(list[i][1].sort());
                b = JSON.stringify(value.sort());
                if(a==b){
                    return list[i][0];
                }
            }
            return false;
        }

    });

    website.website_sale_shop_by_grid.no_variants_grid_one = openerp.Widget.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function (parent, options) {
            var self = this,
                input = $('input[name="add_qty_grid"]'),
                $button  = $('#add_to_cart_grid'),
                banner_alert = ($('.o_sbg_errors')).length > 1 ? $('.o_sbg_errors')[0] : $('.o_sbg_errors');

            $(input).change(function(){
                check_input(this, input);
            });

            $(input).on('focus', function(){
                if ($(this).parent().hasClass('has-error')) {
                    check_input(this, input);
                }
            });

            // put qyt cart in input
            var cart_products = $('#add_to_cart_grid').data('get_order_product_qty'),
                input = $('input[name="add_qty_grid"]'),
                product_in_cart = false,
                product_id = [$('ul[data-attribute_value_ids]').data('attribute_value_ids')[0][0]],
                qty_to_add = 0;

            if (cart_products) {
                product_in_cart = product_id[0] in cart_products ? true : false;
                if (product_in_cart){
                    $(input).val(cart_products[product_id[0]])
                }
            }

            $button.on('click', function (e) {
                e.preventDefault();
                var $inputs = [],
                    input_value = parseInt($('input[name="add_qty_grid"]').val()),
                    line_id = [],
                    add_qty = [parseInt($('input[name="add_qty_grid"]').val())];

                // Control between inputs qtys and  Cart qtys
                if (product_in_cart) {
                    var cart_qty = cart_products[product_id[0]];

                    if (cart_qty < input_value) {
                        qty_to_add = (-(cart_qty - input_value));

                    }else if (cart_qty > input_value) {

                        qty_to_add = ((input_value - cart_qty));

                    }else if (cart_qty == input_value) {
                        return;
                    }
                    add_qty = [qty_to_add]
                }

                $('.js_wssg_loading').removeClass('hidden');
                $('.js_wssg_spinner').removeClass('hidden');
                $('.add_to_cart_grid').addClass('disabled');
                $('.reset_grid').addClass('disabled');
                openerp.jsonRpc('/shop/cart/update_json_multi', 'call', {
                    'product_id': product_id,
                    'line_id': line_id,
                    'add_qty': add_qty,
                    'set_qty': []
                }).then(function (data) {
                    window.location.href='/shop/cart';
                });
            });

            // Remove to Cart button
            $('a#reset_grid').on('click', function (e) {
                e.preventDefault();
                var cart_products = $('#add_to_cart_grid').data('get_order_product_qty'),
                    $input = $('input[name="add_qty_grid"]'),
                    line_id = [],
                    add_qty = [0],
                    qty_to_add = 0;
                $input.val(0)
                if (product_in_cart) {
                    var cart_qty = cart_products[product_id[0]];
                    $('.js_wssg_loading').removeClass('hidden');
                    $('.js_wssg_spinner').removeClass('hidden');
                    $('.add_to_cart_grid').addClass('disabled');
                    $('.reset_grid').addClass('disabled');
                    openerp.jsonRpc('/shop/cart/update_json_multi', 'call', {
                        'product_id': product_id,
                        'line_id': [],
                        'add_qty': [-cart_qty]
                    }).then(function (data) {
                        $('.js_wssg_loading').addClass('hidden');
                        $('.js_wssg_spinner').addClass('hidden');
                        $('.add_to_cart_grid').removeClass('disabled');
                        $('.reset_grid').removeClass('disabled');
                        window.location.reload();
                    });
                }
            });

            function check_input(each_input, input) {
                var input_product = each_input,
                    $error_div = $(input).parent(),
                    product_id = ($(input_product).data('product_id')),
                    input_qty = parseInt($(input_product).val()),
                    qty_available = parseInt($(input_product).data('qty_available')),
                    // Check values
                    limit = Number($(input_product).data('qty_available')) ? true : false,
                    input_okey = Number(input_qty),
                    add_qty = parseInt($(input_product).val()),
                    warning_label = ($('.o_sbg_errors')).length > 1 ? $($('.o_sbg_errors')[0]) : $('.o_sbg_errors');

                if (input_okey) {
                    $($error_div).removeClass('has-error');
                    warning_label.addClass('hidden');

                    // Product stock control
                    if (limit) {
                        if (qty_available < input_qty) {
                            $($error_div).addClass('has-error');
                            warning_label.html(_t('Check available quantities for products marked in red.'));
                            warning_label.removeClass('hidden');
                            $(input).val(qty_available);
                        }else{
                            $($error_div).removeClass('has-error');
                            warning_label.addClass('hidden');
                        }
                    }

                }else{
                    // onBlur effect
                    if (isNaN(input_qty)) {
                        $(input_product).val(0)
                        $($error_div).removeClass('has-error');
                        warning_label.addClass('hidden');
                    }else{
                        $($error_div).addClass('has-error');

                        if (!(Number($(input).val()))) {
                            warning_label.html(_t('Please enter only number'));
                        }else{
                            warning_label.html(
                                _t('Check available quantities for products marked in red.'));
                            $(input).val(qty_available)
                        }
                        warning_label.removeClass('hidden');
                    }
                }
            }

        }

    })

    website.website_sale_shop_by_grid.Cart = openerp.Widget.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function (parent, options) {
            this._super(parent);
            var self = this,
                cart_products_line = $('.js_quantity.form-control'),
                delete_button = $('span.input-group-addon.delete');

            cart_products_line.each(function() {
                $(this).change(function () {
                    self.check_product_available(this);
                })
            })
        },

        check_product_available: function check_product_available(input){
            var input = input,
                limit = Number($(input).data('qty_available')) ? true : false,
                input_value = parseInt($(input).val());
            if (limit) {
                var qty_available = parseInt($(input).data('qty_available')),
                    button_plus = $(input).parent().find('.float_left'),
                    warning = $(input).parent().parent().find('.js_wss_by_grid');

                if (input_value <= qty_available) {
                    var fa_plus = $(input).parent().parent().find('a.mb8.float_left.js_add_cart_json');

                    button_plus.removeClass('disabled');
                    warning.addClass('hidden');
                    fa_plus.attr('style', 'none;');

                    if (input_value == qty_available) {
                        fa_plus.attr('style', 'color:gray;pointer-events: none;');
                    }
                }
                if (input_value > qty_available){
                    warning.removeClass('hidden');
                    button_plus.addClass('disabled');
                    $(input).val(qty_available);
                }
            }
        }

    });

    website.ready().done(function () {
        var product_has_variants = $('.table.o_sbg_table.o_sbg_table_one')[0] ||
                $('.table.o_sbg_table.o_sbg_table_two')[0] ||
                $('.table.o_sbg_table.o_sbg_table_list')[0];
        website.if_dom_contains(product_has_variants, function ($el) {
            if($('#add_to_cart_grid').length == 0){
                $('.oe_website_spinner').attr('style', 'display: table;');
                $('#add_to_cart').attr('style', 'display: inline-block;');
            } else {
                new website.website_sale_shop_by_grid.Grid();
            }
        });

        website.if_dom_contains('div.no_variants_grid_one', function () {
            new website.website_sale_shop_by_grid.no_variants_grid_one();
        });

        website.if_dom_contains('.js_add_cart_json', function ($el) {
            new website.website_sale_shop_by_grid.Cart();
        });

    });
}());

