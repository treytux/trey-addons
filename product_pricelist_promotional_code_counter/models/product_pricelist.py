# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class product_pricelist(models.Model):
    _inherit = "product.pricelist"

    code_counter = fields.Integer(
        string='Available codes')
    code_unique_partner = fields.Boolean(
        string='Unique per partner',
        help='Code unique per partner, only one use per partner.')

    @api.one
    def substract_coupon(self):
        if not self.code_unique_partner:
            self.code_counter -= 1

    @api.one
    def add_coupon(self):
        if not self.code_unique_partner:
            self.code_counter += 1

    @api.one
    def compute_coupons_number(self, partner):
        orders = self.env['sale.order'].search([
            ('pricelist_id', '=', self.id),
            ('partner_id', '=', partner.id),
            ('state', 'in', (
                'progress',
                'manual',
                'shipping_except',
                'invoice_except',
                'done'))])
        coupons_number = len(orders.ids)
        return coupons_number
