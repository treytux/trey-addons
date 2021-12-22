###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends()
    def _compute_product_customer_code(self):
        res = super()._compute_product_customer_code()
        for move in self.filtered(
            lambda m: m.picking_id and m.picking_id.partner_id
                and m.product_tmpl_id.customer_ids):
            customers = \
                move.product_tmpl_id.customer_ids.filtered(
                    lambda m: m.name == move.picking_id.partner_id)
            move.product_customer_code = (
                customers and customers[0].product_code or '')
        return res
