# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _

import logging
_log = logging.getLogger(__name__)


class Coupon(models.Model):
    _name = 'coupon'
    _description = 'Coupon Promotion'
    _order = 'sequence'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id)
    date_start = fields.Datetime(
        string='Start',
        default=fields.Datetime.now())
    date_end = fields.Datetime(
        string='End')
    name = fields.Char(
        string='Coupon',
        required=True)
    sequence = fields.Integer(
        string='Sequence')
    combinable = fields.Boolean(
        string='Combinable',
        default=False)
    line_ids = fields.One2many(
        comodel_name='coupon.line',
        inverse_name='coupon_id',
        string='Lines')
    use_type = fields.Selection(
        selection=[
            ('all', 'All'),
            ('salesman', 'Selected salesman')],
        string='Type Limit Use',
        default='all')
    use_max = fields.Integer(
        string='Max uses',
        default=1)
    use_count = fields.Integer(
        string='Used heretofore',
        compute='_compute_use_count',
        readonly=True,
        default=1)
    use_salesman_ids = fields.One2many(
        comodel_name='coupon.salesman',
        inverse_name='coupon_id',
        string='Salesmans')
    order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='coupon2sale_order_rel',
        column1='coupon_id',
        column2='order_id')
    notes = fields.Text(
        string='Notes')

    @api.one
    @api.depends('use_max')
    def _compute_use_count(self):
        self.use_count = len(self.order_ids)


class CouponLine(models.Model):
    _name = 'coupon.line'
    _description = 'Coupon Line Promotion'
    _order = 'sequence'

    coupon_id = fields.Many2one(
        comodel_name='coupon',
        string='Coupon')
    ttype = fields.Selection(
        selection=lambda s: s._get_types(),
        string='Type',
        default=lambda s: s._get_type_default(),
        required=True)
    sequence = fields.Integer(
        string='Sequence')
    total_dto = fields.Float(
        string='Total Dto (%)')
    name = fields.Char(
        string='Description',
        required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    gift_ids = fields.One2many(
        comodel_name='coupon.line.gifts',
        inverse_name='coupon_line_id',
        string='Gift lines')

    @api.model
    def _get_types(self):
        return [('dto-total', _('Total Disc.')),
                ('product-to-gift', _('Product to gift'))]

    @api.model
    def _get_type_default(self):
        return 'dto-total'

    @api.multi
    def order_apply_dto_total(self, order_id):
        self.ensure_one()
        order = self.env['sale.order'].browse(order_id)
        if not order:
            return


class CouponLineGift(models.Model):
    _name = 'coupon.line.gifts'
    _description = 'Coupon Line Gift'

    name = fields.Char(
        string='Name')
    coupon_line_id = fields.Many2one(
        comodel_name='coupon.line',
        string='Coupon line',
        ondelete='cascade',
        required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    quantity = fields.Float(
        string='Quantity',
        required=True)
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='UoM',
        required=True)

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        cr, uid, context = self.env.args
        res = {}
        if 'domain' not in context:
            res['domain'] = {}
        res['domain']['uom_id'] = [
            ('id', 'in', [x.uom_id.id for x in self.product_id.uom_price_ids] +
                [self.product_id.uom_id.id])]
        return res


class CouponSalesman(models.Model):
    _name = 'coupon.salesman'
    _description = 'Coupon salesman'

    name = fields.Char(
        string='Name')
    coupon_id = fields.Many2one(
        comodel_name='coupon',
        string='Coupon',
        ondelete='cascade',
        required=True)
    salesman_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesman',
        required=True)
    use_max_salesman = fields.Integer(
        string='Max uses for salesman',
        required=True,
        default=1)
    period_id = fields.Many2one(
        comodel_name='period',
        string='Period',
        required=True)
    use_count_salesman = fields.Integer(
        string='Used heretofore',
        compute='_compute_use_count_salesman',
        readonly=True,
        default=1)

    @api.one
    @api.depends('use_max_salesman')
    def _compute_use_count_salesman(self):
        if self.salesman_id.exists():
            now = fields.Datetime.now()
            before_time = fields.Datetime.to_string(self.period_id.before(now))
            sql = '''
                SELECT so.id
                FROM sale_order AS so
                LEFT JOIN res_users AS u ON so.user_id = u.id
                LEFT JOIN coupon2sale_order_rel AS rel ON rel.order_id= so.id
                WHERE
                    so.user_id = %s AND
                    rel.coupon_id = %s AND
                    so.create_date >= \'%s\' AND
                    so.create_date <= \'%s\'''' % (
                self.salesman_id.id, self.coupon_id.id, before_time, now)
            self.env.cr.execute(sql)
            order_ids = self.env.cr.fetchall()
            self.use_count_salesman = len(order_ids)
