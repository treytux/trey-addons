###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    def _mark_done(self):
        res = super()._mark_done()
        survey_notify_param = self.env['ir.config_parameter'].sudo().get_param(
            'survey_completion_notification.survey_notify', default=False)
        template = self.env.ref(
            'survey_completion_notification.email_template_survey_completed',
            raise_if_not_found=False)
        if survey_notify_param and template:
            for user_input in self:
                user_input.message_post_with_template(
                    template.id, composition_mode='comment',
                    email_layout_xmlid='mail.mail_notification_light')
        return res
