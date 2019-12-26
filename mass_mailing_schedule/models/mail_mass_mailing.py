# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class MailMassMailing(models.Model):
    _inherit = 'mail.mass_mailing'

    scheduled_date = fields.Datetime(
        string='Scheduled date')

    @api.multi
    def schedule_mass_mailing(self):
        if not self.scheduled_date:
            raise UserError(_('You must complete scheduled date field'))
        if self.scheduled_date <= fields.Datetime.now():
            raise UserError(
                _('Scheduled date must be later than the current one'))
        for mailing in self:
            if mailing._sendings_get():
                raise UserError(_(
                    'There is another sending task running. '
                    'Please, be patient. You can see all the sending tasks in '
                    '"Sending tasks" tab'
                ))
            if not mailing.get_recipients(mailing):
                raise UserError(_('Please select recipients.'))
            sending = self.env['mail.mass_mailing.sending'].create({
                'state': 'enqueued',
                'mass_mailing_id': mailing.id,
            })
            sending.date_start = self.scheduled_date
            mailing.write({
                'state': 'sending',
            })
        return True
