###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for sale in self:
            if not sale.client_order_ref and (
                    sale.partner_id.require_client_order_ref):
                raise ValidationError(_(
                    'A client order number is required to confirm this '
                    'quotation.'))
        return super().action_confirm()
