###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.tools import float_is_zero


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id.force_packaging_qty:
            packaging = self.product_id.packaging_ids.filtered(
                lambda p: not float_is_zero(
                    p.qty, precision_rounding=p.product_id.uom_id.rounding
                )
            )[:1]
            if packaging:
                self.update(
                    {
                        'product_packaging': packaging.id,
                        'product_uom_qty': packaging.qty,
                    }
                )
        return res

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        if not self.product_uom_qty:
            self.product_uom_qty = self.product_packaging.qty
        res = super()._onchange_product_uom_qty()
        if not res:
            res = self._check_qty_is_pack_multiple()
        return res

    def _check_qty_is_pack_multiple(self):
        if self.product_id.force_packaging_qty and self.product_packaging.qty:
            if self.product_uom_qty % self.product_packaging.qty:
                warning_msg = {
                    'title': _('Product quantity cannot be packed'),
                    'message': _(
                        'For the product {prod}, '
                        'the {qty} is not the multiple of any pack.\n'
                        'Please change quantity nor package.'
                    ).format(
                        prod=self.product_id.name, qty=self.product_uom_qty),
                }
                return {'warning': warning_msg}
        return {}
