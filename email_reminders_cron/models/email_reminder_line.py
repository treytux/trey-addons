###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from openerp import api, fields, models


class EmailReminderLine(models.TransientModel):
    _name = 'email.reminder.line'
    _description = 'Email reminder for inactivity'

    model_id = fields.Many2one(
        comodel_name='ir.model',
        required=True,
        string='Model',
    )
    date_field = fields.Many2one(
        comodel_name='ir.model.fields',
        domain="[('ttype', '=', 'datetime'),('model_id', '=', model_id)]",
        string='Date Field',
        required=True,
    )
    domain = fields.Char(
        help="Please fill with valid domain type, e.g: ('state', '=', 'sale')",
        required=True,
        string='Domain',
    )
    days = fields.Integer(
        string='Days until notice',
    )
    template_id = fields.Many2one(
        comodel_name='mail.template',
        domain=[('model_id', '=', _name)],
        required=True,
        string='Email Template',
    )
    re_notify = fields.Boolean(
        default=False,
        string='Notify continiusly?'
    )
    user_type = fields.Selection(
        help='Leave blank to all',
        selection='_get_user_type_groups',
        string='Addressee type',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        string='Sender company',
        default=lambda self: self.env.user.company_id.id,
    )

    def get_model_domain(self, reminder_line, deadline_time):
        return [
            (reminder_line.date_field.name, '<', deadline_time),
            eval(reminder_line.domain),
        ]

    def get_message_domain(self, model_obj, res):
        return [
            ('model', '=', model_obj),
            ('res_id', '=', res.id),
        ]

    def send_reminder_mail(self, reminder_line, partners_ids, res):
        reminder_line.template_id.sudo().with_context(
            lang=reminder_line.create_uid.lang,
            partners_ids=partners_ids, res=res).send_mail(
                reminder_line.id, force_send=True)

    @api.model
    def _get_user_type_groups(self):
        return [(group.id, group.name) for group in [
            self.env.ref('base.group_user'),
            self.env.ref('base.group_public')]
        ]

    @api.model
    def check_reminders_alerts(self):
        for reminder_line in self.with_context(cron=True).search([]):
            deadline_time = datetime.now() - timedelta(days=reminder_line.days)
            model_obj = reminder_line.model_id.model
            search = self.env[model_obj].search(self.get_model_domain(
                reminder_line, deadline_time))
            for res in search:
                if not res.message_follower_ids:
                    continue
                partners_to_send = self.env['res.partner']
                for follower in res.message_follower_ids:
                    if reminder_line.user_type:
                        if not follower.partner_id.user_ids:
                            continue
                        user_ids = follower.partner_id.user_ids
                        if reminder_line.user_type in user_ids.groups_id.ids:
                            partners_to_send += follower.partner_id
                    else:
                        partners_to_send += follower.partner_id
                if not partners_to_send:
                    continue
                message_domain = self.get_message_domain(model_obj, res)
                reminder_message = self.env['mail.message'].search(
                    (message_domain + [('is_reminder', '=', True)]),
                    order='create_date desc')
                if not reminder_message:
                    self.send_reminder_mail(
                        reminder_line, partners_to_send.ids, res)
                    messages = self.env['mail.message'].search(
                        message_domain, order='create_date desc')
                    if messages:
                        messages[0].is_reminder = True
                if (
                        reminder_message
                        and reminder_message[0].create_date < deadline_time
                        and reminder_line.re_notify):
                    self.send_reminder_mail(
                        reminder_line, partners_to_send.ids, res)
