###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    task_count = fields.Integer(
        string='Tasks',
        compute='_compute_task_count',
    )

    @api.depends('contract_line_ids')
    def _compute_task_count(self):
        for rec in self:
            try:
                order_lines = rec.contract_line_ids.mapped(
                    'sale_order_line_id'
                )
                tasks = self.env['project.task'].search([
                    ('sale_line_id', 'in', order_lines.ids),
                ])
                task_count = len(tasks)
            except exceptions.AccessError:
                task_count = 0
            rec.task_count = task_count

    def action_view_task(self):
        self.ensure_one()
        order_lines = self.contract_line_ids.mapped(
            'sale_order_line_id'
        )
        tasks = self.env['project.task'].search([
            ('sale_line_id', 'in', order_lines.ids),
        ])
        action = {
            'name': _('Tasks'),
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', tasks.ids)],
        }
        if len(tasks) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': tasks.id,
            })
        return action
