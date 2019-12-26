odoo.define('website_bootstrap_select.selectpicker', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let SelectPicker = Class.extend({
        init: function () {
            let $selectpicker = $('.selectpicker')
            if($selectpicker.length > 0) {
                $selectpicker.selectpicker()
            }
        },
    })
    let select_picker = new SelectPicker()
    return {
        SelectPicker: SelectPicker,
        select_picker: select_picker,
    }
})
