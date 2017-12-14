# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.one
    def _bom_price_total(self):
        self.bom_prod_price_total = sum(
            [l.bom_prod_price for l in self.bom_line_ids])

    bom_prod_price_total = fields.Float(
        string='Total price',
        compute='_bom_price_total')


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.one
    @api.depends('product_id')
    def _product_price_total(self):
        self.bom_prod_price = self.product_qty * self.product_id.standard_price

    bom_prod_price = fields.Float(
        string='Product price total',
        compute='_product_price_total')
