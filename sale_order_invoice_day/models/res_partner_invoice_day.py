###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartnerInvoiceDay(models.Model):
    _name = 'res.partner.invoice_day'
    _description = 'Partner invoice day'
    _order = 'name'

    name = fields.Char(
        string='Name',
        translate=True,
        required=True,
    )
