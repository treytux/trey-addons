###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    show_missing_taxes_in_so = fields.Boolean(
        string='Show Missing Taxes Warning in Sale Order',
        help='When this setting is set, a warning is displayed on sale order '
        'form alerting you that taxes in sale order are missing.',
    )
