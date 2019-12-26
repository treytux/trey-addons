# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class MrpProductProduce(models.TransientModel):
    _inherit = 'mrp.product.produce'

    @api.multi
    def do_produce(self):
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        location_src = production.location_src_id
        mrp_stock_type = production.company_id.mrp_stock_type
        for consume_line in self.consume_lines:
            product = self.env['product.product'].with_context(
                location=location_src.id, compute_child=False).browse(
                consume_line.product_id.id)
            product_qty = (
                mrp_stock_type == 'virtual' and product.virtual_available or
                product.qty_available)
            if consume_line.product_qty <= product_qty:
                continue
            raise exceptions.Warning(_(
                'Product \'%s\' does not have enough stock in the raw '
                'materials location \'%s\'.\nYou plan to do a move of %s %s '
                'but its %s stock is %s %s.') % (
                    product.display_name, location_src.complete_name,
                    consume_line.product_qty, product.uom_id.name,
                    mrp_stock_type, product_qty, product.uom_id.name))
        return super(MrpProductProduce, self).do_produce()
