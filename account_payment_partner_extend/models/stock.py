# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        res = super(StockPicking, self)._get_invoice_vals(
            key, inv_type, journal_id, move)
        if not len(key) > 1:
            return res
        partner = key[0]
        if inv_type in ('out_invoice', 'out_refund'):
            payment_mode = (
                partner.customer_payment_mode and
                partner.customer_payment_mode.id or False)
        else:
            payment_mode = (
                partner.supplier_payment_mode and
                partner.supplier_payment_mode.id or False)
        res.update({'payment_mode_id': payment_mode})
        return res
