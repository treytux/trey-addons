# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    website_order = fields.Boolean(
        default=False,
        string='Website order')
    is_cart = fields.Boolean(
        compute='_compute_is_cart',
        store=True)

    @api.one
    @api.depends('website_order', 'state')
    def _compute_is_cart(self):
        self.is_cart = self.website_order and self.state == 'draft'
