# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class MailInviteWizard(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    @api.model
    def default_get(self, fields):
        result = super(MailInviteWizard, self).default_get(fields)
        model = result.get('res_model')
        res_id = result.get('res_id')
        report_obj = self.env['report']
        selected_body = self.env.ref(
            'email_custom_formats.email_template_follow_claim').body_html
        docargs = {
            'doc_ids': self.res_id,
            'doc_model': model,
            'docs': selected_body}
        render = report_obj.render(
            'email_custom_formats.email_layout', docargs)
        if 'message' in fields and model and res_id:
            result['message'] = render
        elif 'message' in fields:
            default_msg = report_obj.render(
                'email_custom_formats.email_invite_default')
            result['message'] = default_msg
        return result
