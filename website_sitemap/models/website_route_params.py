# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, _


class WebsiteRouteParams(models.Model):
    _name = 'website.route.param'
    _description = 'Website Routes Params'

    @api.model
    def _get_available_routes(self):
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
        selection=_get_available_routes,
        string='Route',
        required=True)
    changefreq = fields.Selection(
        selection=[
            ('always', 'Always'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
            ('never', 'Never'),
        ],
        string='Frequence',
        default='daily',
        required=True)
    priority = fields.Float(
        string='Priority',
        help='Must be between 0.0 and 1.0',
        digits=(2, 1),
        default=0.5,
        required=True)

    @api.onchange('priority')
    def onchange_priority(self):
        if self.priority < 0 or self.priority > 1.0:
            self.priority = 0.5
            title = _('Wrong value')
            message = _('Priority must be between 0.0 and 1.0')
            return {'warning': {'title': title, 'message': message}}
