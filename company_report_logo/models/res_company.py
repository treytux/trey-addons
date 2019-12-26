###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class Company(models.Model):
    _inherit = ['res.company']

    report_logo = fields.Binary(
        string='Logo',
        attachment=True,
        help='Adds logo for reports'
    )
