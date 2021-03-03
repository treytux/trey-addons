##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import api, fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    attachment_public_cat_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachment Files',
        domain=[('res_model', '=', 'product.public.category')],
    )

    @api.multi
    def write(self, values):
        for attachment in values.get('attachment_public_cat_ids', []):
            if attachment and attachment[0] == 0:
                attachment[2]['res_model'] = 'product.public.category'
        return super().write(values)
