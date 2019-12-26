# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        if self.picking_id.picking_type_id.code == 'incoming':
            return super(StockTransferDetails, self).do_detailed_transfer()
        pick_reserv_qtys = {}
        wiz_transfer_qtys = {}
        for move in self.picking_id.move_lines:
            if move.product_id not in pick_reserv_qtys:
                pick_reserv_qtys[move.product_id] = move.reserved_availability
            else:
                pick_reserv_qtys[move.product_id] += move.reserved_availability
        for transf_items in [self.item_ids, self.packop_ids]:
            for item in transf_items:
                if item.product_id not in wiz_transfer_qtys:
                    wiz_transfer_qtys[item.product_id] = item.quantity
                else:
                    wiz_transfer_qtys[item.product_id] += item.quantity
        for product, qty2transfer in wiz_transfer_qtys.iteritems():
            if product not in pick_reserv_qtys:
                raise exceptions.Warning(_(
                    'The product \'%s\' you are trying to transfer is not on '
                    'the stock picking. It is not allowed to transfer '
                    'products not previously reserved on the stock '
                    'picking.') % product.display_name.encode('utf-8'))
            if (
                    product.type == 'product' and
                    qty2transfer > pick_reserv_qtys[product]):
                raise exceptions.Warning(_(
                    'You have reserved %s %s of the product \'%s\' and '
                    'you are trying to transfer %s. This operation is not '
                    'allowed.') % (
                        pick_reserv_qtys[product],
                        product.uom_id.name.encode('utf-8'),
                        product.display_name.encode('utf-8'),
                        wiz_transfer_qtys[product]))
        return super(StockTransferDetails, self).do_detailed_transfer()
