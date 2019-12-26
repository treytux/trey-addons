# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def get_mail_values(self, wizard, res_ids):
        if wizard.model == 'crm.lead':
            leads = self.env['crm.lead'].browse(res_ids)
            results = {l.partner_id.id: l.id for l in leads}
            return super(MailComposeMessage, self).get_mail_values(
                wizard, results.values())
        return super(MailComposeMessage, self).get_mail_values(wizard, res_ids)
