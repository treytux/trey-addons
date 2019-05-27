# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _quant_create(
            self, qty, move, lot_id=False, owner_id=False,
            src_package_id=False, dest_package_id=False,
            force_location_from=False, force_location_to=False):
        if move.location_id.usage == 'internal':
            raise exceptions.Warning(_(
                'It is not allowed to create negative quants in the system. \n'
                'Please check the current stock of the product \'%s\' because '
                'it is not sufficient for the operation you want to do.' % (
                    move.product_id.display_name)))
        return super(StockQuant, self)._quant_create(
            qty, move, lot_id, owner_id, src_package_id, dest_package_id,
            force_location_from, force_location_to)
