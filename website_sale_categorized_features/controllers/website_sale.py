###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    def _get_features(self, category):
        if not category or not category.exists():
            return request.env['product.feature']
        return category.feature_ids

    def _get_applied_feature_value_ids(self):
        arg_feature = request.httprequest.args.getlist('feature')
        applied = []
        for v in arg_feature:
            if not v:
                continue
            parts = v.split('-')
            if len(parts) != 2:
                continue
            try:
                applied.append(int(parts[1]))
            except ValueError:
                continue
        return set(applied)

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
            feature_id = line.feature_id.id
            if feature_id not in res:
                res[feature_id] = set()
            res[feature_id].update(line.value_ids.ids)
        return res

    @http.route()
    def shop(
        self, page=0, category=None, search='', min_price=0.0, max_price=0.0,
            ppg=False, **post):
        res = super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            **post
        )
        qcontext = getattr(res, 'qcontext', None)
        if not qcontext:
            return res
        features = self._get_features(qcontext.get('category'))
        if not features:
            qcontext['features'] = features
            qcontext['available_values'] = {}
            qcontext['features_set'] = set()
            return res
        search_product = qcontext.get('search_product')
        qcontext['features_set'] = self._get_applied_feature_value_ids()
        if not search_product:
            qcontext['features'] = features
            qcontext['available_values'] = {}
            return res
        available_values = self._get_available_feature_values(
            search_product, features.ids
        )
        features = features.filtered(
            lambda f: bool(available_values.get(f.id))
        )
        qcontext['features'] = features
        qcontext['available_values'] = available_values
        return res
