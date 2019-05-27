###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class WebsiteSaleDocument(models.Model):
    _name = 'website.sale.document'

    name = fields.Char(
        string='Name')
    image = fields.Binary(
        string='Image',
        attachment=True)
    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'website.sale.document')],
        string='Attachments')
    public_categ_ids = fields.Many2many(
        comodel_name='product.public.category')
