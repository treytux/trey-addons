# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def onchange_product_id(
            self, pricelist_id, product_id, qty, uom_id, partner_id,
            date_order=False, fiscal_position_id=False,
            date_planned=False, name=False, price_unit=False, state='draft'):
        if product_id:
            product = self.env['product.product'].browse(product_id)
            res = super(
                PurchaseOrderLine,
                self.with_context(
                    uom=product.uom_po_id.id)).onchange_product_id(
                        pricelist_id, product_id, qty, uom_id, partner_id,
                        date_order=date_order,
                        fiscal_position_id=fiscal_position_id,
                        date_planned=date_planned, name=name,
                        price_unit=price_unit,
                        state=state)
            return res
