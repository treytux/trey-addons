###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_policy = fields.Selection(
        compute='_compute_invoice_policy',
    )

    @api.depends('partner_id.invoice_policy')
    def _compute_invoice_policy(self):
        for order in self:
            if order.partner_id and order.partner_id.invoice_policy:
                order.invoice_policy = order.partner_id.invoice_policy
            else:
                order.invoice_policy = order._get_default_invoice_policy()

    def _get_default_invoice_policy(self):
        default_invoice_policy = (
            self.env['res.config.settings']
            .sudo()
            .default_get(['default_invoice_policy'])
            .get('default_invoice_policy', False)
        )
        return default_invoice_policy
