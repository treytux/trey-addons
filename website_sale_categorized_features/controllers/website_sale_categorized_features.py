# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class WebSiteSale(main.website_sale):
    def get_feature_values(self, features):
        feature_values = {}
        for f in features:
            key = f[0]
            if key not in feature_values:
                feature_values[key] = []
        for f in features:
            feature_values[f[0]].append(f[1])
        return feature_values

    def get_feature_domain(self, features):
        feature_values = self.get_feature_values(features)
        feature_domain = None
        for f in feature_values:
            if feature_domain:
                feature_domain += [
                    ('feature_line_ids.value_ids', 'in', feature_values[f])]
            else:
                feature_domain = [
                    ('feature_line_ids.value_ids', 'in', feature_values[f])]
        return feature_domain

    @http.route(['/shop',
                 '/shop/page/<int:page>',
                 '/shop/category/<model("product.public.category"):category>',
                 '/shop/category/<model("product.public.category"):category>'
                 '/page/<int:page>'],
                type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', **post):
        res = super(WebSiteSale, self).shop(
            page=page, category=category, search=search, **post)

        category_features = category.feature_ids if category else None
        applied_feature_values = []
        if category_features:
            arg_feature = request.httprequest.args.getlist('feature')
            applied_features = arg_feature and [
                map(int, v.split("-")) for v in arg_feature if v] or []
            applied_feature_values = set(
                [v[1] for v in applied_features]) if applied_features else []
            feature_domain = self.get_feature_domain(applied_features)
            if feature_domain and len(feature_domain) > 0:
                domain = request.website.sale_product_domain()
                domain += feature_domain
                if category:
                    domain += [('public_categ_ids', 'child_of', int(category))]
                env = request.env
                attrib_list = request.httprequest.args.getlist('attrib')
                attrib_values = [
                    map(int, v.split("-")) for v in attrib_list if v]
                if attrib_values:
                    attrib = None
                    ids = []
                    for value in attrib_values:
                        if not attrib:
                            attrib = value[0]
                            ids.append(value[1])
                        elif value[0] == attrib:
                            ids.append(value[1])
                        else:
                            domain += [('attribute_line_ids.value_ids', 'in',
                                        ids)]
                            attrib = value[0]
                            ids = [value[1]]
                    if attrib:
                        domain += [('attribute_line_ids.value_ids', 'in', ids)]
                keep = main.QueryURL(
                    '/shop', category=category and int(category),
                    search=search,
                    attrib=attrib_list, feature=arg_feature)
                url = "/shop"
                product_count = env['product.template'].search_count(domain)
                pager = request.website.pager(
                    url=url, total=product_count, page=page,
                    step=main.__dict__['PPG'], scope=7, url_args=post)
                products = env['product.template'].search(
                    domain, limit=main.__dict__['PPG'], offset=pager['offset'],
                    order='website_published desc, website_sequence desc')
                table = main.table_compute()
                res.qcontext['pager'] = pager
                res.qcontext['bins'] = table.process(products)
                res.qcontext['products'] = products
                res.qcontext['keep'] = keep
        res.qcontext['features'] = category_features
        res.qcontext['features_set'] = applied_feature_values
        return res
