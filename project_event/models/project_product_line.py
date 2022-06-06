###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectProductLine(models.Model):
    _name = 'project.product.line'
    _description = 'Project product line for events'

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    name = fields.Char(
        string='Description',
    )
    quantity = fields.Float(
        string='Quantity',
        default=1,
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            if not line.product_id:
                continue
            line.name = line.product_id.name
