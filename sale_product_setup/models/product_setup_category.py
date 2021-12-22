###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductSetupCategory(models.Model):
    _name = 'product.setup.category'
    _description = 'Product setup category'

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
        inverse_name='setup_categ_id',
        string='Product templates',
    )
    product_template_count = fields.Integer(
        string='Product template count',
        compute='_compute_product_template_count',
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
    )

    @api.depends('product_tmpl_ids')
    def _compute_product_template_count(self):
        for category in self:
            category.product_template_count = len(category.product_tmpl_ids)
