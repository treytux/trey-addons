# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class Website(models.Model):
    _inherit = 'website'

    allow_sale_out_of_stock = fields.Boolean(
        string='Allow sale out of stock',
        default=True)


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    allow_sale_out_of_stock = fields.Boolean(
        related='website_id.allow_sale_out_of_stock',
        string='Allow sale out of stock')
