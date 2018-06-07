# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self):
        ctx = self.env.context
        if ctx.get('default_model') != 'sale.cost.simulator':
            return super(MailComposeMessage, self).send_mail()
        simulator_obj = self.env['sale.cost.simulator'].browse(
            ctx.get('active_id'))
        if not any([self.partner_ids, simulator_obj.partner_id]):
            raise exceptions.Warning(_('Please, choose a partner.'))
        res = super(MailComposeMessage, self).send_mail()
        simulator_obj.to_send()
        return res
