###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOpenSimulatorLine(models.TransientModel):
    _inherit = 'sale.open.simulator.line'

    multiple_discount = fields.Char(
        string='Disc. (%)',
        default='0.0',
    )
    discount_name = fields.Char(
        string='Disc. Name',
    )

    @api.onchange('multiple_discount')
    def onchange_multiple_discount(self):
        self.env['sale.order.line'].get_multiple_discount(
            self, self.multiple_discount)
