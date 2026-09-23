###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_banner = fields.Html(
        string='Invoice Banner',
        translate=True,
    )
