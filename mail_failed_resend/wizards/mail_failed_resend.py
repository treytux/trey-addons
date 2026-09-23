###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MailFailedResend(models.TransientModel):
    _name = 'mail.failed.resend'
    _description = 'Mail Failed Resend'

    state = fields.Selection(
        string='State',
        selection=[
            ('new', 'New'),
            ('error', 'Error'),
            ('done', 'Done'),
        ],
        required=True,
        default='new',
    )
    date_from = fields.Date(
        string='Date from',
        default=fields.Date.today(),
        required=True,
    )
    date_to = fields.Date(
        string='Date to',
        default=fields.Date.today(),
        required=True,
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def resend_mails(self):
        pending_mails = self.env['mail.mail'].search([
            ('state', '=', 'exception'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ])
        if not pending_mails.exists():
            self.state = 'error'
            return self._reopen_view()
        for pending_mail in pending_mails:
            pending_mail.mark_outgoing()
            pending_mail.send()
        self.state = 'done'
        return self._reopen_view()

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wiz in self:
            if wiz.date_to < wiz.date_from:
                raise ValidationError(_(
                    'The Date to must not be earlier than the Date from.'))
