###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    unpaid_reminder = fields.Boolean(
        string='Unpaid Reminder',
    )

    @api.model
    def _send_unpaid_reminders(self):
        draft_invoices = self.search([
            ('state', 'in', ['draft', 'posted']),
            ('payment_state', '=', 'not_paid'),
            ('unpaid_reminder', '=', True),
        ])
        for invoice in draft_invoices:
            follower_emails = ','.join(
                follower.partner_id.email
                for follower in invoice.message_follower_ids
                if follower.partner_id.email)
            if follower_emails:
                template = self.env.ref(
                    'account_move_unpaid_reminder.email_tmpl_unpaid_reminder')
                template.with_context(
                    lang=invoice.partner_id.lang,
                    email_to=follower_emails).send_mail(
                        invoice.id, force_send=True, raise_exception=False)
                self.env['mail.message'].create({
                    'subject': _('Unpaid reminder sent'),
                    'body': (
                        _('Unpaid reminder sent for invoice'
                            ' %s "%s".') % (invoice.id, invoice.ref)
                    ),
                    'model': 'account.move',
                    'res_id': invoice.id,
                    'message_type': 'notification',
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                })
