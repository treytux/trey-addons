###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def onchange_product(self):
        super().onchange_product()
        for line in self:
            line.date_end = False

    @api.onchange('date_start', 'product_uom_qty', 'recurring_rule_type')
    def onchange_date_start(self):
        super().onchange_date_start()
        for line in self:
            line.date_end = False
