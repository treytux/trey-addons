# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    shop_products_per_comparison = fields.Integer(
        string=u'Products per Comparison',
        related='website_id.shop_products_per_comparison',
        store=True,
        default=3
    )
