# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import time
from openerp import models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def onchange_product_id(
            self, pricelist_id, product_id, qty, uom_id, partner_id,
            date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft'):
        res = super(PurchaseOrderLine, self).onchange_product_id(
            pricelist_id, product_id, qty, uom_id, partner_id,
            date_order=date_order, fiscal_position_id=fiscal_position_id,
            date_planned=date_planned, name=name, price_unit=price_unit,
            state=state)
        analytic_account = self.env['account.analytic.default'].account_get(
            product_id=product_id, partner_id=partner_id,
            user_id=self.env.user.id, date=time.strftime('%Y-%m-%d'),
            company_id=self.env.user.company_id.id)
        if analytic_account:
            res['value'].update({
                'account_analytic_id': analytic_account.analytic_id.id,
            })
        return res
