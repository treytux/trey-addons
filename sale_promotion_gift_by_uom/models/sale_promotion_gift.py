# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class SalePromotionGift(models.Model):
    _inherit = 'sale.promotion.gift'

    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Product uom')


class SaleFinalGift(models.Model):
    _inherit = 'sale.final.gift'

    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Product uom')
