###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductBrand(models.Model):
    _inherit = 'product.brand'

    main_attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Main attribute',
        help='Set main attribute to display in grid header',
    )
    sell_by_grid = fields.Boolean(
        string='Allow to sell by grid',
    )
