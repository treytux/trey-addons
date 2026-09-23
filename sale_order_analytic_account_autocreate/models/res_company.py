###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    autocreate_sale_analytic_account = fields.Boolean(
        string='Autocreate sale analytic account',
    )
