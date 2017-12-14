# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    social_instagram = fields.Char(
        string=_('Instagram Account'),
        help=_('Instagram Account URL'),
        related='website_id.social_instagram')
