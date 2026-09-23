##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import _, api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'rental_qty', 'start_date', 'end_date')
    def rental_product_id_change(self):
        result = super().rental_product_id_change() or {}
        result.pop('warning', None)
        for line in self:
            if (
                not line.product_id.rented_product_id
                or line.rental_type not in ('new_rental', 'rental_extension')
                or not line.rental_qty
                or not line.start_date
                or not line.end_date
                or not line.order_id.warehouse_id
            ):
                continue
            availability = self.env[
                'rental.availability']._get_rental_availability(
                line.product_id.rented_product_id,
                line.order_id.warehouse_id,
                line.start_date,
                line.end_date,
                line.rental_qty
            )
            if not availability['is_available']:
                result['warning'] = {
                    'title': _('Not enough stock !'),
                    'message': availability['warning'], }
        return result
