# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _website_product_id_change(self, order_id, product_id, qty=0,
                                   line_id=None):
        res = super(SaleOrder, self)._website_product_id_change(
            order_id, product_id, qty, line_id)
        if line_id and res.get('agents'):
            del res['agents']
        return res
