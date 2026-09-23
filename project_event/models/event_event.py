###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from pytz import timezone


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
    product_line_ids = fields.One2many(
        comodel_name='event.product',
        inverse_name='event_id',
        string='Product lines',
        domain=[('product_type', '!=', 'service')],
    )
    service_line_ids = fields.One2many(
        comodel_name='event.product',
        inverse_name='event_id',
        string='Service lines',
        domain=[('product_type', '=', 'service')],
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
    has_task_picking = fields.Boolean(
        string='Has tasks/pickings',
        help='Already has generated tasks/pickings',
    )

    @api.depends('service_line_ids', 'product_line_ids.task_id')
    def _compute_tasks(self):
        for event in self:
            tasks = event.service_line_ids.mapped('task_id')
            event.task_ids = [(6, 0, tasks.ids)]
            event.task_count = len(tasks)

    def create_services_and_material(
            self, product_ids=False, product_lines=False):
        self.ensure_one()
        msg = _('Tasks and pickings generated')
        lines = product_lines or self.product_line_ids + self.service_line_ids
        for line in lines:
            if line.task_id or (
                    product_ids and line.product_id.id not in product_ids):
                continue
            if (line.product_id.type != 'service'
                    or line.product_id.service_tracking == 'no'):
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
                self.already_generated = True
                self.message_post(body=msg)
                return
            vals = self._prepare_task_values(line, project)
            task = self.env['project.task'].create(vals)
            line.task_id = task.id
        self.already_generated = True
        self.message_post(body=msg)

    def _prepare_task_values(self, line, project):
        self.ensure_one()
        planned_hours = 1
        if self.date_begin and self.date_end:
            timedelta = self.date_end - self.date_begin
            planned_hours = timedelta.seconds / 3600
        return {
            'name': line.name or line.product_id.name,
            'date_deadline': self.date_begin,
            'planned_hours': planned_hours,
            'partner_id': project.partner_id.id,
            'email_from': project.partner_id.email,
            'project_id': project.id,
            'event_id': self.id,
            'company_id': self.company_id.id,
            'user_id': line.user_id.id,
        }

    def name_get(self):
        result = super().name_get()
        user_tz = timezone(self.env.user.tz or 'UTC')
        for count, event in enumerate(self):
            if not event.date_begin:
                continue
            current = list(result[count])
            date_time = event.date_begin.astimezone(user_tz)
            current[1] += ' %s' % date_time.strftime('%H:%M')
            result[count] = tuple(current)
        return result
