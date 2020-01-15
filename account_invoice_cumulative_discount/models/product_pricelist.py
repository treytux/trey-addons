# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    cumulative_discount_ids = fields.One2many(
        comodel_name='product.pricelist.cumulative',
        inverse_name='item_id',
        string='Cumulative Discounts',
    )
    without_discount = fields.Boolean(
        compute='_compute_without_discount',
        string='Discount Policy',
        store=True,
    )

    def _get_item_discount(self):
        for item in self:
            discount = ''
            for value in item.cumulative_discount_ids:
                sign = '+'
                if value.discount < 0.0:
                    sign = '-'
                discount += '%s%s' % (sign, value.discount)
            return discount

    def _get_item_name(self):
        for item in self:
            description = ''
            for value in item.cumulative_discount_ids:
                sign = '+'
                if value.discount < 0.0:
                    sign = '-'
                description += '%s%s %s ' % (
                    sign, value.discount, value.name)
            return description

    @api.depends('categ_id', 'product_tmpl_id', 'product_id', 'compute_price',
                 'fixed_price', 'pricelist_id', 'percent_price',
                 'price_discount', 'price_surcharge')
    def _get_pricelist_item_name_price(self):
        super()._get_pricelist_item_name_price()
        for item in self:
            if not item.without_discount and item.cumulative_discount_ids:
                item.price = item._get_item_name()

    @api.depends('pricelist_id.discount_policy')
    def _compute_without_discount(self):
        for item in self:
            item.without_discount = \
                item.pricelist_id.discount_policy == 'without_discount'


class ProductPricelistCumulative(models.Model):
    _name = "product.pricelist.cumulative"
    _description = "Cumulative discounts"

    name = fields.Char(
        required=True,
        translate=True,
    )
    discount = fields.Float(
        required=True,
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
        default=0.0,
    )
    item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        required=True,
        string='Item',
    )
    sequence = fields.Integer(
        string='Sequence',
        required=True,
        default=0,
    )

    _sql_constraints = [
        ('discount_limit', 'CHECK (discount <= 100.0)',
         'Discount must be lower than 100%.'),
    ]
