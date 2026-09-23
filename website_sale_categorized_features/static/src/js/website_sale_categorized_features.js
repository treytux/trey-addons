(function () {
    'use strict'
    $(document).ready(function () {
        $('.oe_website_sale').each(function () {
            var oe_website_sale = this
            $('form.js_features input', oe_website_sale).on('change', function () {
                $(this).closest("form").submit()
            })
        })
        $('.js_features').each(function () {
            var $form = $(this)
            $form.find('input[name="feature"]:checked').each(function () {
                var $checked = $(this)
                var $collapse = $checked.closest('.accordion-collapse.collapse')
                if ($collapse.length) {
                    $collapse.addClass('show').css('height', 'auto')
                    var collapseId = $collapse.attr('id')
                    if (collapseId) {
                        var $btn = $form.find('[data-bs-toggle="collapse"][data-bs-target="#' + collapseId + '"]')
                        if ($btn.length) {
                            $btn.removeClass('collapsed').attr('aria-expanded', 'true')
                        }
                    }
                }
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
        _onOpenClick: function (ev) {
            var $fa = $(ev.currentTarget)
            $fa.parent().siblings().find('.fa-chevron-down:first').click()
            $fa.parents('li').find('ul:first').show('normal')
            $fa.toggleClass('fa-chevron-down fa-chevron-right')
        },
        _onCloseClick: function (ev) {
            var $fa = $(ev.currentTarget)
            $fa.parent().find('ul:first').hide('normal')
            $fa.toggleClass('fa-chevron-down fa-chevron-right')
        },
    })
})
