# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import werkzeug
import openerp.addons.website_sale.controllers.main as main
from openerp import http
from openerp.http import request

PPG = 20  # Products Per Page
PPR = 4  # Products Per Row


class QueryURL(object):
    def __init__(self, path='', **args):
        self.path = path
        self.args = args

    def __call__(self, path=None, **kw):
        if not path:
            path = self.path
        for k, v in self.args.items():
            kw.setdefault(k, v)
        li = []
        for k, v in kw.items():
            if v:
                if isinstance(v, list) or isinstance(v, set):
                    li.append(werkzeug.url_encode([(k, i) for i in v]))
                else:
                    li.append(werkzeug.url_encode([(k, v)]))
        if li:
            path += '?' + '&'.join(li)
        return path


class WebsiteSale(main.website_sale):
    # Sobreescribir funcion para permitir filtrar por caracteristicas
    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/'
        '<int:page>'],
        type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', **post):
        cr, uid, context, pool = (
            request.cr, request.uid, request.context, request.registry)
        domain = request.website.sale_product_domain()
        if search:
            domain += [
                '|', '|', '|',
                ('name', 'ilike', search),
                ('description', 'ilike', search),
                ('description_sale', 'ilike', search),
                ('product_variant_ids.default_code', 'ilike', search)]
        if category:
            domain += [('product_variant_ids.public_categ_ids',
                        'child_of', int(category))]
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        feat_list = request.httprequest.args.getlist('feat')
        feat_values = [map(int, v.split("-")) for v in feat_list if v]
        feat_set = set([v[1] for v in feat_values])

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
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        if feat_values:
            feat = None
            ids = []
            for value in feat_values:
                if not feat:
                    feat = value[0]
                    ids.append(value[1])
                elif value[0] == feat:
                    ids.append(value[1])
                else:
                    domain += [('feature_line_ids.value_ids', 'in', ids)]
                    feat = value[0]
                    ids = [value[1]]
            if feat:
                domain += [('feature_line_ids.value_ids', 'in', ids)]

        keep = QueryURL('/shop', category=category and int(category),
                        search=search, attrib=attrib_list, feat=feat_list)

        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(
                cr, uid, context['pricelist'], context
            )

        product_obj = pool.get('product.template')

        url = "/shop"
        product_count = product_obj.search_count(
            cr, uid, domain, context=context)
        if search:
            post["search"] = search
        # if category:
        #     url = "/shop/category/%s" % slug(category)
        pager = request.website.pager(
            url=url, total=product_count, page=page, step=PPG, scope=7,
            url_args=post
        )
        product_ids = product_obj.search(
            cr, uid, domain, limit=PPG + 10, offset=pager['offset'],
            order='website_published desc, website_sequence desc',
            context=context
        )
        products = product_obj.browse(cr, uid, product_ids, context=context)

        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [], context=context)
        categories = category_obj.browse(
            cr, uid, category_ids, context=context)
        categs = filter(lambda x: not x.parent_id, categories)

        attributes_obj = request.registry['product.attribute']
        attributes_ids = attributes_obj.search(cr, uid, [], context=context)
        attributes = attributes_obj.browse(
            cr, uid, attributes_ids, context=context)

        features_obj = request.registry['product.template.feature']
        features_ids = features_obj.search(cr, uid, [], context=context)
        features = features_obj.browse(cr, uid, features_ids, context=context)

        from_currency = pool.get('product.price.type')._get_field_currency(
            cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id

        def compute_currency(price):
            return pool['res.currency']._compute(
                cr, uid, from_currency, to_currency, price, context=context)

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'bins': main.table_compute().process(products),
            'rows': PPR,
            'styles': styles,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [
                s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode(
                [('attrib', i) for i in attribs]),
            'feat_values': feat_values,
            'feat_set': feat_set,
            'features': features,
            'feat_encode': lambda feats: werkzeug.url_encode(
                [('feat', i) for i in feats]),
        }
        return request.website.render("website_sale.products", values)
