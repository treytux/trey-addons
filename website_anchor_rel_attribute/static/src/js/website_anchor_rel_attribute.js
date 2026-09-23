odoo.define('website_anchor_rel_attribute.website_editor_link_extension', function (require) {
    'use strict'

    var weWidgets = require('wysiwyg.widgets')

    weWidgets.LinkTools.include({
        select_menu_selector: 'we-selection-items[name="link_rel"]',
        custom_events: _.extend({}, weWidgets.LinkTools.prototype.custom_events || {}, {
            website_url_chosen: '_onAutocompleteClose',
            rel_option_chosen: '_onRelChange',
        }),

        init: function () {
            this._super.apply(this, arguments)
        },

        start: async function () {
            var def = await this._super.apply(this, arguments)
            this._loadRelValue()
            return def
        },

        _loadRelValue: function () {
            let relValue = this.$link.attr('rel') || ''
            const $selectMenu = this.$(this.select_menu_selector)
            const buttons = $selectMenu.find('we-button')
            buttons.each(function () {
                if ($(this).data('value') === relValue) {
                    $(this).addClass('selected')
                } else {
                    $(this).removeClass('selected')
                }
            })
            const $toggler = $selectMenu.closest('we-select').find('we-toggler')
            $toggler.text(relValue || 'None')
        },

        _onRelChange: function (ev) {
            const relValue = $(ev.currentTarget).data('value')
            this._setRel(relValue)
        },

        _setRel: function (relValue) {
            if (relValue) {
                this.$link.attr('rel', relValue)
            } else {
                this.$link.removeAttr('rel')
            }
        },

        _onPickSelectOption(ev) {
            if (ev.currentTarget.closest('[name="link_rel"]')) {
                this._onRelChange(ev)
            }
            this._super(...arguments)
        },

    })
})
