###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    show_wrong_accounts = fields.Boolean(
        string='Show Wrong Accounts Warning',
        help='When this setting is set, a warning is displayed on invoice form'
             ' alerting you that accounts in invoice are wrong.',
    )
    show_wrong_taxes = fields.Boolean(
        string='Show Wrong Taxes Warning',
        help='When this setting is set, a warning is displayed on invoice form'
             ' alerting you that taxes in invoice are missing.',
    )
    show_wrong_vat = fields.Boolean(
        string='Show Wrong VAT Warning',
        help='When this setting is set, a warning is displayed on invoice form'
             ' alerting you that partner VAT is missing.',
    )
