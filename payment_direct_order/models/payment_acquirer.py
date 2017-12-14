# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.osv import osv
from openerp.tools.float_utils import float_compare

import logging
import pprint

_logger = logging.getLogger(__name__)


class DirectPaymentAcquirer(osv.Model):
    _inherit = 'payment.acquirer'

    def _get_providers(self, cr, uid, context=None):
        providers = super(DirectPaymentAcquirer, self)._get_providers(
            cr, uid, context=context
        )
        providers.append(['direct_order', 'Direct payment'])
        return providers

    def direct_order_get_form_action_url(self, cr, uid, id, context=None):
        return '/payment/direct_order/feedback'

    def _format_direct_order_data(self, cr, uid, context=None):
        post_msg = '''
        <div>
            <h3>Ya tienes tu pedido</h3>
        </div>'''
        return post_msg

    def create(self, cr, uid, values, context=None):
        """ Hook in create to create a default post_msg. This is done in create
        to have access to the name and other creation values. If no post_msg
        or a void post_msg is given at creation, generate a default one. """
        if values.get('name') == 'direct_order' and not values.get('post_msg'):
            values['post_msg'] = self._format_direct_order_data(
                cr, uid, context=context
            )
        return super(DirectPaymentAcquirer, self).create(
            cr, uid, values, context=context
        )


class DirectPaymentTransaction(osv.Model):
    _inherit = 'payment.transaction'

    def _direct_order_form_get_tx_from_data(self, cr, uid, data, context=None):
        reference = data.get('reference')
        tx_ids = self.search(cr, uid, [('reference', '=', reference)],
                             context=context)

        if not tx_ids or len(tx_ids) > 1:
            error_msg = 'received data for reference %s' % (
                pprint.pformat(reference)
            )
            if not tx_ids:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        return self.browse(cr, uid, tx_ids[0], context=context)

    def _direct_order_form_get_invalid_parameters(self, cr, uid, tx, data,
                                                  context=None):
        invalid_parameters = []

        if float_compare(float(data.get('amount', '0.0')), tx.amount, 2) != 0:
            invalid_parameters.append(
                ('amount', data.get('amount'), '%.2f' % tx.amount)
            )
        if data.get('currency') != tx.currency_id.name:
            invalid_parameters.append(
                ('currency', data.get('currency'), tx.currency_id.name)
            )

        return invalid_parameters

    def _direct_order_form_validate(self, cr, uid, tx, data, context=None):
        _logger.info(
            'Validated direct order payment for tx %s: set as pending' % (
                tx.reference))
        return tx.write({'state': 'pending'})
