odoo.define('stock_barcodes_dummy_label.BarcodesDummyLabel', function (require) {
    'use strict';

    const BarcodesDummyLabel = {
        _barcode_models: [
            'stock.barcodes.dummy.label',
        ],
        _isAllowedBarcodeModel: function(model_name){
            return this._barcode_models.indexOf(model_name) !== -1;
        },
    };
    return BarcodesDummyLabel;
});
