# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    website_sale_acquire_discount_applied = fields.Boolean(
        string='Has a acquire payment method discount from website?')
