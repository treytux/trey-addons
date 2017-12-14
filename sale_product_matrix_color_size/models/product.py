# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
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
        string='Combinable')
    line_ids = fields.One2many(
        comodel_name='coupon.line',
        inverse_name='coupon_id',
        string='Lines')
    use_type = fields.Selection(
        selection=[
            ('all', 'All'),
            ('partner', 'Selected Partner')],
        string='Type Limit Use',
        default='all')
    use_max = fields.Integer(
        string='Max uses',
        default=1)
    use_count = fields.Integer(
        string='used heretofore',
        compute='_compute_use_count',
        readonly=True,
        default=1)
    use_max_partner = fields.Integer(
        string='Max uses per partner',
        default=1)
    use_partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='product_coupon2res_partner_rel',
        column1='coupon_id',
        column2='partner_id')
    order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='coupon2sale_order_rel',
        column1='coupon_id',
        column2='order_id')

    @api.one
    @api.depends('use_max')
    def _compute_use_count(self):
        self.use_count = len(self.order_ids)

    @api.multi
    def allow_use(self, partner_id):
        self.ensure_one()
        if self.use_type == 'all':
            return True
        elif self.use_type == 'partner':
            return bool(
                [p for p in self.use_partner_ids if p.id == partner_id])
        return None

    @api.multi
    def is_valid(self, order_id):
        self.ensure_one()
        order = self.env['sale.order'].browse(order_id)
        if not self.allow_use(order.partner_id.id):
            return False
        return True

    @api.one
    def apply(self, order_id):
        order = self.env['sale.order'].browse(order_id)
        if not self.allow_use(order.partner_id.id):
            return False
        return True


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
        default=lambda s: s._get_type_default())
    sequence = fields.Integer(
        string='Sequence')
    total_dto = fields.Float(
        string='Total Dto (%)')
    name = fields.Char(string='Description')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')

    @api.model
    def _get_types(self):
        return [('dto-total', 'Dto. Total')]

    @api.model
    def _get_type_default(self):
        return 'dto-total'

    @api.multi
    def order_apply_dto_total(self, order_id):
        self.ensure_one()
        order = self.env['sale.order'].browse(order_id)
        if not order:
            return
