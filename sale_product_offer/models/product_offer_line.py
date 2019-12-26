# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api
import openerp.addons.decimal_precision as dp


class ProductOfferLine(models.Model):
    _name = 'product.offer.line'
    _description = 'Product Offer Line'
    _order = 'date_start desc, date_end desc'
    _rec_name = 'product_id'

    @api.model
    def _get_sale_price(self):
        return self.product_id and self.product_id.lst_price or None

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        copy=True,
        index=True,
    )
    offer_id = fields.Many2one(
        comodel_name='product.offer',
        string='Offer',
        required=True,
        readonly=True,
        ondelete='cascade',
        index=True,
    )
    price_unit = fields.Float(
        string='Unit Price',
        required=True,
        digits_compute=dp.get_precision('Product Price'),
    )
    customer_id = fields.Many2one(
        related='offer_id.customer_id',
        store=True,
        readonly=True,
        index=True,
    )
    date_start = fields.Date(
        related='offer_id.date_start',
        store=True,
        readonly=True,
    )
    date_end = fields.Date(
        related='offer_id.date_end',
        store=True,
        readonly=True,
    )

    @api.one
    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.price_unit = self.product_id.lst_price
