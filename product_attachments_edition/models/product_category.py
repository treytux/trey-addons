###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    attachment_category_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachment Files',
        domain=[('res_model', '=', 'product.category')],
    )

    @api.multi
    def write(self, values):
        for attachment in values.get('attachment_category_ids', []):
            if attachment and attachment[0] == 0:
                attachment[2]['res_model'] = 'product.category'
        return super().write(values)
