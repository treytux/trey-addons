# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    request_accept_terms = fields.Boolean(
        related='website_id.request_accept_terms',
        string='Allow request to accept terms of privacy and use.',
        default=True)
