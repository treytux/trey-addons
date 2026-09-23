###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    catalog_ids = fields.Many2many(
        comodel_name='product.catalog',
        relation='product_template2product_catalog_rel',
        column1='product_template_id',
        column2='product_catalog_id',
        string='Catalogs',
    )
