###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProjectUpdate(models.Model):
    _inherit = 'project.update'

    def send_update_report(self):
        self.ensure_one()
        mail_template = self.env.ref(
            'project_update_report.mail_template_update_reports',
            raise_if_not_found=False
        )
        ctx = {
            'default_model': 'project.update',
            'default_res_id': self.id,
            'default_use_template': bool(mail_template),
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': (
                'mail.mail_notification_layout_with_responsible_signature'),
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views' : [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
