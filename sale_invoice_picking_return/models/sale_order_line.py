###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends(
        'qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        res = super()._get_to_invoice_qty()
        for line in self:
            if line.move_ids and line.move_ids[0].to_refund:
                line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
        return res
