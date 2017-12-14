# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class WebsiteRouteExclude(models.Model):
    _name = 'website.route.exclude'
    _description = 'Website Routes Exclude'

    @api.model
    def _get_available_routes_exclude(self):
        res = []
        all_routes = self.env['website'].get_all_routes()
        for route in all_routes:
            res.append((route, route))
        res = sorted(res, key=lambda tuple: tuple[0])
        return res

    website_id = fields.Many2one(
        comodel_name='website',
        string='Website')
    route = fields.Selection(
        selection=_get_available_routes_exclude,
        string='Excluded routes',
        required=True)
