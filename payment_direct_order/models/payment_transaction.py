###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import pprint

from odoo import api, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _direct_order_form_get_tx_from_data(self, data):
        reference = data.get('reference')
        tx_ids = self.search([('reference', '=', reference)])
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
        tx_ids._set_transaction_pending()
        return tx_ids

    @api.multi
    def _direct_order_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(
                ('amount', data.get('amount'), '%.2f' % self.amount)
            )
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(
                ('currency', data.get('currency'), self.currency_id.name)
            )
        return invalid_parameters

    def _direct_order_form_validate(self, data):
        _logger.info(
            'Validated direct order payment for tx %s: set as done' % (
                self.reference))
        return self._set_transaction_done()

    def _post_process_after_done(self):
        if (self.acquirer_id.automatic_reconcile
                or self.acquirer_id.provider != 'direct_order'):
            return super()._post_process_after_done()
        if self.sale_order_ids:
            self.sale_order_ids.action_confirm()
        return True
