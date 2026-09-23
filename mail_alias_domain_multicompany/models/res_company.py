###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    alias_domain = fields.Char(
        string='Alias Domain',
        help='Defatult domain to use for sending emails to this company',
    )
