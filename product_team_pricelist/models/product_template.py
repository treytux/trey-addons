###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    team_pricelist_ids = fields.One2many(
        comodel_name='product.team.pricelist',
        inverse_name='product_id',
        string='Sales Team Pricelist',
    )
