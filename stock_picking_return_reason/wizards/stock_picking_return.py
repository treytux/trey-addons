###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    return_reason = fields.Many2one(
        comodel_name='stock.picking.return.reason',
        string='Return reason'
    )

    def create_returns(self):
        res = super().create_returns()
        if not self.return_reason:
            return res
        self.picking_id.return_reason_id = self.return_reason.id
        return res
