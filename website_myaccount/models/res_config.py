# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    edit_portal_addresses = fields.Boolean(
        string='Edit portal addresses',
        help='Allow to create and edit addresses in customers portal',
        related='website_id.edit_portal_addresses',
        default=True)
