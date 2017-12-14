# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Product uom')

    #    Comentada para que se pueda seleccionar alguna unidad cuando se
    # rellena la categoria
    # @api.multi
    # def product_id_change(self, product_id):
    #     '''Inherit function for the domain field unit of measure
    #     includes only
    #     one of the units of the table UoM prices or the unit of measure by
    #     default.'''
    #     res = super(PricelistItem, self).product_id_change(product_id)
    #     product = self.env['product.product'].browse(product_id)
    #     if 'domain' not in res:
    #         res['domain'] = {}
    #     res['domain']['uom_id'] = [
    #         ('id', 'in', [x.uom_id.id for x in product.uom_price_ids]
    #             + [product.uom_id.id])]
    #     return res
