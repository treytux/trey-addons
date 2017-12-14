# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


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
