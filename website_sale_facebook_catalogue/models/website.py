###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    company_brand = fields.Char(
        string='Company Brand',
        help='Generic brand for products to be shown in Facebook catalogue.',
    )
    id_prefix = fields.Char(
        string='Product ID prefix',
        help='Prefix por the products ID shown in Facebook catalogue.',
    )
