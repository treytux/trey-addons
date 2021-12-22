###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    unit_balance = fields.Float(
        string='Quantity balance',
        compute='_compute_unit_balance',
        store=True,
    )
    last_notification = fields.Selection(
        selection=[
            ('0', 'Empty'),
            ('1', 'January'),
            ('2', 'February'),
            ('3', 'March'),
            ('4', 'April'),
            ('5', 'May'),
            ('6', 'June'),
            ('7', 'July'),
            ('8', 'August'),
            ('9', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),
        ],
        string='Month last notification',
        default='0',
    )
    notify_unit_balance = fields.Boolean(
        string='Notify unit balance',
    )

    @api.depends('line_ids', 'line_ids.unit_amount', 'line_ids.task_id')
    def _compute_unit_balance(self):
        for line in self:
            line.unit_balance = sum([ln.unit_balance for ln in line.line_ids])

    @api.multi
    def send_negative_balance_mail(self):
        template = self.env.ref('hr_timesheet_balance.email_negative_balance')
        for account in self.search([]):
            if account.last_notification != str(
                fields.Date.today().month) and (
                    account.notify_unit_balance and account.unit_balance < 0):
                for follower in account.message_follower_ids:
                    follower.partner_id.message_post_with_template(
                        template.id,
                        composition_mode='comment',
                        notif_layout='mail.mail_notification_light')
                account.last_notification = str(fields.Date.today().month)
