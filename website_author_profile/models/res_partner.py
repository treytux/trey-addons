###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    author_description = fields.Text(
        string='Description',
        help='Author description for the profile page.',
    )
