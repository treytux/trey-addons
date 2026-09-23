###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderCancel(models.TransientModel):
    _inherit = 'sale.order.cancel'

    has_posted_invoice = fields.Boolean(
        string='Has posted invoice',
        compute='_compute_has_posted_invoice',
    )

    @api.depends('order_id')
    def _compute_has_posted_invoice(self):
        for wizard in self:
            wizard.has_posted_invoice = bool(
                wizard.order_id.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted'))
