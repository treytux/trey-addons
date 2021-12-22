###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductSetupGroup(models.Model):
    _name = 'product.setup.group'
    _description = 'Product setup group'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    name = fields.Char(
        string='Name',
        translate=True,
        required=True,
    )
    description = fields.Html(
        string='Description',
        translate=True,
    )
    product_tmpl_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='setup_group_id',
        string='Product templates',
    )
    setup_property_ids = fields.Many2many(
        string='Properties',
        comodel_name='product.setup.property',
        relation='product_setup_group2setup_property_rel',
        column1='product_setup_group',
        column2='property_id',
    )
    setup_property_incompatible_ids = fields.Many2many(
        string='Incompatible',
        comodel_name='product.setup.property',
        relation='product_setup_group2setup_property_incompatible_rel',
        column1='product_setup_group',
        column2='property_id',
    )
