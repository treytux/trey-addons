odoo.define('website_sale_product_brand_grid.FancyBox', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let FancyBox = Class.extend({
        fancy_box_selector: '[data-fancybox="product_detail_gallery"]',
        init: function () {
            let $fancybox = $(self.fancy_box_selector)
            if($fancybox.length > 0) {
                $fancybox.fancybox({buttons: [
                        'zoom',
                        'slideShow',
                        'fullScreen',
                        'close'
                    ]
                })
            }
        },
    })
    let fancy_box = new FancyBox()
    return {
        FancyBox: FancyBox,
        fancy_box: fancy_box,
    }
})

odoo.define('website_sale_product_brand_grid.CartQuantities', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let CartQuantities = Class.extend({
        cart_quantities_selector: 'input[name="cart_quantities"]',
        init: function () {
            let self = this
            let $cart_quantities = $(self.cart_quantities_selector)
            if($cart_quantities.length > 0) {
                let cart_quantities = JSON.parse($cart_quantities.val())
                for (var key in cart_quantities) {
                    if (cart_quantities.hasOwnProperty(key)) {
                        $('[data-product-id="' + key + '"]').val(cart_quantities[key])
                    }
                }
            }
        },
    })
    let cart_quantities = new CartQuantities()
    return {
        CartQuantities: CartQuantities,
        cart_quantities: cart_quantities,
    }
})

odoo.define('website_sale_product_brand_grid.QuantityButton', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let QuantityButton = Class.extend({
        qty_btn_selector: 'a.js_wspbg_qty_btn',
        init: function () {
            let self = this
            $(self.qty_btn_selector).each(function(){
                $(this).on('click', function(e){
                    e.preventDefault()
                    self.set_value(this)
                })
            })
        },
        set_value: function (qty_btn) {
            let $input = $('input[data-product-id="' + $(qty_btn).data('product_id') + '"]')
            $input.val($(qty_btn).text())
        },
    })
    let qty_btn = new QuantityButton()
    return {
        QuantityButton: QuantityButton,
        qty_btn: qty_btn,
    }
})

odoo.define('website_sale_product_brand_grid.GridButton', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let GridButton = Class.extend({
        grid_btn_selector: 'a.js_wspbg_grid_btn',
        init: function () {
            let self = this
            $(self.grid_btn_selector).each(function(){
                $(this).on('click', function(e){
                    e.preventDefault()
                    self.set_value($(this).data('set_attribute'))
                })
            })
        },
        set_value: function (set_attribute) {
            let $inputs = $('input.js_wspbg_variant_qty')
            $inputs.each(function(index){
                $(this).val($(this).data(set_attribute))
            })
        },
    })
    let grid_btn = new GridButton()
    return {
        GridButton: GridButton,
        grid_btn: grid_btn,
    }
})

odoo.define('website_sale_product_brand_grid.GridButtonRow', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let GridButtonRow = Class.extend({
        grid_btn_row_selector: 'a.js_wspbg_grid_btn_row',
        init: function () {
            let self = this
            $(self.grid_btn_row_selector).each(function(index){
                $(this).on('click', function(e){
                    e.preventDefault()
                    self.set_quantities_to(this)
                })
            })
        },
        set_quantities_to: function (obj) {
            let $inputs = $(obj).closest('tr').find('input.js_wspbg_variant_qty')
            $inputs.each(function(index){
                $(this).val($(this).data($(obj).data('set_attribute')))
            })
        },
    })
    let grid_btn_row = new GridButtonRow()
    return {
        GridButtonRow: GridButtonRow,
        grid_btn_row: grid_btn_row,
    }
})

