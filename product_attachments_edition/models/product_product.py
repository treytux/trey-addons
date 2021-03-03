###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    attachment_product_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachment Product Files',
        domain=[('res_model', '=', 'product.product')],
    )

    @api.multi
    def write(self, values):
        for attachment in values.get('attachment_product_ids', []):
            if attachment and attachment[0] == 0:
                attachment[2]['res_model'] = 'product.product'
        return super().write(values)
