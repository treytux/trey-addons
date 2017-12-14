# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
from functools import partial


class ReportProductsPricelistCustom(models.AbstractModel):
    _name = 'report.products_pricelist_report.products_pricelist_custom'

    @api.multi
    def get_pricelist(self):
        return self.env['product.pricelist'].browse(
            self.env.context['pricelist'])

    @api.multi
    def get_table_pricelist(self, o):
        def _get_description(p):
            return p.description_sale and (
                p.description_sale if len(p.description_sale) <= 79
                else p.description_sale[:79] + '..') or ''

        def _get_price_per_qtys(p, pricelist_id):
            pp = p.product_variant_ids[0]
            price = pp.get_price_by_qty(pricelist_id)
            return price and ([c.encode("utf-8") if isinstance(c, unicode) else
                               c for c in price]) or []

        dict_products = {}
        pricelist_id = self.env.context['pricelist']
        pricelist_obj = self.env['product.pricelist'].browse(pricelist_id)
        for p in self.env['product.template'].browse(o):
            if p.product_variant_ids:
                price = _get_price_per_qtys(p, pricelist_id)
            if not p.product_variant_ids or price == []:
                price = pricelist_obj._price_get_multi(pricelist_obj,
                                                       [(p, 1.0, False)])[p.id]
            if price is False:
                continue
            dict_products[p.id] = {'name': p.name,
                                   'description': _get_description(p),
                                   'price': price}
        return dict_products

    @api.multi
    def render_html(self, data=None):
        template = 'products_pricelist_report.products_pricelist_custom'
        doc = self.env['report']._get_report_from_name(template)
        selected_product = self.env['product.template'].browse(self.ids)[0]
        report = self.env['report'].browse(self.ids[0])
        return report.render(template, {
            'doc_ids': self.ids,
            'doc_model': doc.model,
            'docs': selected_product,
            'get_pricelist': partial(self.get_pricelist),
            'get_table_pricelist': partial(self.get_table_pricelist)})
