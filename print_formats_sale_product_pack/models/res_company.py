###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_report_show_pack = fields.Boolean(
        string='Show pack lines in sale reports',
    )
