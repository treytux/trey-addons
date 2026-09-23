###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################

from odoo import fields, models


class StockBarcodesDummyLog(models.Model):
    _name = 'stock.barcodes.dummy.log'
    _description = 'Stock barcodes dummy log'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    barcode = fields.Char(
        string='Barcode',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot',
    )
    qty = fields.Integer(
        string='Qty',
    )
    dummy_id = fields.Many2one(
        comodel_name='stock.quant.package_dummy',
        string='Dummy',
    )
    pallet_barcode = fields.Char(
        string='Pallet barcode',
    )
    active = fields.Boolean(
        string='Active',
    )
