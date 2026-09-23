odoo.define('portal_stock_picking_signature.signature_custom', function (require) {
    "use strict";

    var signatureForm = require('portal.signature_form');

    signatureForm.SignatureForm.include({
        start: function () {
            let res = this._super.apply(this, arguments);
            let $js_button_cancel = $('.o_portal_sidebar a.btn-secondary');
            let $js_button_confirm = this.$('button.o_portal_sign_submit');
            if ($js_button_confirm.length && $js_button_cancel.length) {
                $js_button_cancel.insertBefore($js_button_confirm);
            }
            return res;
        },
    });
});
