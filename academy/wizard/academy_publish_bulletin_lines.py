###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class AcademyPublishBulletinLines(models.TransientModel):
    _name = 'academy.publish.bulletin.lines'
    _description = 'Wizard publish bulletin lines'

    @api.model
    def _get_domain_evaluation_id(self):
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)
        if active_model != 'academy.activity' or not active_ids:
            return False
        activities = self.env[active_model].browse(active_ids)
        evaluations_ids = activities.mapped('evaluation_ids').ids
        if not evaluations_ids:
            return False
        return [('id', 'in', evaluations_ids)]

    evaluation_id = fields.Many2one(
        comodel_name='academy.evaluation',
        string='Evaluation',
        required=True,
        domain=_get_domain_evaluation_id,
    )

    def button_publish_bulletin_lines(self):
        self.ensure_one()
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)
        if active_model != 'academy.activity' or not active_ids:
            raise exceptions.UserError(_('Please select one activity.'))
        activities = self.env[active_model].browse(active_ids)
        bulletin_lines_obj = self.env['academy.marks.bulletin.line']
        for activity in activities:
            bulletin_lines = bulletin_lines_obj.search([
                ('activity_id', '=', activity.id),
                ('evaluation_id', '=', self.evaluation_id.id),
                ('portal_published', '=', False),
            ])
            if not bulletin_lines:
                continue
            bulletin_lines.write({
                'portal_published': True,
            })
        return {'type': 'ir.actions.act_window_close'}
