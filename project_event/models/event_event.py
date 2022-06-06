###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class EventEvent(models.Model):
    _inherit = 'event.event'

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
    project_event_line_id = fields.Many2one(
        comodel_name='project.event.line',
        string='Project event line',
    )
    product_ids = fields.One2many(
        comodel_name='event.product',
        inverse_name='event_id',
        string='Products',
    )
    task_ids = fields.One2many(
        comodel_name='project.task',
        compute='_compute_tasks',
        string='tasks',
    )
    task_count = fields.Integer(
        string='Task count',
        compute='_compute_tasks',
    )

    @api.depends('product_ids', 'product_ids.task_id')
    def _compute_tasks(self):
        for event in self:
            tasks = event.product_ids.mapped('task_id')
            event.task_ids = [(6, 0, tasks.ids)]
            event.task_count = len(tasks)

    def button_confirm(self):
        res = super().button_confirm()
        for event in self:
            event.create_services_and_material()
        return res

    def create_services_and_material(self):
        self.ensure_one()
        for line in self.product_ids:
            if line.product_id.type != 'service':
                continue
            if line.product_id.service_tracking == 'no':
                continue
            if line.product_id.service_tracking == 'task_global_project':
                project = line.product_id.project_id
            elif line.product_id.service_tracking == 'task_new_project':
                project = self.project_id
            elif line.product_id.service_trackig == 'project_only':
                values = {
                    'name': '(%s) %s' % (self.name, line.name),
                    'allow_timesheets': True,
                    'partner_id': self.address_id.id,
                    'event_id': self.id,
                    'active': True,
                }
                if self.product_id.project_template_id:
                    values['name'] = '(%s) %s' % (
                        line.product_id.project_template_id.name, line.name),
                    project = self.product_id.project_template_id.copy(values)
                    project.tasks.write({
                        'partner_id': self.project_id.partner_id.id,
                        'email_from': self.project_id.partner_id.email,
                        'event_id': self.id,
                    })
                return
            vals = self._prepare_task_values(line, project)
            task = self.env['project.task'].create(vals)
            line.task_id = task.id

    def _prepare_task_values(self, line, project):
        self.ensure_one()
        return {
            'name': line.name,
            'date_deadline': self.date_begin,
            'planned_hours': line.quantity,
            'partner_id': project.partner_id.id,
            'email_from': project.partner_id.email,
            'project_id': project.id,
            'event_id': self.id,
            'company_id': self.company_id.id,
            'user_id': False,  # force non assigned task, as created as sudo()
        }
