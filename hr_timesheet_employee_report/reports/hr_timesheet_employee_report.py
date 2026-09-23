###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, tools


class TimesheetEmployeeReport(models.Model):
    _name = "hr.timesheet.employee.report"
    _description = "Timesheet employee report"
    _auto = False

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        index=True,
    )
    timesheet_id = fields.Many2one(
        comodel_name='account.analytic.line',
        string='Timesheet',
        index=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
    )
    date = fields.Date(
        string='Date',
    )
    unit_amount = fields.Float(
        string='Hours',
    )
    holiday_id = fields.Many2one(
        comodel_name='hr.leave',
        string='Absence',
    )
    days_leave = fields.Float(
        string='Days Leave',
    )
    account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
    )
    workorder_id = fields.Many2one(
        comodel_name='mrp.workorder',
        string='Workorder',
    )

    def _from(self):
        return ['''
            (
                (
                    SELECT
                        e.id AS "employee_id",
                        e.active AS "active",
                        NULL AS "timesheet_id",
                        NULL AS "project_id",
                        NULL AS "task_id",
                        NULL AS "holiday_id",
                        date(NULL) AS "date",
                        NULL AS "unit_amount",
                        NULL AS "account_id",
                        NULL AS "workorder_id",
                        NULL AS "days_leave"
                    FROM
                        hr_employee AS e
                ) UNION (
                    SELECT
                        e.id AS "employee_id",
                        e.active AS "active",
                        aal.id AS "timesheet_id",
                        aal.project_id AS "project_id",
                        aal.task_id AS "task_id",
                        aal.holiday_id AS "holiday_id",
                        aal.date AS "date",
                        aal.unit_amount AS "unit_amount",
                        aal.account_id AS "account_id",
                        aal.workorder_id AS "workorder_id",
                        CASE
                            WHEN aal.holiday_id IS NOT NULL AND
                                hl.number_of_days BETWEEN 0 AND 1
                                THEN hl.number_of_days
                            WHEN aal.holiday_id IS NOT NULL THEN 1
                            ELSE 0
                        END AS days_leave
                    FROM hr_employee AS e
                        LEFT JOIN account_analytic_line AS aal ON
                            e.id = aal.employee_id
                        LEFT JOIN hr_leave AS hl ON hl.id = aal.holiday_id
                    WHERE aal.project_id IS NOT NULL OR
                        aal.workorder_id IS NOT NULL
                )
            ) AS employee
        ''']

    def _where(self):
        return [
            'employee.active IS NOT FALSE'
        ]

    def _query(self):
        return 'SELECT ROW_NUMBER () OVER () AS id, * FROM %s WHERE %s' % (
            ' '.join(self._from()),
            ' '.join(self._where()),
        )

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            'CREATE or REPLACE VIEW %s as (%s)' % (self._table, self._query()))
