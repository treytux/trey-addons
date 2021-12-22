###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductSetupLine(models.Model):
    _name = 'product.setup.line'
    _description = 'Product setup line'
    _order = 'sequence, name'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    categ_id = fields.Many2one(
        comodel_name='product.setup.category',
        string='Category',
        required=True,
    )
    property_ids = fields.Many2many(
        string='Properties',
        comodel_name='product.setup.property',
        relation='product_setup_line2product_setup_property_rel',
        column1='line_id',
        column2='property_id',
    )
    required = fields.Boolean(
        string='Required',
        default=True,
    )
    quantity_min = fields.Float(
        string='Quantity Min',
        default=1,
    )
    quantity_max = fields.Float(
        string='Quantity Max',
        default=1,
    )
    quantity_max_multiple = fields.Many2one(
        comodel_name='product.setup.category',
        string='Multiple of',
    )
    quantity_max_sum = fields.Many2one(
        comodel_name='product.setup.category',
        string='Sum with',
    )

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        for line in self:
            if line.name or not line.categ_id:
                continue
            line.name = line.categ_id.name

    @api.onchange('quantity_min', 'quantity_max')
    def onchange_quantity(self):
        if self.quantity_min > self.quantity_max:
            self.quantity_max = self.quantity_min
