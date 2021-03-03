###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_open_simulator(self):
        res = super().action_open_simulator()
        sale_simulator = self.env[res['res_model']].browse(res['res_id'])
        for line in sale_simulator.line_ids:
            line.write({
                'multiple_discount': line.sale_line_id.multiple_discount,
                'discount_name': line.sale_line_id.discount_name,
            })
        return res
