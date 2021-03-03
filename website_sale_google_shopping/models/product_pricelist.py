###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    effective_date_start = fields.Datetime(
        string='Google Shopping date start',
    )
    effective_date_end = fields.Datetime(
        string='Google Shopping date end',
    )
