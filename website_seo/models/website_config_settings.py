# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    google_site_verification = fields.Char(
        related=['website_id', 'google_site_verification'],
        string='Google site verification',
        help='Google site verification code provided by Search Console.')
