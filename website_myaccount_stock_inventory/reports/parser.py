# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from functools import partial
from openerp import models, api
from operator import itemgetter


class ReportSeason(models.TransientModel):
    _name = 'report.website_myaccount_stock_inventory.report_season'

    @api.model
    def _get_inventory_products(self, season_id=None):
        products = self.env['product.product'].sudo().search([
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
            key = '%s-%s' % (attr_values[0].id, attr_values[1].id)
            inv_products[product.product_tmpl_id.id]['products'][key] = (
                product.qty_available)
            inv_products[product.product_tmpl_id.id]['qty_total'] += (
                product.qty_available)
        inv_products = sorted(inv_products.values(), key=itemgetter('key'))
        return inv_products

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        season_obj = self.env['product.season']
        report = report_obj._get_report_from_name(
            'website_myaccount_stock_inventory.report_season')
        selected_seasons = season_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_seasons,
            'get_inventory_products': partial(
                self._get_inventory_products)}
        report = report_obj.browse(self.ids[0])
        return report.render(
            'website_myaccount_stock_inventory.report_season', docargs)
