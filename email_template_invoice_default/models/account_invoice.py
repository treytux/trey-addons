# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_sent(self):
        def_template = self.company_id.default_invoice_email_template
        res = super(AccountInvoice, self).action_invoice_sent()
        if not def_template:
            return res
        res['context']['default_template_id'] = def_template.id
        res['context']['default_use_template'] = True
        return res
