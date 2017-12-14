# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrderLineAgent(models.Model):
    _inherit = 'sale.order.line.agent'

    @api.depends('sale_line.price_subtotal', 'sale_line.discount')
    def _compute_amount(self):
        return super(SaleOrderLineAgent, self)._compute_amount()
