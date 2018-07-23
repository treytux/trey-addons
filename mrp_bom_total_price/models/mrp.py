# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields
from openerp.addons import decimal_precision as dp


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def _bom_price_total(self):
        for bom in self:
            bom.bom_prod_price_total = sum(
                [l.bom_prod_price for l in bom.bom_line_ids])

    @api.multi
    def _compute_bom_lst_price_total(self):
        for bom in self:
            bom.bom_lst_price_total = sum(bom.mapped(
                'bom_line_ids.bom_lst_price'))

    bom_prod_price_total = fields.Float(
        string='Total Cost',
        compute='_bom_price_total',
        digits=dp.get_precision('Product Price'),
    )
    bom_lst_price_total = fields.Float(
        string='Total Price',
        compute='_compute_bom_lst_price_total',
        digits=dp.get_precision('Product Price'),
    )


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.multi
    @api.depends('product_qty', 'product_id', 'product_id.standard_price')
    def _product_price_total(self):
        for line in self:
            line.bom_prod_price = (
                line.product_qty * line.product_id.standard_price)

    @api.multi
    @api.depends('product_qty', 'product_id', 'product_id.lst_price')
    def _compute_bom_lst_price(self):
        for line in self:
            line.bom_lst_price = (
                line.product_qty * line.product_id.lst_price)

    standard_price = fields.Float(
        string='Cost Price',
        related='product_id.standard_price',
        readonly=True,
        digits=dp.get_precision('Product Price'),
    )
    lst_price = fields.Float(
        string='Public Price',
        related='product_id.lst_price',
        readonly=True,
        digits=dp.get_precision('Product Price'),
    )
    bom_prod_price = fields.Float(
        string='Total Cost',
        compute='_product_price_total',
        digits=dp.get_precision('Product Price'),
    )
    bom_lst_price = fields.Float(
        string='Total Price',
        compute='_compute_bom_lst_price',
        digits=dp.get_precision('Product Price'),
    )
