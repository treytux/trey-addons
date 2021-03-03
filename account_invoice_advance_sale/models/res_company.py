###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    account_invoice_advance_sale_method = fields.Selection(
        selection=[
            ('formula', 'Formula (ej: "50+30+20")'),
            ('grid', 'Grid lines with name, percent and date'),
        ],
        required=True,
        string='Invoice advance method',
        default='formula',
    )
