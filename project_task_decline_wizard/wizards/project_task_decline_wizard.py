###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ProjectTaskDeclineWizard(models.TransientModel):
    _name = 'project.task.decline.wizard'
    _description = 'Wizard to decline project task'

    reason = fields.Char(
        string='Reason to decline',
        required=True,
    )

    def button_accept(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', False)
        project_task_obj = self.env['project.task']
        if not active_ids:
            raise ValidationError(_('You must select at least one task'))
        declined_stage = self.env['project.task.type'].search([
            ('declined_status', '=', True),
        ], limit=1)
        if not declined_stage:
            raise ValidationError(_('You must define declined stage'))
        for project_task in project_task_obj.browse(active_ids):
            project_task.write({
                'stage_id': declined_stage.id,
                'reason_to_decline': self.reason,
            })
            project_task.message_post(body=(_(
                'Reason to decline: %s') % project_task.reason_to_decline))
        return True
