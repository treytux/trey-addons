###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    attachment_template_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachment Template Files',
        domain=[('res_model', '=', 'product.template')],
    )

    @api.multi
    def write(self, values):
        for attachment in values.get('attachment_template_ids', []):
            if attachment and attachment[0] == 0:
                attachment[2]['res_model'] = 'product.template'
        return super().write(values)
