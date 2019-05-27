###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def behaviour(self):
        self.ensure_one()
        if self.env.context.get('behaviour'):
            return self.env.context['behaviour']
        return super().behaviour()

    @api.multi
    def behaviour_with_conditions(self, records):
        self.ensure_one()
        actions = self.env['printing.report.xml.action'].search([
            ('report_id', '=', self.id),
            ('action', '!=', 'user_default'),
            '|',
            ('user_id', '=', self.env.uid),
            ('user_id', '=', False)])
        for action in actions:
            if action.pass_condition(records):
                return action
        return None

    def render_qweb_pdf(self, docids, data=None):
        if self.env.context.get('force_email'):
            return super().render_qweb_pdf(docids, data=data)
        records = self.env[self.model].browse(docids)
        action = self.behaviour_with_conditions(records)
        behaviour = self._get_user_default_print_behaviour()
        behaviour.update(self._get_report_default_print_behaviour())
        if action:
            behaviour.update(
                {k: v for k, v in action.behaviour().items() if v})
        self = self.with_context(behaviour=behaviour)
        return super().render_qweb_pdf(docids, data=data)
