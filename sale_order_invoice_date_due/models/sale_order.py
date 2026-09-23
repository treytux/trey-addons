###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_date_due = fields.Date(
        string='Invoice date due',
    )

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        for sale in self:
            if sale.invoice_date_due:
                res['date_due'] = sale.invoice_date_due
        return res
