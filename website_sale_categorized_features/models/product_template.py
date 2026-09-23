###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    feature_line_ids = fields.One2many(
        comodel_name='product.template.feature.line',
        inverse_name='template_id',
        string='Feature Line',
    )
