###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import Command, _, fields, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    project_task_line_extra_count = fields.Integer(
        compute='_compute_project_task_line_extra_count',
        string='Project task line extra count',
    )

    def _compute_project_task_line_extra_count(self):
        for contract in self:
            contract.project_task_line_extra_count = len(
                contract.get_project_task_line_extra())

    def get_extra_lines(self, invoice_next_date):
        self.ensure_one()
        extra_lines = self.env['project.task.line.extra'].search([
            ('partner_ids', 'in', self.invoice_partner_id.id),
            '|',
            ('date_to_invoice', '=', False),
            ('date_to_invoice', '<=', invoice_next_date),
        ])
        extra_lines = extra_lines.filtered(
            lambda ln: ln.invoice_line_ids is False
            or self.invoice_partner_id not in ln.invoice_line_ids.partner_id
        )
        return extra_lines

    def _prepare_recurring_invoices_values(self, date_ref=False):
        for contract in self:
            invoice_next_date = contract.recurring_next_date or date_ref
            if not invoice_next_date:
                continue
            extra_lines = contract.get_extra_lines(invoice_next_date)
            invoice_values = super(
                ContractContract, contract
            )._prepare_recurring_invoices_values()
            for extra_line in extra_lines:
                invoice_line_vals = extra_line._prepare_invoice_line()
                if not invoice_line_vals:
                    continue
                invoice_line_vals['project_task_line_extra_id'] = extra_line.id
                invoice_values[0]['invoice_line_ids'].append(
                    Command.create(invoice_line_vals)
                )
        return invoice_values

    def get_project_task_line_extra(self):
        self.ensure_one()
        return self._get_related_invoices().mapped(
            'invoice_line_ids.project_task_line_extra_id')

    def action_view_project_task_line_extra(self):
        project_task_lines_extra = self.get_project_task_line_extra()
        form_view = self.env.ref(
            'contract_project_task_invoice_extra_lines.'
            'project_task_line_extra_form_view'
        )
        tree_view = self.env.ref(
            'contract_project_task_invoice_extra_lines.'
            'project_task_line_extra_tree_view'
        )
        action_vals = {
            'name': _('Project task lines extra'),
            'res_model': 'project.task.line.extra',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'view_type': 'form',
            'domain': [('id', 'in', project_task_lines_extra.ids)],
        }
        if len(project_task_lines_extra) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': project_task_lines_extra.ids[0],
            })
        return action_vals
