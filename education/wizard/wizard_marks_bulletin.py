# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, exceptions, _


class EduWizardMarkBulletins(models.TransientModel):
    _name = 'edu.wizard.marks.bulletins'
    _description = 'Wizard Marks Bulletins'

    evaluation_id = fields.Many2one(
        comodel_name='edu.evaluation',
        string='Evaluation',
        required=True)

    def get_report_formats(self):
        report_ids = self.env['ir.actions.report.xml'].search([])
        return self.env['ir.actions.report.xml'].browse(report_ids)

    @api.multi
    def button_print(self):
        context = self.env.context
        objects = (
            context['active_model'] and context['active_ids'] and
            self.env[context['active_model']].browse(
                context['active_ids'] or []))
        if not objects:
            raise exceptions.Warning(
                _('Error'),
                _('You should select at least one bulletin'))
        evaluation = self.evaluation_id.sequence
        return {
            'type': 'ir.actions.report.xml',
            'report_name': ('education.edu_marks_bulletin'),
            'datas': dict(ids=objects.ids, evaluation=evaluation)}
