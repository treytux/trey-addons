###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductSetupOption(models.Model):
    _name = 'product.setup.option'
    _description = 'Product setup option'

    name = fields.Char(
        string='Name',
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    quantity = fields.Float(
        string='Quantity',
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            if line.name:
                continue
            if not line.product_id:
                continue
            line.name = line.product_id.name
