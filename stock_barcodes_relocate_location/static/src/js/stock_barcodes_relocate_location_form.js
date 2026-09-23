odoo.define('stock_barcodes_relocate_location.FormController', function (require) {
    'use strict';

    var FormController = require('web.FormController');

    FormController.include({
        renderButtons: function ($node) {
            this._super($node);
            if (this.modelName.includes('stock.barcodes.relocate.location')) {
                this.$buttons.find('.o_form_buttons_edit')
                    .css({'display': 'none'});
            }
        },
        canBeDiscarded: function (recordID) {
            if (!this.modelName.includes('stock.barcodes.relocate.location')) {
                return this._super.apply(this, arguments);
            }
            return $.when(false);
        },
    });
});
