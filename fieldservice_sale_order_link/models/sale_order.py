###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super().onchange_partner_id()
        if self._context.get('default_fsm_location_id'):
            self.fsm_location_id = self._context['default_fsm_location_id']
        if self._context.get('default_partner_invoice_id'):
            self.partner_invoice_id = (
                self._context['default_partner_invoice_id'])
        if self._context.get('default_partner_shipping_id'):
            self.partner_shipping_id = (
                self._context['default_partner_shipping_id'])
