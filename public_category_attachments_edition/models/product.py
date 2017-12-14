# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        string="Attachment Files",
        domain=[('res_model', '=', 'product.public.category')],
        required=False)

    @api.one
    def write(self, values):
        if values.get('attachment_ids'):
            for attachment in values['attachment_ids']:
                if attachment[0] == 0:
                    attachment[2]['res_model'] = 'product.public.category'
        return super(ProductPublicCategory, self).write(values)
