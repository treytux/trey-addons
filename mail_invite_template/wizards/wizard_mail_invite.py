###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class MailInvite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        model = res.get('res_model')
        res_id = res.get('res_id')
        report = self.env.ref('mail_invite_template.mail_invite_template')
        if model and res_id:
            record = self.env[model].browse(res_id)
            render = report.with_context(record=record)._render_template(
                report.body_html, model, res_id)
            if 'message' in fields:
                res['message'] = render
        return res
