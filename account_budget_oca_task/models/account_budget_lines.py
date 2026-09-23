###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        domain="[('project_id.analytic_account_id', '=', analytic_account_id)]",
    )

    @api.depends('general_budget_id.account_ids', 'date_from', 'date_to',
                 'analytic_account_id', 'task_id')
    def _compute_practical_amount(self):
        for line in self:
            if not line.task_id:
                super(CrossoveredBudgetLines, line)._compute_practical_amount()
                continue
            result = 0.0
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = line.date_to
            date_from = line.date_from
            if line.analytic_account_id.id and date_from and date_to:
                self.env.cr.execute(
                    """
                    SELECT SUM(amount)
                    FROM account_analytic_line
                    WHERE account_id=%s
                        AND (date between %s AND %s)
                        AND general_account_id=ANY(%s)
                        AND task_id=%s""",
                    (line.analytic_account_id.id, date_from, date_to, acc_ids,
                     line.task_id.id),
                )
                result = self.env.cr.fetchone()[0] or 0.0
            line.practical_amount = result

    @api.model
    def _get_select_amount(self):
        return 'SELECT SUM(amount) '

    @api.model
    def _get_select_id(self):
        return 'SELECT id '

    @api.model
    def _get_analytic_sql(self, exist_task=True, exist_account=True,
                          get_id=False):
        sql = self._get_select_amount()
        if get_id:
            sql = self._get_select_id()
        sql += """
                FROM account_analytic_line
                WHERE general_account_id=ANY(%s)
                AND (date between %s
                AND %s)
            """
        if exist_account:
            sql += ' AND account_id=%s '
        if exist_task:
            sql += ' AND task_id=%s '
        return sql

    def _get_practical_ids(self):
        self.ensure_one()
        acc_ids = self.general_budget_id.account_ids.ids
        model = 'account.analytic.line'
        params = [acc_ids, self.date_from, self.date_to]
        sql = self._get_analytic_sql(
            exist_task=self.task_id.exists(),
            exist_account=self.analytic_account_id.exists(),
            get_id=True,
        )
        if self.analytic_account_id:
            params.append(self.analytic_account_id.id)
        if self.task_id:
            params.append(self.task_id.id)
        self.env.cr.execute(sql, tuple(params))
        return self.env.cr.fetchall(), model

    def open_moves(self):
        self.ensure_one()
        lines, model = self._get_practical_ids()
        line_ids = [record[0] for record in lines]
        if not line_ids:
            return False
        action = self.env.ref(
            'analytic.account_analytic_line_action_entries').read()[0]
        action['name'] = _('Analytic Summary')
        action['domain'] = [('id', 'in', line_ids)]
        return action
