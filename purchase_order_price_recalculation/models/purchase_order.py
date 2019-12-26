# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def recalculate_prices(self):
        for purchase in self:
            if not purchase.order_line:
                return
            for line in purchase.order_line:
                if line.product_id:
                    res = line.onchange_product_id(
                        purchase.pricelist_id.id,
                        line.product_id.id,
                        line.product_qty,
                        line.product_uom.id,
                        purchase.partner_id.id,
                        date_order=purchase.date_order,
                        fiscal_position_id=purchase.fiscal_position.id,
                        name=line.name)
                    line.write(res['value'])
