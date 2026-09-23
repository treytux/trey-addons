###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    product_producer_number = fields.Char(
        string='Product Producer No.',
        help='Number given by the Product Producer Registry',
    )
