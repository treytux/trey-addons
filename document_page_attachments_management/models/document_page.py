###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class DocumentPage(models.Model):
    _inherit = 'document.page'

    attachment_page_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachment Page Files',
        domain=[('res_model', '=', 'document.page')],
    )

    @api.multi
    def write(self, values):
        for attachment in values.get('attachment_page_ids', []):
            if attachment and attachment[0] == 0:
                attachment[2]['res_model'] = 'document.page'
        return super().write(values)
