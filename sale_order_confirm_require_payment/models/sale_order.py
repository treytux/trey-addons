###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            missing = []
            if not order.payment_term_id:
                missing.append(_('Payment Terms'))
            if not order.payment_mode_id:
                missing.append(_('Payment Mode'))
            if missing:
                raise ValidationError(_(
                    'The following fields are required before confirming the '
                    'order: %s.') % ', '.join(missing))
        return super().action_confirm()
