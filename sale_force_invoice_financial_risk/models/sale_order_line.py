###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends(
        "state",
        "price_reduce_taxinc",
        "qty_delivered",
        "product_uom_qty",
        "qty_invoiced",
        "order_id.force_invoiced",
    )
    def _compute_risk_amount(self):
        for line in self:
            if line.order_id.force_invoiced:
                line.risk_amount = 0.0
                continue
            super(SaleOrderLine, line)._compute_risk_amount()
