###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def write(self, vals):
        if self._context.get('website_id', False):
            self = self.with_context(force_update_maintenance_line=True)
        return super().write(vals)

    def is_cart_visible(self):
        self.ensure_one()
        if self.is_maintenance_line:
            if self.order_id.maintenance_active and self.price_subtotal:
                return True
            return False
        if self.is_maintenance_section:
            return self.order_id.maintenance_active
        return True
