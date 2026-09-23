###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for order in self:
            product_not_consolidated = self.env['product.product']
            for line in order.order_line:
                if line.product_id and not line.product_id.is_consolidated:
                    product_not_consolidated |= line.product_id
            if product_not_consolidated:
                product_lines = "\n".join(
                    f"-{name}" for name in product_not_consolidated.mapped(
                        'display_name'))
                raise UserError(
                    _("You cannot confirm a purchase order with "
                      "non-consolidated products. \n%s") % (product_lines)
                )
        return super().button_confirm()
