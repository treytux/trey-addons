###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    website_published = fields.Boolean(
        string=('Visible in Website'),
        default=True)
