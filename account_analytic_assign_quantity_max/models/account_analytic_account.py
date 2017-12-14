# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields
import logging
_log = logging.getLogger(__name__)


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    quantity_max = fields.Float(
        track_visibility='onchange')

    @api.model
    def _prepare_invoice_data(self, contract):
        res = super(AccountAnalyticAccount, self)._prepare_invoice_data(
            contract)
        if contract.exists():
            res['contract_id'] = contract.id
        return res
