###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    activity_date = fields.Datetime(
        string='Activity date',
        default=fields.Datetime.now,
        required=True,
    )
    activity_duration = fields.Float(
        string='Activity duration',
        default=1,
        required=True,
    )
    activity_all_day = fields.Boolean(
        string='All day',
        default=True,
    )
    activity_id = fields.Integer(
        string='Activity ID',
        related='activity_type_id.id',
    )
    activity_all_day_date = fields.Date(
        string='Date of all day activity',
        default=fields.Date.today(),
    )

    @api.depends('activity_date')
    def change_date_deadline(self):
        for activity in self:
            activity.date_deadline = activity.activity_date.strftime(
                '%Y-%m-%d')

    @api.depends('activity_all_day')
    def check_activity_all_day(self):
        for activity in self:
            if activity.activity_all_day:
                activity.activity_date = activity.date_deadline.strftime(
                    '%Y-%m-%d')
                activity.activity_duration = 1

    @api.depends('calendar_event_id_start, duration')
    def update_date_and_duration_meeting(self):
        for activity in self:
            if activity.calendar_event_id_start and activity.duration:
                activity.activity_date = activity.calendar_event_id_start
                activity.activity_duration = activity.duration

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.activity_type_id.id == self.env.ref(
                'mail.mail_activity_data_meeting').id:
            res.activity_all_day = False
        return res

    @api.multi
    def action_close_dialog(self):
        for activity in self:
            if activity.activity_all_day:
                activity.date_deadline = activity.activity_all_day_date
                activity.activity_date = activity.date_deadline.strftime(
                    '%Y-%m-%d')
                activity.activity_duration = 1
            else:
                activity.date_deadline = activity.activity_date.strftime(
                    '%Y-%m-%d')
        return super().action_close_dialog()
