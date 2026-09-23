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

    @api.model
    def _get_select_amount(self):
        return 'SELECT SUM(amount) '

    @api.model
    def _get_select_amount_financial(self):
        return 'SELECT SUM(credit - debit) '

    @api.model
    def _get_select_id(self):
        return 'SELECT id '

    @api.model
    def _get_financial_sql(self, exist_task=True, get_id=False):
        sql = self._get_select_amount_financial()
        if get_id:
            sql = self._get_select_id()
        sql += """
            FROM account_move_line
            WHERE (date between %s
            AND %s)
            AND account_id=ANY(%s)
        """
        if exist_task:
            sql += ' AND task_id=ANY(%s)'
        return sql

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
            sql += ' AND task_id=ANY(%s) '
        return sql

    @api.multi
    def _get_practical_amount_sql(self):
        self.ensure_one()
        if self.crossovered_budget_id.financial:
            sql = self._get_financial_sql(exist_task=self.task_id.exists())
        else:
            sql = self._get_analytic_sql(
                exist_task=self.task_id.exists(),
                exist_account=self.analytic_account_id.exists(),
            )
        return sql

    @api.multi
    def _get_task_ids(self):
        self.ensure_one()
        task_ids = []
        if self.task_id:
            task_ids.append(self.task_id.id)
        if (self.crossovered_budget_id.include_subtasks
                and self.task_id.child_ids):
            task_ids += self.task_id.child_ids.ids
        return task_ids

    @api.multi
    def _get_practical_amount(self):
        self.ensure_one()
        acc_ids = self.general_budget_id.account_ids.ids
        if self.crossovered_budget_id.financial:
            params = [self.date_from, self.date_to, acc_ids]
            sql = self._get_financial_sql(exist_task=self.task_id.exists())
            if self.task_id:
                params.append(self._get_task_ids())
        else:
            params = [acc_ids, self.date_from, self.date_to]
            sql = self._get_analytic_sql(
                exist_task=self.task_id.exists(),
                exist_account=self.analytic_account_id.exists())
            if self.analytic_account_id:
                params.append(self.analytic_account_id.id)
            if self.task_id:
                params.append(self._get_task_ids())
        self.env.cr.execute(sql, tuple(params))
        return self.env.cr.fetchone()[0] or 0.0

    @api.multi
    def _compute_practical_amount(self):
        for line in self:
            if not line.task_id and not line.crossovered_budget_id.financial:
                super(CrossoveredBudgetLines, line)._compute_practical_amount()
                continue
            line.practical_amount = line._get_practical_amount()

    @api.multi
    def _get_practical_ids(self):
        self.ensure_one()
        acc_ids = self.general_budget_id.account_ids.ids
        if self.crossovered_budget_id.financial:
            model = 'account.move.line'
            params = [self.date_from, self.date_to, acc_ids]
            sql = self._get_financial_sql(
                exist_task=self.task_id.exists(),
                get_id=True,
            )
            if self.task_id:
                params.append(self._get_task_ids())
        else:
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
                params.append(self._get_task_ids())
        self.env.cr.execute(sql, tuple(params))
        return self.env.cr.fetchall(), model

    @api.multi
    def open_moves(self):
        self.ensure_one()
        lines, model = self._get_practical_ids()
        line_ids = [record[0] for record in lines]
        if not line_ids:
            return False
        if model == 'account.move.line':
            action = self.env.ref(
                'account.action_account_moves_all_a').read()[0]
            action['name'] = _('Financial Summary')
        else:
            action = self.env.ref(
                'analytic.account_analytic_line_action_entries').read()[0]
            action['name'] = _('Analytic Summary')
        action['domain'] = [('id', 'in', line_ids)]
        return action
