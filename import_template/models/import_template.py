###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ImportTemplate(models.Model):
    _name = 'import.template'
    _description = 'Template for imports'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=True,
        translate=True,
    )
    description = fields.Html(
        string='Description',
        translate=True,
        required=True,
        readonly=True,
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Wizard Model',
        required=True,
        readonly=True,
    )
    has_simulation = fields.Boolean(
        string='Has simulation',
        default=True,
    )
    template_file = fields.Binary(
        string='Template file',
        attachment=True,
    )
    template_file_name = fields.Char(
        string='Template file name',
        compute='_compute_template_file_name',
    )

    @api.multi
    def _compute_template_file_name(self):
        self.template_file_name = None

    def action_open_form(self, wizard):
        self.ensure_one()
        import_wizard = self.env[self.model_id.model].with_context(
            wizard=wizard).create({})
        view = import_wizard.fields_view_get()
        if view.get('view_id'):
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': import_wizard.id,
                'res_model': import_wizard._name,
                'target': 'new',
                'context': {
                    'active_ids': self.id,
                    'wizard_id': wizard.id,
                },
            }
        import_wizard.import_file(simulation=wizard.simulate)
        return self.open_form(wizard)

    def open_form(self, wizard):
        wizard.state = wizard.simulate and 'simulation' or 'step_done'
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wizard.id,
            'res_model': 'import.file',
            'target': 'new',
            'context': {},
        }

    def action_open_from_simulation_form(self, wizard):
        self.ensure_one()
        import_wizard = self.env[self.model_id.model].with_context(
            wizard=wizard).search([], order='id desc', limit=1)
        assert import_wizard.exists(), 'Import wizard must exist!'
        view = import_wizard.fields_view_get()
        if not view:
            import_wizard = self.env[self.model_id.model].with_context(
                wizard=wizard).create({})
        else:
            if view.get('view_id'):
                import_wizard = import_wizard
        res = import_wizard.import_file(simulation=False)
        wizard.state = res and 'step_done' or 'orm_error'
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wizard.id,
            'res_model': 'import.file',
            'target': 'new',
            'context': {},
        }
