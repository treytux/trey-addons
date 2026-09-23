###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_cancel(self):
        if self._context.get('skip_check_cancel'):
            return super().action_cancel()
        for sale in self:
            if sale.invoice_ids:
                raise exceptions.UserError(
                    _('You cannot cancel a sale order that has been invoiced.')
                )
        return super().action_cancel()
