###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    partner_internal_transfers = fields.Many2one(
        comodel_name='res.partner',
        string='Partner internal transfers',
    )
    validate_barcode_action = fields.Char(
        string='Validate barcode',
    )

    def action_barcode_scan_internal_transfers(self):
        module_name = 'stock_barcodes_internal_transfers'
        action_name = 'stock_barcodes_internal_transfers_wizard_action'
        action = self.env.ref('%s.%s' % (module_name, action_name)).read()[0]
        wizard = self.env['stock.barcodes.internal.transfers'].create({})
        action['res_id'] = wizard.id
        return action
