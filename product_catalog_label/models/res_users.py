###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    catalog_ids = fields.Many2many(
        comodel_name='product.catalog',
        relation='res_user2product_catalog_rel',
        column1='res_user_id',
        column2='product_catalog_id',
        string='Catalogs',
    )
