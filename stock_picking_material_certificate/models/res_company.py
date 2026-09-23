###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_conformity_declaration = fields.Html(
        string='Stock Declaration of Conformity',
        translate=True,
    )
