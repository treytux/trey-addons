###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class EventRegistrationResendBadgeWizard(models.TransientModel):
    _name = 'event.registration.resend.badge.wizard'
    _description = 'Event registration resend badge wizard'

    attendee_ids = fields.Many2many(
        comodel_name='event.registration',
        string='Selected attendees',
        help='Confirmed attendees will receive the email.',
        domain=lambda self: [(
            'company_id', 'in', self.env.user.company_ids.ids)],
    )
    template_id = fields.Many2one(
        comodel_name='mail.template',
        string='Email template',
        domain=[('model_id.model', '=', 'event.registration')],
        required=True,
        help='Select the email template to use for accreditation sending.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        active_model = self._context.get('active_model')
        if active_ids and active_model == 'event.registration':
            res['attendee_ids'] = [(6, 0, active_ids)]
        return res

    def _get_confirmed_attendees(self):
        return self.attendee_ids.filtered(lambda att: att.state == 'open')

    def resend_accreditations(self):
        if not self._get_confirmed_attendees():
            raise UserError(_(
                'No confirmed attendees in the selected records. '
                'Only \'confirmed\' attendees will receive accreditations.'))
        if not self.template_id:
            raise ValidationError(_('Please select an email template.'))
        for attendee in self._get_confirmed_attendees():
            if attendee.company_id not in self.env.user.company_ids:
                raise UserError(_(
                    'You are not allowed to send badges to '
                    'attendees from another company.'))
            if (
                attendee.partner_id and attendee.partner_id.email
                != attendee.email
            ):
                attendee.partner_id.write({'email': attendee.email})
            self.template_id.send_mail(attendee.id, force_send=False)
        return {'type': 'ir.actions.act_window_close'}
