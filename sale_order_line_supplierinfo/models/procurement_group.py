###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    def _get_rule(self, product_id, location_id, values):
        def get_sale_line(values):
            if values.get('sale_line_id'):
                return self.env['sale.order.line'].browse(
                    values['sale_line_id'])
            if values.get('move_dest_ids'):
                return values['move_dest_ids'].mapped('sale_line_id')[0]

        line = get_sale_line(values)
        if not line:
            return super()._get_rule(product_id, location_id, values)
        if line.supplierinfo_id.route_select == 'product':
            return super()._get_rule(product_id, location_id, values)
        domain = [
            '&',
            ('location_id', '=', location_id.id),
            ('action', '!=', 'push')]
        return self._search_rule(
            line.supplierinfo_id.route_ids,
            line.product_id, values.get('warehouse_id', False), domain)
