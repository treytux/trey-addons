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
