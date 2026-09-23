# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

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
        compute='_compute_bom_line_price',
        digits=dp.get_precision('Product Price'),
    )
    bom_lst_price = fields.Float(
        string='Total Price',
        compute='_compute_bom_line_price',
        digits=dp.get_precision('Product Price'),
    )

    @api.multi
    @api.depends('product_qty', 'product_id', 'product_id.lst_price',
                 'product_id.standard_price')
    def _compute_bom_line_price(self):
        for line in self:
            line.bom_lst_price = (
                line.product_qty * line.product_id.lst_price)
            line.bom_prod_price = (
                line.product_qty * line.product_id.standard_price)
