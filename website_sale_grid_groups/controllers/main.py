###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, http
from odoo.addons.website_sale.controllers.main import QueryURL
from odoo.addons.website_sale_product_grid.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    def _get_grids_domain(self, search):
        domain = [('website_published', '=', True)]
        if search:
            domain += [('name', 'ilike', search)]
        return domain

    @http.route(['/shop/grids'], type='http', auth='public', website=True)
    def grids(self, **post):
        grid_obj = request.env['grid.group']
        domain = self._get_grids_domain(post.get('search'))
        if post.get('grid'):
            grid = grid_obj.browse(int(post['grid']))
            if not grid:
                raise exceptions.UserError(_(
                    'Not grid found for id %s.' % int(post['grid'])))
            main_attr = grid.main_attribute_id
            product_tmpls = request.env['product.template'].search([
                ('id', 'in', grid.product_ids.ids),
                ('website_published', '=', True)
            ], order='sequence')
            grid_data = self._fill_grid(product_tmpls, main_attr)
            values = {
                'grid': grid,
                'grid_data': grid_data,
                'main_attr_values': self._get_main_attr_value_ids(
                    grid_data, grid.main_attribute_id.value_ids),
                'main_attribute_id': grid.main_attribute_id,
                'cart_quantities': self._get_cart_quantities(),
            }
            return request.render(
                'website_sale_product_grid.products_grid', values)
        values = {
            'grids': grid_obj.sudo().search(domain),
            'keep': QueryURL('/shop/grids', grid=[]),
        }
        if post.get('search'):
            values.update({'search': post.get('search')})
        return request.render('website_sale_grid_groups.grids', values)
