# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        help='This pricelist only be necessary when you create the invoice '
             'and it can not be obtained automatically')


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_price_unit_invoice(self, move_line, type):
        product = move_line.product_id
        sale_line = (move_line.procurement_id and
                     move_line.procurement_id.sale_line_id or False)
        purchase_line = (move_line.purchase_line_id and
                         move_line.purchase_line_id or False)
        picking = move_line.picking_id
        uom_id = product.uom_id.id
        uos_id = product.uos_id and product.uos_id.id or False
        coeff = product.uos_coeff
        model_line = sale_line if sale_line else purchase_line
        msg = _('The pricelist can not be obtained automatically. You must '
                'assign a pricelist on the picking before generating the '
                'invoice.')
        if (model_line and model_line.product_id and
                model_line.product_id.id == product.id):
            price = model_line.price_unit
            if uos_id and uom_id != uos_id and coeff != 0:
                price_unit = price / coeff
                return price_unit
            return model_line.price_unit
        if picking:
            pricelist = None
            if picking.sale_id:
                pricelist = picking.sale_id.pricelist_id
            if move_line.purchase_line_id:
                pricelist = move_line.purchase_line_id.order_id.pricelist_id
            if picking.pricelist_id:
                pricelist = picking.pricelist_id
            if not pricelist:
                raise exceptions.Warning(msg)
            price = pricelist.price_get(
                product.id, move_line.product_qty)[pricelist.id]
            return price
        if move_line.purchase_line_id:
            pricelist = move_line.purchase_line_id.order_id.pricelist_id
            price = pricelist.price_get(
                product.id, move_line.product_qty)[pricelist.id]
            return price
        else:
            raise exceptions.Warning(msg)
        return super(StockMove, self)._get_price_unit_invoice(move_line, type)
