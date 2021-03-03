odoo.define('website_rma.WebsiteOrder', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let WebsiteOrder = Class.extend({
        init: function () {
            let self = this
            let $all_line_button = $('button.js_all_line_button')
            if($all_line_button.length) {
                $all_line_button.on('click', function(e){
                    e.preventDefault()
                    let $inputs = $('input.js_wrma_variant_qty')
                    self.reset_quantities_lines_to($inputs)
                })
            }
            let $add_cart_json = $('a.float_left.js_add_cart_json')
            if($add_cart_json.length) {
                $add_cart_json.on('click', function(e){
                    e.preventDefault()
                    let $obj = $(this).parent('').find('input.js_wrma_variant_qty')
                    var max = $obj.data("max")
                    if ($obj.val() < max){
                        $obj.val(parseInt($obj.val()) + 1)
                    }
                    else if (!$obj.val()){
                        $obj.val(0)
                    }
                })
            }
            let $sub_cart_json = $('a.float_right.js_add_cart_json')
            if($sub_cart_json.length) {
                $sub_cart_json.on('click', function(e){
                    e.preventDefault()
                    let $obj = $(this).parent('').find('input.js_wrma_variant_qty')
                    if ($obj.val() > 0){
                        $obj.val(parseInt($obj.val()) - 1)
                    }
                    else if (!$obj.val()){
                        $obj.val(0)
                    }
                })
            }
        },
        reset_quantities_lines_to: function ($inputs) {
            if($inputs.length) {
                $inputs.each(function(index){
                    let $val = $(this).data("max") || 0
                    $(this).val(parseInt($val))
                })
            }
        },
    })
    let show_website_order = new WebsiteOrder()
    return {
        WebsiteOrder: WebsiteOrder,
        show_website_order: show_website_order,
    }
})
