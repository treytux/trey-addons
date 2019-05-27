###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleDocuments(WebsiteSale):
    def _get_documents_search_domain(self, category):
        domain = [('attachment_ids', '!=', False)]
        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]
        return domain

    @http.route([
        '/documents',
        '/documents/category/<model("product.public.category"):category>'],
        type='http', auth='public', website=True)
    def documents(self, category=None, **post):
        domain = self._get_documents_search_domain(category)
        documents = request.env['website.sale.document'].search(domain)
        categories = request.env['product.public.category'].search(
            [('parent_id', '=', False)])
        parent_category_ids = []
        if category:
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id
        values = {
            'documents': documents,
            'categories': categories,
            'category': category,
            'keep': QueryURL(
                '/documents', category=category and int(category)),
            'parent_category_ids': parent_category_ids,
        }
        if category:
            values['main_object'] = category
        return request.render('website_sale_docs.documents', values)
