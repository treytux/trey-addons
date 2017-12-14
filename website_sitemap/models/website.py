# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields
from openerp.http import request


class Website(models.Model):
    _inherit = 'website'

    expiry_time = fields.Integer(
        string='Expiry time',
        help='Time in hours to keep cached sitemap. Set 0 to disable.'
             ' Default 12.',
        default=12)
    default_changefreq = fields.Selection(
        selection=[
            ('always', 'Always'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
            ('never', 'Never'),
        ],
        string='Default Frequence',
        default='daily')
    default_priority = fields.Float(
        string='Default Priority',
        help='Must be between 0.0 and 1.0',
        digits=(2, 1),
        default=0.5)
    excluded_urls = fields.Text(
        string='Excluded URLs',
        help='Excluded URLs, one URL per line')
    excluded_route_ids = fields.One2many(
        comodel_name='website.route.exclude',
        inverse_name='website_id',
        string='Excluded Routes')
    route_param_ids = fields.One2many(
        comodel_name='website.route.param',
        inverse_name='website_id',
        string='Route Parameters')

    @api.model
    def custom_enumerate_pages(self, query_string=None):
        router = request.httprequest.app.get_db_router(request.db)
        url_set = set()
        urls_to_exclude = request.website.excluded_urls
        excluded_urls = str(urls_to_exclude).split('\n')
        map(str.strip, excluded_urls)
        routes_exclude = request.website.excluded_route_ids
        routes_params = request.website.route_param_ids
        for rule in router.iter_rules():
            changefreq = request.website.default_changefreq
            priority = request.website.default_priority
            if not self.rule_is_enumerable(rule):
                continue
            include_rule = True
            for route in routes_exclude:
                if route.route in rule.endpoint.routing['routes']:
                    include_rule = False
                    break
            for r_param in routes_params:
                if r_param.route in rule.endpoint.routing['routes']:
                    changefreq = r_param.changefreq
                    priority = r_param.priority
            if not include_rule:
                continue
            converters = rule._converters or {}
            if query_string and not converters and (
                    query_string not in
                    rule.build([{}], append_unknown=False)[1]):
                continue
            values = [{}]
            convitems = converters.items()
            gd = (lambda x: hasattr(x[1], 'domain') and (x[1].domain != '[]'))
            convitems.sort(lambda x, y: cmp(gd(x), gd(y)))
            for (i, (name, converter)) in enumerate(convitems):
                newval = []
                for val in values:
                    query = i == (len(convitems) - 1) and query_string
                    for v in converter.generate(
                            request.cr, request.uid, query=query, args=val):
                        newval.append(val.copy())
                        v[name] = v['loc']
                        del v['loc']
                        newval[-1].update(v)
                values = newval
            for value in values:
                domain_part, url = rule.build(value, append_unknown=False)
                page = {'loc': url}
                for key, val in value.items():
                    if key.startswith('__'):
                        page[key[2:]] = val
                if url in ('/sitemap.xml',):
                    continue
                if url in url_set:
                    continue
                url_set.add(url)
                if page.get('loc').strip() in excluded_urls:
                    continue
                if not page.get('priority') and priority:
                    page['priority'] = priority
                if not page.get('changefreq') and changefreq:
                    page['changefreq'] = changefreq
                yield page

    def get_all_pages(self):
        if not request:
            return []
        return self.env['website'].enumerate_pages()

    def get_all_routes(self):
        if not request:
            return []
        all_routes = []
        router = request.httprequest.app.get_db_router(request.db)
        for rule in router.iter_rules():
            if not self.env['website'].rule_is_enumerable(rule):
                continue
            all_routes.extend(rule.endpoint.routing['routes'])
        return all_routes
