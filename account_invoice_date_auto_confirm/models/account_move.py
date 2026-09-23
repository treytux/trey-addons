###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _cron_auto_confirm_draft_invoices(self, confirm_past_date=False):
        today = fields.Date.context_today(self)
        domain = [('state', '=', 'draft')]
        if confirm_past_date:
            domain.append(('invoice_date', '<=', today))
        else:
            domain.append(('invoice_date', '=', today))
        invoices = self.search(domain)
        for invoice in invoices:
            try:
                with self.env.cr.savepoint():
                    invoice.action_post()
            except UserError as error:
                _logger.warning(
                    'Could not confirm invoice %s: %s', invoice.id, error)
