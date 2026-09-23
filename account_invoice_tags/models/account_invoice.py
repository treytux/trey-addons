###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    tag_ids = fields.Many2many(
        comodel_name='account.invoice.tag',
        string='Invoice Tags',
        relation='account_invoice_tag_rel',
        column1='invoice_id',
        column2='tag_id',
    )
