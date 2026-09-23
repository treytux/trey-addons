###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CreditControlRun(models.Model):
    _inherit = 'credit.control.run'

    def run_channel_action(self):
        result = super().run_channel_action()
        lines = self.line_ids.filtered(
            lambda x: x.state == 'to_be_sent' and x.channel == 'phone')
        for line in lines:
            users = (
                line.partner_id.payment_responsible_id,
                line.partner_id.user_id,
                line.partner_user_id,
                self.env.user,
            )
            user = [user for user in users if user][0]
            line.activity_schedule(
                summary=line.policy_level_id.name,
                act_type_xmlid='mail.mail_activity_data_call',
                user_id=user.id,
                note=line.policy_level_id.custom_text,
                date_deadline=fields.Date.today(),
            )
            line.partner_id.write({
                'payment_responsible_id': user.id,
                'payment_next_action': line.policy_level_id.custom_text,
                'payment_next_action_date': fields.Date.today(),
            })
        return result
