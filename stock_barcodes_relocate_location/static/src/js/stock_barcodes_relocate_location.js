odoo.define('stock_barcodes_relocate_location.BarcodesRelocateLocation', function (require) {
    'use strict';

    const BarcodesRelocateLocation = {
        _barcode_models: [
            'stock.barcodes.relocate.location',
        ],
        _isAllowedBarcodeModel: function(model_name){
            return this._barcode_models.indexOf(model_name) !== -1;
        },
    };
    return BarcodesRelocateLocation;
});
