###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    signature = fields.Binary(
        string='Signature',
        attachment=True,
        copy=False,
    )
    signature_datetime = fields.Datetime(
        string='Signature datetime',
        copy=False,
    )
    signature_filename = fields.Char(
        string='Signature filename',
        copy=False,
    )

    def action_sign(self):
        self.ensure_one()
        action = self.env.ref(
            'stock_picking_signature.stock_picking_signature_wizard_action')
        action = action.read()[0]
        return action
