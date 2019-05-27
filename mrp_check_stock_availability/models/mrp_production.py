# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def _make_consume_line_from_data(
            self, production, product, uom_id, qty, uos_id, uos_qty):
        uom = self.env['product.uom'].browse(uom_id)
        location_src = production.location_src_id
        product = self.env['product.product'].with_context(
            location=location_src.id, compute_child=False).browse(
            product.id)
        if qty <= product.qty_available:
            return super(MrpProduction, self)._make_consume_line_from_data(
                production, product, uom_id, qty, uos_id, uos_qty)
        raise exceptions.Warning(_(
            'Product \'%s\' does not have enough stock in the raw materials '
            'location \'%s\'.\nYou plan to do a move of %s %s but its real '
            'stock is %s %s.') % (
                product.display_name, location_src.complete_name, qty,
                uom.name, product.qty_available, uom.name))
