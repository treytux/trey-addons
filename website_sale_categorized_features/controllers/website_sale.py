###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.http import request


class WebsiteSale(main.WebsiteSale):
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

    def get_features(self, category):
        if not category:
            return None
        if isinstance(category, (str)):
            category = request.env['product.public.category'].browse(
                int(category))
        return category.feature_ids

    def _get_available_feature_values(self, tmpl_ids, feature_ids=None):
        if not tmpl_ids:
            return {}
        Line = request.env['product.template.feature.line'].sudo()
        domain = [('template_id', 'in', tmpl_ids.ids)]
        if feature_ids:
            domain.append(('feature_id', 'in', feature_ids))
        lines = Line.search(domain)
        res = {}
        for line in lines:
            fid = line.feature_id.id
            if fid not in res:
                res[fid] = set()
            res[fid].update(line.value_ids.ids)
        return res

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        res = super().shop(
            page=page, category=category, search=search, ppg=ppg, **post)
        features = self.get_features(category)
        applied_feature_values = []
        available_values = []
        if features:
            attrib_list = request.httprequest.args.getlist('attrib')
            attrib_values = [[
                int(x) for x in v.split('-')] for v in attrib_list if v]
            domain = self._get_search_domain(search, category, attrib_values)
            Product = request.env['product.template'].with_context(
                bin_size=True)
            products = Product.search(
                domain, order=self._get_search_order(post))
            available_values = self._get_available_feature_values(
                products, features.ids)
            if ppg:
                try:
                    ppg = int(ppg)
                except ValueError:
                    ppg = main.PPG
                post['ppg'] = ppg
            else:
                ppg = main.PPG
            arg_feature = request.httprequest.args.getlist('feature')
            applied_features = arg_feature and [
                list(map(int, v.split('-'))) for v in arg_feature if v] or []
            applied_feature_values = list(set(
                [v[1] for v in applied_features])) if applied_features else []
            feature_domain = self.get_feature_domain(applied_features)
            if feature_domain and len(feature_domain) > 0:
                domain = request.website.sale_product_domain()
                domain += feature_domain
                if category:
                    domain += [('public_categ_ids', 'child_of', int(category))]
                env = request.env
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
                            domain += [(
                                'attribute_line_ids.value_ids', 'in', ids)]
                            attrib = value[0]
                            ids = [value[1]]
                    if attrib:
                        domain += [('attribute_line_ids.value_ids', 'in', ids)]
                keep = QueryURL(
                    '/shop', category=category and int(category),
                    search=search,
                    attrib=attrib_list, feature=arg_feature)
                if category:
                    if isinstance(category, (str)):
                        PublicCateg = request.env['product.public.category']
                        category = PublicCateg.browse(int(category))
                    url = '/shop/category/%s' % slug(category)
                else:
                    url = '/shop'
                product_count = env['product.template'].search_count(domain)
                pager = request.website.pager(
                    url=url, total=product_count, page=page,
                    step=ppg, scope=7, url_args=post)
                pricelist_context, pricelist = self._get_pricelist_context()
                product_obj = env['product.template'].with_context(
                    bin_size=True)
                search_product = product_obj.search(
                    domain, offset=pager['offset'],
                    order=self._get_search_order(post))
                offset = pager['offset']
                products = search_product[offset: offset + ppg]
                res.qcontext.update({
                    'pager': pager,
                    'bins': TableCompute().process(products, ppg),
                    'products': products,
                    'keep': keep,
                    'order_feature': post.get('order'),
                })
        res.qcontext.update({
            'available_values': available_values,
            'features': features,
            'features_set': applied_feature_values,
        })
        return res
