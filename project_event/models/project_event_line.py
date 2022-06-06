###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, exceptions, fields, models


class ProjectEventLine(models.Model):
    _name = 'project.event.line'
    _description = 'Project event line for generate events'

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
    address_id = fields.Many2one(
        comodel_name='res.partner',
        string='Location',
    )
    date_begin = fields.Datetime(
        string='Begin',
        default=fields.Datetime.now,
    )
    date_end = fields.Datetime(
        string='End',
    )
    repeat = fields.Integer(
        string='Repeats',
        default=1,
        required=True,
    )
    period = fields.Selection(
        selection=[
            ('day', 'Days'),
            ('week', 'Week'),
            ('month', 'Months'),
            ('year', 'Year'),
        ],
        string='Period',
        default='day',
        required=True,
    )
    event_ids = fields.One2many(
        comodel_name='event.event',
        inverse_name='project_event_line_id',
        string='Events',
    )

    def generate_event_prepare(self, vals):
        self.ensure_one()
        return vals

    def generate_event_product_line(self, line):
        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'quantity': line.quantity,
        }

    def generate_events(self):
        self.ensure_one()
        if not self.date_begin:
            raise exceptions.ValidationError(_('Event date begin is required'))
        event_obj = self.env['event.event']
        for index in range(0, self.repeat):
            date_end = self.date_end or self.date_begin
            if self.period == 'day':
                date_begin = self.date_begin + relativedelta(days=index)
                date_end = date_end + relativedelta(days=index)
            elif self.period == 'week':
                date_begin = self.date_begin + relativedelta(days=index * 7)
                date_end = date_end + relativedelta(days=index * 7)
            elif self.period == 'month':
                date_begin = self.date_begin + relativedelta(months=index)
                date_end = date_end + relativedelta(months=index)
            elif self.period == 'year':
                date_begin = self.date_begin + relativedelta(years=index)
                date_end = date_end + relativedelta(years=index)
            vals = {
                'project_id': self.project_id.id,
                'project_event_line_id': self.id,
                'address_id': (
                    self.address_id.id or self.project_id.partner_id.id),
                'name': self.project_id.name,
                'date_begin': date_begin,
                'date_end': date_end,
                'product_ids': [
                    (0, 0, self.generate_event_product_line(ln))
                    for ln in self.project_id.product_line_ids
                ],
            }
            event_obj.create(self.generate_event_prepare(vals))

    def action_view_events(self):
        self.ensure_one()
        action = self.env.ref('event.action_event_view').read()[0]
        action['context'] = {
            'default_project_event_line_id': self.id,
        }
        return action
