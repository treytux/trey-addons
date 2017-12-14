# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachment Files',
        domain=[('res_model', '=', 'product.template')],
        required=False)

    @api.one
    def write(self, values):
        if values.get('attachment_ids', False):
            for attachment in values['attachment_ids']:
                if attachment[0] == 0:
                    attachment[2]['res_model'] = 'product.template'
        return super(ProductTemplate, self).write(values)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        string="Attachment Files",
        domain=[('res_model', '=', 'product.category')],
        required=False)

    @api.one
    def write(self, values):
        if values.get('attachment_ids', False):
            for attachment in values['attachment_ids']:
                if attachment[0] == 0:
                    attachment[2]['res_model'] = 'product.category'
        return super(ProductCategory, self).write(values)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    attachment_product_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachment Files',
        domain=[('res_model', '=', 'product.product')],
        required=False)

    @api.one
    def write(self, values):
        if values.get('attachment_product_ids', False):
            for attachment in values['attachment_product_ids']:
                if attachment[0] == 0:
                    attachment[2]['res_model'] = 'product.product'
        return super(ProductProduct, self).write(values)
