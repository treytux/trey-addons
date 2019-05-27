###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    website_sale_document_ids = fields.Many2many(
        comodel_name='website.sale.document')
    website_sale_documents_count = fields.Integer(
        string='Documents Count',
        compute='_compute_website_sale_documents_count')

    @api.model
    def _get_documents_count(self, category):
        return (
            sum([c._get_documents_count(c) for c in category.child_id]) +
            len(category.website_sale_document_ids.ids))

    @api.one
    @api.depends('website_sale_document_ids')
    def _compute_website_sale_documents_count(self):
        self.website_sale_documents_count = self._get_documents_count(self)
