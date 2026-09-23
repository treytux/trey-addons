(function () {
    'use strict'
    $(document).ready(function () {
        $('.oe_website_sale').each(function () {
            var oe_website_sale = this
            $('form.js_features input', oe_website_sale).on('change', function () {
                $(this).closest("form").submit()
            })
        })
    })
})()

odoo.define('website_sale.website_sale_feature', function (require) {
    'use strict'
    var sAnimations = require('website.content.snippets.animation')
    sAnimations.registry.websiteSaleFeature = sAnimations.Class.extend({
        selector: '#o_shop_collapse_feature',
        read_events: {
            'click .fa-chevron-right': '_onOpenClick',
            'click .fa-chevron-down': '_onCloseClick',
        },
        start: function () {
            var res = this._super.apply(this, arguments)
            this.$('ul.nav-hierarchy').each(function () {
                var $ul = $(this)
                if ($ul.find('li.active').length) {
                    $ul.show()
                    var $icon = $ul.closest('li.nav-item').find('i.fa:first')
                    $icon.removeClass('fa-chevron-right').addClass('fa-chevron-down')
                }
            })
            return res
        },
        _onOpenClick: function (ev) {
            var $fa = $(ev.currentTarget)
            var $li = $fa.closest('li.nav-item')
            $li.find('ul.nav-hierarchy:first').show('normal')
            $fa.removeClass('fa-chevron-right').addClass('fa-chevron-down')
        },
        _onCloseClick: function (ev) {
            var $fa = $(ev.currentTarget)
            var $li = $fa.closest('li.nav-item')
            $li.find('ul.nav-hierarchy:first').hide('normal')
            $fa.removeClass('fa-chevron-down').addClass('fa-chevron-right')
        },
    })
})
