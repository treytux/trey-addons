# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    coupon_ids = fields.Many2many(
        string='Coupon',
        comodel_name='coupon',
        relation='coupon2sale_order_rel',
        column1='order_id',
        column2='coupon_id',
        readonly=True,
        states={'draft': [('readonly', False)]})

    @api.one
    def clean_coupons(self):
        if self.state == 'draft':
            for line in self.order_line:
                if line.coupon_id:
                    line.unlink()

    @api.multi
    def allow_use(self):
        for coupon in self.coupon_ids:
            if len(self.coupon_ids) > 1 and not coupon.combinable:
                raise exceptions.Warning(_(
                    'The coupon {0} can not be combined, you should use it '
                    'alone or remove it from the list of coupons.').format(
                    coupon.name))
            if coupon.use_type == 'all':
                if coupon.use_count > coupon.use_max:
                    raise exceptions.Warning(_(
                        'You can not assign the {0} coupon; it has exceeded '
                        'the maximum number of uses.').format(coupon.name))
            elif coupon.use_type == 'salesman':
                for line_salesman in coupon.use_salesman_ids:
                    if self.user_id not in line_salesman.salesman_id:
                        raise exceptions.Warning(_(
                            'You do not allowed to apply the coupon {0}.'
                            ).format(coupon.name))
                    if line_salesman.salesman_id.id == self.user_id.id:
                        if (line_salesman.use_count_salesman >
                                line_salesman.use_max_salesman):
                            raise exceptions.Warning(_(
                                'You can not assign the {0} coupon; the '
                                'salesman it has exceeded the maximum number '
                                'of uses.').format(coupon.name))

    @api.one
    def apply_coupons(self):
        self.allow_use()
        self.clean_coupons()
        if self.state == 'draft':
            for coupon in self.coupon_ids:
                for line in coupon.line_ids:
                    fnc_name = 'apply_coupon_%s' % str(
                        line.ttype).replace('-', '_')
                    if not hasattr(self, fnc_name):
                        msg = 'No have a method "%s" for apply coupon type %s'
                        raise exceptions.Warning(_(msg) % (
                            fnc_name, line.ttype))
                    fnc = getattr(self, fnc_name)
                    if not fnc(line):
                        self.coupon_ids = [(3, coupon.id)]

    @api.one
    def apply_coupon_dto_total(self, coupon_line):
        total = sum([l.price_subtotal
                     for l in self.order_line if not l.coupon_id])
        uom = (coupon_line.product_id and
               coupon_line.product_id.uom_id or
               self.env.ref('product.product_uom_unit'))
        line_taxes = list(set(
            [l.tax_id for l in self.order_line if not l.coupon_id]))
        tax_ids = []
        for taxs in line_taxes:
            for t in taxs:
                tax_ids.append(t.id)
        line_tax = [(6, 0, tax_ids)]
        data_line = {
            'order_id': self.id,
            'coupon_id': coupon_line.coupon_id.id,
            'name': coupon_line.name,
            'product_id': (coupon_line.product_id and
                           coupon_line.product_id.id or None),
            'product_uom': uom.id,
            'product_uom_qty': 1.0,
            'price_unit': total * (coupon_line.total_dto/100) * -1,
            'tax_id': line_tax}
        self.env['sale.order.line'].create(data_line)
        return True

    @api.one
    def apply_coupon_product_to_gift(self, coupon_line):
        line_taxes = list(set(
            [l.tax_id for l in self.order_line if not l.coupon_id]))
        tax_ids = []
        for taxs in line_taxes:
            for t in taxs:
                tax_ids.append(t.id)
        line_tax = [(6, 0, tax_ids)]
        for gift in coupon_line.gift_ids:
            data_line = {
                'order_id': self.id,
                'coupon_id': coupon_line.coupon_id.id,
                'product_id': gift.product_id and gift.product_id.id,
                'product_uom': gift.uom_id.id,
                'product_uom_qty': gift.quantity,
                'price_unit': 0,
                'tax_id': line_tax}
            self.env['sale.order.line'].create(data_line)
        return True

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        res.apply_coupons()
        return res

    @api.one
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.apply_coupons()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    coupon_id = fields.Many2one(
        comodel_name='coupon',
        string='Coupon',
        readonly=True,
        states={'draft': [('readonly', False)]})
