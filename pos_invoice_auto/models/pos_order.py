# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.one
    def action_paid(self):
        res = super(PosOrder, self).action_paid()
        if self.session_id.config_id.auto_invoice:
            self.action_invoice()
            self.invoice_id.signal_workflow('invoice_open')
        return res
