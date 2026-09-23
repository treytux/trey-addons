###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class MailDeleteMassive(models.TransientModel):
    _name = 'mail.delete.massive'
    _description = 'Wizard to delete emails in mass'

    def action_delete(self):
        assert self._context.get('active_ids'), _('Missing active_ids')
        mails = self.env['mail.mail'].browse(self._context['active_ids'])
        mails.sudo().unlink()
        return {'type': 'ir.actions.act_window_close'}
