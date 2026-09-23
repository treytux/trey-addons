###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockBarcodesDummyRemoveLogs(models.TransientModel):
    _name = 'stock.barcodes.dummy.remove.logs'
    _description = 'Wizard to remove logs'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )

    def button_unlink_stock_barcodes_dummy_log(self):
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', self.picking_id.id),
        ])
        logs.unlink()
