###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AcademyWizardFillBulletinLine(models.TransientModel):
    _name = 'academy.wizard.fill.bulletin.line'
    _description = 'Wizard Fill Bulletin Line'

    @api.model
    def _get_domain_evaluation_id(self):
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model != 'academy.marks.bulletin' or not active_id:
            return False
        bulletin = self.env[active_model].browse(active_id)
        return [("id", "in", bulletin.activity_id.evaluation_ids.ids)]

    evaluation_id = fields.Many2one(
        comodel_name='academy.evaluation',
        string='Evaluation',
        required=True,
        domain=_get_domain_evaluation_id,
    )

    def button_accept(self):
        self.ensure_one()
        bulletin = self.env['academy.marks.bulletin'].browse(
            self.env.context['active_id'])
        bulletin.create_bulletin_lines(self.evaluation_id)
        return {'type': 'ir.actions.act_window_close'}
