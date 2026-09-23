###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class MailRetrySendMassive(models.TransientModel):
    _name = 'mail.retry.send.massive'
    _description = 'Wizard to resend emails in mass'

    def action_retry_send(self):
        assert self._context.get('active_ids'), _('Missing active_ids')
        mails = self.env['mail.mail'].browse(self._context['active_ids'])
        valid_mails = mails.filtered(lambda m: m.state in ['exception', 'cancel'])
        if not valid_mails:
            raise UserError(_('No emails in exception or cancel state found'))
        valid_mails.sudo().mark_outgoing()
        valid_mails.sudo().send()
        return {'type': 'ir.actions.act_window_close'}
