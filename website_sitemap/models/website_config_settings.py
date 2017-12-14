# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, _


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    expiry_time = fields.Integer(
        related='website_id.expiry_time',
        string='Cache Time',
        help='Sitemap cache time in hours.',
        default=12)
    default_changefreq = fields.Selection(
        related='website_id.default_changefreq',
        string='Default Frequence',
        default='daily')
    default_priority = fields.Float(
        related='website_id.default_priority',
        string='Default Priority',
        help='Must be between 0.0 and 1.0',
        digits=(2, 1),
        default=0.5)
    excluded_urls = fields.Text(
        related='website_id.excluded_urls',
        string='Excluded URLs',
        help='Excluded URLs, one URL per line')
    excluded_route_ids = fields.One2many(
        related='website_id.excluded_route_ids',
        comodel_name='website.route.exclude',
        inverse_name='website_id',
        string='Excluded Routes')
    route_param_ids = fields.One2many(
        related='website_id.route_param_ids',
        comodel_name='website.route.param',
        inverse_name='website_id',
        string='Route Parameters')

    @api.onchange('default_priority')
    def onchange_default_priority(self):
        if self.default_priority < 0 or self.default_priority > 1.0:
            self.default_priority = 0.5
            title = _('Wrong value')
            message = _('Priority must be between 0.0 and 1.0')
            return {'warning': {'title': title, 'message': message}}
