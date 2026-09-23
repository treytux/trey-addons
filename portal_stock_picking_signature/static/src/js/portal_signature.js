odoo.define('portal_stock_picking_signature.signature_custom', function (require) {
    "use strict";

    var signatureForm = require('portal.signature_form');

    signatureForm.SignatureForm.include({
        /**
         * @override
         */
        initSign: function () {
            this.$("#o_portal_signature").empty().jSignature({
                'decor-color': '#D1D0CE',
                'color': '#000',
                'background-color': '#fff',
                'height': '260px',
                'width': '100%',
            });
            this.empty_sign = this.$("#o_portal_signature").jSignature('getData', 'image');
        },
        /**
         * @override
         */
        start: function () {
            this._super.apply(this, arguments);
            let $js_button_cancel = $('.o_portal_sidebar a.btn-secondary');
            let $js_button_confirm = this.$('button.o_portal_sign_submit');
            if($js_button_confirm.length && $js_button_cancel.length) {
                $js_button_cancel.insertBefore($js_button_confirm);
            }
            return $.when();
        },
    });
});
