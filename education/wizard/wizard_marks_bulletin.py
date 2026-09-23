###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduWizardMarkBulletin(models.TransientModel):
    _name = 'edu.wizard.marks.bulletin'
    _description = 'Wizard Marks Bulletins'

    evaluation_id = fields.Many2one(
        comodel_name='edu.evaluation',
        string='Evaluation',
        required=True,
    )

    def get_report_formats(self):
        report_ids = self.env['ir.actions.report.xml'].search([])
        return self.env['ir.actions.report.xml'].browse(report_ids)

    def button_print(self):
        self.ensure_one()
        data = {}
        data['active_ids'] = self._context['active_ids']
        data['evaluation_id'] = self.evaluation_id.id
        return self.env.ref(
            'education.edu_marks_bulletin_create').report_action(self, data)
