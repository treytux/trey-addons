# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    def render(self, cr, uid, id, reference, amount, currency_id, tx_id=None,
               partner_id=False, partner_values=None, tx_values=None,
               context=None):
        if reference != '/':
            transaction_id = self.pool.get('payment.transaction').search(
                cr, uid, [('reference', '=', reference)], limit=1)
            if transaction_id:
                transaction = self.pool.get('payment.transaction').browse(
                    cr, uid, transaction_id)
                if transaction.sale_order_id:
                    tx_values['reference'] = transaction.sale_order_id.name
        return super(PaymentAcquirer, self).render(
            cr, uid, id, reference, amount, currency_id, tx_id, partner_id,
            partner_values, tx_values, context)
