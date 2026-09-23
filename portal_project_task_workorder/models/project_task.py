###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    center = fields.Many2one(
        comodel_name='stock.location',
        domain=[
            ('is_center', '=', True),
        ],
        string='Center',
    )
    workorder_create_user = fields.Many2one(
        comodel_name='res.users',
        string='Workorder create user',
    )
    portal_created = fields.Boolean(
        string='Created from portal',
    )

    def write(self, vals):
        mail_template = self.env.ref(
            'portal_project_task_workorder.email_template_update_task_state')
        if 'stage_id' in vals:
            new_stg = self.env['project.task.type'].browse(vals['stage_id'])
            for task in self:
                if task.stage_id != new_stg and task.portal_created:
                    user = task.workorder_create_user
                    if user.email:
                        email_list = {
                            'email_to': user.email,
                        }
                        mail_template.send_mail(
                            task.id, force_send=True, email_values=email_list)
        return super().write(vals)
