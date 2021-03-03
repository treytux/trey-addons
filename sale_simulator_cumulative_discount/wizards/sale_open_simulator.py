###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOpenSimulator(models.TransientModel):
    _inherit = 'sale.open.simulator'

    multiple_discount = fields.Char(
        string='Discount (%)',
        default='0.0',
        states={'readonly': [('readonly', True)]},
    )
    discount_name = fields.Char(
        string='Discount Name',
        states={'readonly': [('readonly', True)]},
    )

    @api.onchange('multiple_discount')
    def onchange_multiple_discount(self):
        for line in self.line_ids:
            line.multiple_discount = line.discount = self.multiple_discount
        self.line_ids._onchange_discount()

    @api.onchange('discount_name')
    def onchange_discount_name(self):
        for line in self.line_ids:
            line.discount_name = self.discount_name

    @api.multi
    def action_update(self):
        super().action_update()
        for line in self.line_ids:
            line.sale_line_id.write({
                'multiple_discount': line.multiple_discount,
                'discount_name': line.discount_name,
            })
