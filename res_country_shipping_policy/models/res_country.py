###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCountry(models.Model):
    _inherit = 'res.country'

    shipping_policy = fields.Text(
        string='Shipping policy for exports',
        translate=True,
    )
