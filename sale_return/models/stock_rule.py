###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(
        self, product_id, product_qty, product_uom, location_id, name, origin,
        values, group_id
    ):
        res = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin,
            values, group_id)
        sale_line_id = values.get('sale_line_id')
        if not sale_line_id:
            return res
        sale_line = self.env['sale.order.line'].browse(sale_line_id)
        if sale_line.is_return <= 0:
            return res
        return_type = self.picking_type_id.return_picking_type_id
        location_dest = (
            sale_line.location_id
            if sale_line.location_id else return_type.default_location_dest_id)
        res.update({
            'is_return': True,
            'picking_type_id': return_type.id,
            'location_id': res['location_dest_id'],
            'location_dest_id': location_dest.id})
        return res
