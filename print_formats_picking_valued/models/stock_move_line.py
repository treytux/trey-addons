###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _get_aggregated_product_quantities(self, **kwargs):
        res = super()._get_aggregated_product_quantities(**kwargs)
        for ml in self:
            if kwargs.get('except_package') and ml.result_package_id:
                continue
            aggregated_props = self._get_aggregated_properties(move_line=ml)
            line_key = aggregated_props['line_key']
            if line_key in res:
                if 'sale_price_unit' not in res[line_key]:
                    res[line_key]['sale_price_unit'] = ml.sale_price_unit
                    res[line_key]['sale_price_subtotal'] = (
                        ml.sale_price_subtotal
                    )
                else:
                    res[line_key]['sale_price_subtotal'] += (
                        ml.sale_price_subtotal
                    )
                if 'lot_set' not in res[line_key]:
                    res[line_key]['lot_set'] = set()
                name = ml.lot_id and ml.lot_id.name or ml.lot_name
                if name:
                    res[line_key]['lot_set'].add(name)
        for _line_key, values in res.items():
            if ('sale_price_unit'
                    not in values or values['sale_price_unit'] == 0):
                move = values.get('move')
                sale_line = move.sale_line_id if move else False
                if sale_line:
                    uom_report = values.get('product_uom')
                    price_unit = sale_line.product_uom._compute_price(
                        sale_line.price_unit, uom_report)
                    qty = (
                        values.get('qty_done')
                        or values.get('qty_ordered') or 0.0)
                    discount_factor = (1 - (sale_line.discount / 100.0))
                    values['sale_price_unit'] = price_unit
                    values['sale_price_subtotal'] = (
                        price_unit * qty * discount_factor
                    )
                else:
                    values.setdefault('sale_price_unit', 0.0)
                    values.setdefault('sale_price_subtotal', 0.0)
            lot_set = values.get('lot_set', set())
            if lot_set:
                values['lot_id_str'] = ", ".join(sorted(lot_set))
            else:
                values['lot_id_str'] = ''
        return res
