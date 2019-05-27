# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
from operator import itemgetter
try:
    from openerp.addons.website_myaccount.controllers.main import MyAccount
except ImportError:
    MyAccount = object


class MyAccountStockInventory(MyAccount):
    def _allowed_season(self, season):
        user = request.env['res.users'].browse(request.uid)
        return (season.public or (
            season.agent and user.ecommerce_agent))

    def _get_inventory_seasons(self):
        inv_obj = request.env['stock.inventory.online'].sudo()
        inventories = inv_obj.search([('user_ids', 'in', request.uid)])
        if not inventories:
            return []
        inventory_seasons = {}
        for inventory in inventories:
            for season in inventory.season_ids:
                if self._allowed_season(season):
                    inventory_seasons.setdefault(inventory.id, {
                        'inventory': inventory,
                        'seasons': []})
                    inventory_seasons[inventory.id]['seasons'].append(season)
        return inventory_seasons.values()

    def _render_inventories(self, inventory_seasons):
            return request.website.render(
                'website_myaccount_stock_inventory.inventories', {
                    'inventory_seasons': inventory_seasons})

    @http.route([
        '/my/inventories',
        '/myaccount/inventories',
        '/mis/inventarios',
        '/micuenta/inventarios'
    ], type='http', auth='user', website=True)
    def my_inventories(self, **post):
        inventory_seasons = self._get_inventory_seasons()
        return self._render_inventories(inventory_seasons)

    def _get_inventory_season(self, inventory_id, season_id):
        inventory = request.env['stock.inventory.online'].sudo().browse(
            inventory_id)
        if (
            not inventory or request.uid not in inventory.user_ids.ids or
                season_id not in inventory.season_ids.ids):
            return None, None
        season = request.env['product.season'].sudo().browse(season_id)
        season = self._allowed_season(season) and season or None
        return inventory, season

    def _get_inventory_products(self, season_id=None):
        products = request.env['product.product'].sudo().search([
            ('qty_available', '>', 0),
            ('product_tmpl_id.season_id', '=', season_id)])
        inv_products = {}
        for product in products:
            attr_lines = product.product_tmpl_id.get_sorted_attribute_lines()
            inv_products.setdefault(product.product_tmpl_id.id, {
                'key': product.product_tmpl_id.name,
                'product_tmpl': product.product_tmpl_id,
                'attr_lines': attr_lines,
                'qty_total': 0,
                'products': {}})
            attr_values = product.get_sorted_attribute_values()
            if attr_values:
                key = '%s-%s' % (attr_values[0].id,
                                 attr_values[1].id)
                inv_products[product.product_tmpl_id.id]['products'][key] = (
                    product.qty_available)
                inv_products[product.product_tmpl_id.id]['qty_total'] += (
                    product.qty_available)
            else:
                inv_products[product.product_tmpl_id.id]['qty_total'] = (
                    product.product_tmpl_id.qty_available)
        inv_products = sorted(inv_products.values(), key=itemgetter('key'))
        return inv_products

    def _render_inventory(self, inventory, season, product_tmpls):
            return request.website.render(
                'website_myaccount_stock_inventory.inventory', {
                    'inventory': inventory,
                    'season': season,
                    'product_tmpls': product_tmpls})

    @http.route([
        '/my/inventory/<int:inventory_id>/<int:season_id>',
        '/myaccount/inventory/<int:inventory_id>/<int:season_id>',
        '/mi/inventario/<int:inventory_id>/<int:season_id>',
        '/micuenta/inventario/<int:inventory_id>/<int:season_id>'
    ], type='http', auth='user', website=True)
    def my_inventory(self, inventory_id=None, season_id=None, **post):
        inventory, season = self._get_inventory_season(inventory_id, season_id)
        if not (inventory and season):
            return request.render('website.404')
        product_tmpls = self._get_inventory_products(season.id)
        return self._render_inventory(inventory, season, product_tmpls)

    @http.route([
        '/my/download/season/<int:inventory_id>/<int:season_id>',
        '/myaccount/download/season/<int:inventory_id>/<int:season_id>',
        '/mi/descargar/temporada/<int:inventory_id>/<int:season_id>',
        '/micuenta/descargar/temporada/<int:inventory_id>/<int:season_id>'
    ], type='http', auth='user', website=True)
    def download_season(self, inventory_id, season_id, **post):
        env = request.env
        inventory, season = self._get_inventory_season(inventory_id, season_id)
        if not (inventory and season):
            return request.render('website.404')
        pdf = env['report'].sudo().get_pdf(
            season, 'website_myaccount_stock_inventory.report_season')
        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                          ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)