odoo.define('website_sale_product_brand_grid.AddToCart', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let Ajax = require('web.ajax');
    let AddToCart = Class.extend({
        add_to_cart_btn: 'a.js_add_to_cart_variants',
        init: function () {
            let self = this
            $(self.add_to_cart_btn).on('click', function(e){
                e.preventDefault()
                self.add_to_cart()
            })
        },
        add_to_cart: function () {
            let $inputs = $('input.js_wspbg_variant_qty')
            if($inputs.length > 0) {
                let product_id = []
                let set_qty = []
                $inputs.each(function(index){
                    product_id.push(parseInt($(this).data('product-id')))
                    set_qty.push(parseInt($(this).val()))
                })
                Ajax.jsonRpc('/shop/cart/update_json_multi', 'call', {
                    'product_id': product_id,
                    'set_qty': set_qty
                }).then(function (data) {
                    // TODO: En o_header_affix hay otro #my_cart al que no se
                    // le aplican estos cambios
                    let $my_cart = $("#my_cart")
                    let $my_cart_quantity = $(".my_cart_quantity")
                    if (data.cart_quantity > 0 && $my_cart.length > 0 && $my_cart_quantity.length > 0) {
                        $my_cart.removeClass('d-none')
                        $my_cart_quantity.html(data.cart_quantity).hide().fadeIn(600)
                    } else if (data.cart_quantity <= 0 && $my_cart) {
                        $my_cart.addClass('d-none')
                    }
                })
            }
        },
    })
    let add_to_cart = new AddToCart()
    return {
        AddToCart: AddToCart,
        add_to_cart: add_to_cart,
    }
})

odoo.define('website_sale_product_brand_grid.SearchAndFilter', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let SearchAndFilter = Class.extend({
        discount: 0,
        search: '',
        init: function () {
            let self = this
            let $discount_values = $('.js_wspbg_cost_price .o_wsdb_badge_value')
            if($discount_values.length > 0) {
                let $filters_legend = $('.js_wspbg_discount_filters_legend')
                if($filters_legend.length > 0) {
                    let $discount_filters_buttons = $('<div class="js_wspbg_discount_filters_buttons form-inline justify-content-center mt16 mb16"><div class="btn-group btn-group-toggle" data-toggle="buttons"></div></div>')
                    let $discount_filters_buttons_group = $discount_filters_buttons.find('.btn-group')
                    $filters_legend.before($discount_filters_buttons)
                    let discount_values = $discount_values.map(function() {
                        return parseInt(this.innerHTML);
                    }).get()
                    new Set(discount_values.sort()).forEach(function(value){
                        let label = value
                        let state = ''
                        if (label == 0) {
                            label = 'Todos'
                            state = 'active'
                        } else {
                            label += ' % de descuento'
                        }
                        $discount_filters_buttons_group.append('<label class="btn btn-outline-secondary ' + state + '"><input type="radio" name="options" data-value="' + value + '" autocomplete="off" checked="checked"/>' + label + '</label>')
                    })
                    let $discount_filters_buttons_labels = $discount_filters_buttons_group.find('label')
                    $discount_filters_buttons_labels.on('click', function(){
                        self.discount = $(this).find('input').data('value')
                        self.apply_search_and_filters()
                    })
                }
            }
            let $grid_search = $('.js_wspbg_search')
            if($grid_search.length > 0) {
                $grid_search.on('keyup', function(){
                    self.search = $(this).val()
                    self.apply_search_and_filters()
                })
            }
        },
        apply_search_and_filters: function () {
            let self = this
            let $grid_table_items = $('.js_wspbg_grid_table_item')
            $grid_table_items.each(function(){
                if(self.search == '' || $(this).find('.js_wspbg_variant_search').val().includes(self.search)){
                    $(this).show()
                } else {
                    $(this).hide()
                }
            })
            // Para cuando estén los descuentos
            // let self = this
            // let $discount_values = $('.js_wspbg_cost_price .o_wsdb_badge_value')
            // $discount_values.each(function(){
            //     if((self.discount == 0 || parseInt(this.innerHTML) == self.discount) && (self.search == '' || $(this).closest('tr').find('.js_wspbg_variant_search').val().includes(self.search))){
            //         $(this).closest('tr').show()
            //     } else {
            //         $(this).closest('tr').hide()
            //     }
            // })
        },
    })
    let search_and_filter = new SearchAndFilter()
    return {
        SearchAndFilter: SearchAndFilter,
        search_and_filter: search_and_filter,
    }
})
