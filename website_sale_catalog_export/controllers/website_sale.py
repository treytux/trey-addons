###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    def get_categ_child_ids(self, category, child_ids):
        for child in category.child_id:
            child_ids.append(child.id)
            if child.child_id:
                self.get_categ_child_ids(child, child_ids)
        return child_ids

    def get_export_search_domain(self, category_id):
        category = request.env['product.public.category'].browse(category_id)
        categs_ids = [category_id] + self.get_categ_child_ids(category, [])
        return [
            ('public_categ_ids', 'in', categs_ids),
            ('website_published', '=', True),
        ]

    @http.route([
        '/shop/export/category/<category_id>/<string:file_type>',
    ], type='http', auth='public', website=True, csrf=False)
    def products_catalog_export(self, category_id, file_type='pdf'):
        product_tmpls = request.env['product.template'].search(
            self.get_export_search_domain(int(category_id)))
        data = {
            'pricelist_id': request.website.get_current_pricelist().id,
            'active_ids': product_tmpls.ids,
        }
        if file_type == 'pdf':
            report = 'product_catalog_report.report_product_catalog_create'
            pdf = request.env.ref(
                report).sudo().render_qweb_pdf(product_tmpls, data)[0]
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf)),
            ]
            return request.make_response(pdf, headers=pdfhttpheaders)
