###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @classmethod
    def _get_confirm_lock_protected_fields(cls):
        return (
            'discount',
            'order_id',
            'price_unit',
            'product_id',
            'product_uom_qty',
            'route_id',
        )

    def _raise_confirm_lock_error(self):
        raise UserError(_(
            'You cannot modify lines on a confirmed sale order. '
            'Cancel the order, set it back to quotation, apply your changes '
            'and confirm it again.'))

    def _has_confirm_lock_protected_fields(self, values):
        return bool(
            set(values).intersection(self._get_confirm_lock_protected_fields()))

    def _is_create_on_confirmed_order(self, order):
        return order and order.state == 'sale'

    def _get_order_from_create_vals(self, values):
        order_id = values.get('order_id')
        if not order_id:
            return self.env['sale.order']
        return self.env['sale.order'].browse(order_id)

    def _check_confirm_lock_create_vals(self, vals_list):
        for values in vals_list:
            order = self._get_order_from_create_vals(values)
            if self._is_create_on_confirmed_order(order):
                self._raise_confirm_lock_error()

    def _check_confirm_lock_write_vals(self, values):
        if not self._has_confirm_lock_protected_fields(values):
            return
        if self.filtered(lambda line: line.order_id.state == 'sale'):
            self._raise_confirm_lock_error()

    def _check_confirm_lock_unlink(self):
        if self.filtered(lambda line: line.order_id.state == 'sale'):
            self._raise_confirm_lock_error()

    @api.model_create_multi
    def create(self, vals_list):
        self._check_confirm_lock_create_vals(vals_list)
        return super().create(vals_list)

    def write(self, values):
        self._check_confirm_lock_write_vals(values)
        return super().write(values)

    def unlink(self):
        self._check_confirm_lock_unlink()
        return super().unlink()
