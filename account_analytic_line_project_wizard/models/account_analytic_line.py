###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models

LINE_STATES = [
    ('to_invoice', 'To Invoice'),
    ('not_billable', 'Not Billable'),
    ('invoiced', 'Invoiced'),
    ('settled', 'Settled'),
]


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    task_state = fields.Selection(
        selection=LINE_STATES,
        default='to_invoice',
        index=True,
        store=True,
    )
    task_invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Task Invoice',
    )
    stage_id = fields.Many2one(
        comodel_name='project.task.type',
        related='task_id.stage_id',
        readonly=True,
        store=True,
    )
    settlement_id = fields.Many2one(
        comodel_name='sale.commission.settlement',
        ondelete='cascade',
    )
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        compute='_compute_supplier_id',
        readonly=True,
        store=True,
    )

    def init(self):
        self.env.cr.execute('''
            UPDATE account_analytic_line AS line
               SET task_state = state.task_state
              FROM (
                    SELECT aal.id,
                           CASE
                               WHEN aal.settlement_id IS NOT NULL
                                   THEN 'settled'
                               WHEN aal.so_line IS NOT NULL
                                    OR aal.task_invoice_id IS NOT NULL
                                    OR aal.timesheet_invoice_id IS NOT NULL
                                   THEN 'invoiced'
                               WHEN move.move_type IN (
                                       'out_invoice', 'out_refund')
                                   THEN 'invoiced'
                               WHEN aal.amount > 0
                                   THEN 'not_billable'
                               ELSE 'to_invoice'
                           END AS task_state
                      FROM account_analytic_line AS aal
                 LEFT JOIN account_move_line AS move_line
                        ON move_line.id = aal.move_line_id
                 LEFT JOIN account_move AS move
                        ON move.id = move_line.move_id
                   ) AS state
             WHERE line.id = state.id
               AND line.task_state IS DISTINCT FROM state.task_state
        ''')

    @api.depends(
        'move_line_id.move_id.partner_id', 'move_line_id.move_id.move_type')
    def _compute_supplier_id(self):
        for line in self:
            move = line.move_line_id.move_id
            if move and move.move_type in ('in_invoice', 'in_refund'):
                line.supplier_id = move.partner_id
            else:
                line.supplier_id = False

    @api.constrains('so_line', 'project_id')
    def _check_sale_line_in_project_map(self):
        for timesheet in self:
            if timesheet.project_id and timesheet.so_line:
                if timesheet.so_line not in timesheet.project_id.mapped(
                        'sale_line_employee_ids.sale_line_id') or \
                        timesheet.task_id.sale_line_id or \
                        timesheet.project_id.sale_line_id:
                    timesheet.project_id.sale_line_id = timesheet.so_line.id
        parent = super()
        if hasattr(parent, '_check_sale_line_in_project_map'):
            return parent._check_sale_line_in_project_map()
        return True

    def _get_task_state(self):
        self.ensure_one()
        if self.settlement_id:
            return 'settled'
        if self.so_line or self.task_invoice_id or self.timesheet_invoice_id:
            return 'invoiced'
        move = self.move_line_id.move_id
        if move and move.move_type in ('out_invoice', 'out_refund'):
            return 'invoiced'
        if self.amount > 0:
            return 'not_billable'
        return 'to_invoice'

    def _sync_task_state(self):
        for state in dict(LINE_STATES):
            lines = self.filtered(
                lambda line, state=state: line._get_task_state() == state
                and line.task_state != state)
            if lines:
                super(AccountAnalyticLine, lines.with_context(
                    skip_task_state_sync=True)
                ).write({
                    'task_state': state,
                })

    def _sale_determine_order(self):
        mapping = {}
        for analytic_line in self:
            sale_order = self.env['sale.order'].search([
                ('analytic_account_id', '=', analytic_line.account_id.id),
                ('state', '=', 'sale'),
            ], limit=1)
            if not sale_order:
                continue
            mapping[analytic_line.id] = sale_order
        return mapping

    def action_view_sale_order(self):
        self.ensure_one()
        sales = self.env['sale.order'].search([
            ('analytic_account_id', '=', self.account_id.id),
        ])
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('id', 'in', sales.ids)]
        return action

    def _timesheet_postprocess_values(self, values):
        amount = values.get('amount', False)
        result = super()._timesheet_postprocess_values(values)
        if 'task_material_id' in values and amount:
            for line in result:
                result[line]['amount'] = amount
        return result

    def _sale_determine_order_line(self):
        return {}

    @api.model_create_multi
    def create(self, vals_list):
        Expense = self.env['hr.expense']
        active_model = self.env.context.get('active_model', False)
        lines = super().create(vals_list)
        if self.env.context.get('no_sheet', False):
            lines.sheet_id = False
        if active_model == 'hr.expense':
            expense = Expense.browse(self.env.context['active_id'])
            for line in lines:
                if not line.task_id and expense.analytic_line_id:
                    line.task_id = expense.task_id.id
                    if line.user_id.id != expense.analytic_line_id.user_id.id:
                        line.user_id = expense.analytic_line_id.user_id.id
        if not self.env.context.get('skip_task_state_sync'):
            lines._sync_task_state()
        return lines

    def write(self, values):
        result = super().write(values)
        sync_fields = {
            'amount',
            'move_line_id',
            'settlement_id',
            'so_line',
            'task_invoice_id',
            'timesheet_invoice_id',
        }
        if not self.env.context.get('skip_task_state_sync') and \
                sync_fields.intersection(values):
            self._sync_task_state()
        return result
