odoo.define('product_purchase_last_price.PivotController', function (require) {
    'use strict';
    require('sale_report_from_stock_move.PivotController');
    var PivotController = require('web.PivotController');
    PivotController.include({
        _getMarginBaseMeasure: function (measures) {
            if (measures.indexOf('purchase_last_price') !== -1) {
                return 'purchase_last_price';
            }
            return this._super.apply(this, arguments);
        },
    });
});
