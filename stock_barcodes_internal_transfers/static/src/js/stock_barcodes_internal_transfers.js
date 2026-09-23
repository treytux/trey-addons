odoo.define('stock_barcodes_internal_transfers.BarcodesInternalTransfers', function (require) {
    'use strict';

    const BarcodesInternalTransfers = {
        _barcode_models: [
            'stock.barcodes.internal.transfers',
        ],
        _isAllowedBarcodeModel: function(model_name){
            return this._barcode_models.indexOf(model_name) !== -1;
        },
    };
    return BarcodesInternalTransfers;
});
