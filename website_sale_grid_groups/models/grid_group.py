###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class GridGroup(models.Model):
    _name = 'grid.group'
    _description = 'Grid Group'
    _inherit = ['product.public.category']
    _order = 'sequence, name, id'

    product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='grid_group_product_template',
        column1='grid_id',
        column2='product_tmpl_id',
        string='Products',
    )
    main_attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Main Attribute',
        help='Set main attribute to display in grid header',
    )
    related_grid_ids = fields.Many2many(
        comodel_name='grid.group',
        relation='grid_related_rel',
        column1='grid_id',
        column2='related_grid_id',
        string='Related Grid',
    )
    website_published = fields.Boolean(
        default=True,
        string='Available on the Website',
    )
