###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_day_id = fields.Many2one(
        comodel_name='res.partner.invoice_day',
        string='Invoicing day',
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_invoice_day(self):
        if not self.partner_id:
            return
        self.update({
            'invoice_day_id': self.partner_id.sale_invoice_day_id,
        })
