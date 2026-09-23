# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
from openerp import fields, models


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    cookiebot_id = fields.Char(
        related=['website_id', 'cookiebot_id'],
        string='Cookiebot ID',
        help='ID provided by Cookiebot after online registration.',
    )
