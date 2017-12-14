# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_button_confirm(self):
        self.ensure_one()
        res = super(SaleOrder, self).action_button_confirm()
        if self.pricelist_id and self.pricelist_id.code:
                self.pricelist_id.substract_coupon()
        return res

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        res = super(SaleOrder, self).action_cancel()
        if self.pricelist_id and self.pricelist_id.code:
                self.pricelist_id.add_coupon()
        return res
