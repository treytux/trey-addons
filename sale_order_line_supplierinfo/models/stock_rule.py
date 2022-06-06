###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_select_supplier(self, values, suppliers):
        def get_sale_line(values):
            if values.get('sale_line_id'):
                return self.env['sale.order.line'].browse(
                    values['sale_line_id'])
            if values.get('move_dest_ids'):
                return values['move_dest_ids'].mapped('sale_line_id')[0]

        line = get_sale_line(values)
        if not line:
            return super()._make_po_select_supplier(values, suppliers)
        if not line.supplierinfo_id:
            return super()._make_po_select_supplier(values, suppliers)
        return line.supplierinfo_id
