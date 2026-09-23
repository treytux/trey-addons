###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_tax = fields.Monetary(
        track_visibility='always',
    )
