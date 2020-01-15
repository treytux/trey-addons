###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api
import logging
_log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        if self._context.get('log_step_sales_create_invoice'):
            self = self.with_context(
                log_step=self._context.get('log_step', 0) + 1)
            _log.info('[%s/%s] Create invoice for sale order' % (
                self._context['log_step'],
                self._context['log_step_sales_create_invoice']))
        return super().create(vals)
