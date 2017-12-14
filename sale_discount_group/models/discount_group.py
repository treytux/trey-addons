# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    dto_group_id = fields.Many2one(
        comodel_name='discount.partner.group',
        string='Discount Group')


class DiscountPartnerGroup(models.Model):
    _name = 'discount.partner.group'
    _description = 'Discount Partner Group'

    name = fields.Char(
        string='Group',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id)
    partner_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='dto_group_id',
        string='Disccount Group')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    dto_group_id = fields.Many2one(
        comodel_name='discount.product.group',
        string='Discount Group')


class DiscountProductGroup(models.Model):
    _name = 'discount.product.group'
    _description = 'Discount Product Group'

    name = fields.Char(
        string='Group',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id)
    product_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='dto_group_id',
        string='Disccount Group')


class DiscountGroup(models.Model):
    _name = 'discount.group'
    _description = 'Discount Group'
    _order = 'sequence'

    name = fields.Char(
        string='Group',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id)
    date_start = fields.Datetime(
        string='Start',
        required=True,
        default=fields.Datetime.now())
    date_end = fields.Datetime(
        string='End')
    sequence = fields.Integer(
        string='Sequence')
    base = fields.Selection(
        selection='_price_field_get',
        string='Based on',
        required=False)
    discount = fields.Float(
        string='Discount')
    partner_id = fields.Many2one(
        comodel_name='discount.partner.group',
        string='Partner Group',
        required=True)
    product_id = fields.Many2one(
        comodel_name='discount.product.group',
        string='Product Group',
        required=True)

    def _price_field_get(self):
        return [(t.id, t.name)
                for t in self.env['product.price.type'].search([])]
