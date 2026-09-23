###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployeeAnnualHourlyCost(models.Model):
    _name = 'hr.employee.annual.hourly.cost'
    _description = 'Employee hourly cost period'
    _order = 'date_start asc, id asc'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    date_start = fields.Date(
        string='Start date',
        required=True,
    )
    date_end = fields.Date(
        string='End date',
    )
    hourly_cost = fields.Monetary(
        string='Hourly cost',
        currency_field='currency_id',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='employee_id.currency_id',
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            'date_range_valid_check',
            'check(date_end is null or date_end >= date_start)',
            'End date must be greater than or equal to start date.',
        ),
    ]

    @api.constrains('employee_id', 'date_start', 'date_end')
    def _check_date_range_overlap(self):
        today = fields.Date.today()
        for record in self:
            record_end = record.date_end or today
            if record_end < record.date_start:
                raise ValidationError(_(
                    'When end date is empty, start date must be lower than or '
                    'equal to today.'))
            candidate_periods = self.search([
                ('id', '!=', record.id),
                ('employee_id', '=', record.employee_id.id),
            ])
            if not record.date_end:
                has_newer_period = any(
                    period.date_start > record.date_start
                    for period in candidate_periods)
                if has_newer_period:
                    raise ValidationError(_(
                        'Only the most recent period can have an empty end '
                        'date.'))
            has_overlap = False
            for period in candidate_periods:
                period_end = period.date_end or today
                if (
                    period.date_start <= record_end
                    and period_end >= record.date_start
                ):
                    has_overlap = True
                    break
            if has_overlap:
                raise ValidationError(_(
                    'There is already an hourly cost period overlapping these '
                    'dates for this employee.'))
