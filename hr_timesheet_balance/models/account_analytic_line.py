###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    unit_balance = fields.Float(
        string='Quantity balance',
        compute='_compute_unit_balance',
    )
    reset_line_id = fields.Many2one(
        comodel_name='account.analytic.line',
        string='Line for reset balance',
    )

    @api.multi
    @api.depends('unit_amount', 'task_id')
    def _compute_unit_balance(self):
        for line in self:
            line.unit_balance = line.unit_amount * (line.task_id and -1 or 1)

    def create_reset_balance(self):
        tag = self.env.ref('hr_timesheet_balance.analytic_line_reset_balance')
        for line in self:
            if not line.product_id:
                continue
            if not line.product_id.analytic_reset_balance:
                continue
            if line.reset_line_id:
                continue
            balance = (line.account_id.unit_balance - line.unit_balance) * -1
            if not balance:
                continue
            reset_line = line.with_context(reset_balance=False).create({
                'account_id': line.account_id.id,
                'date': line.date,
                'name': tag.name,
                'unit_amount': balance,
                'tag_ids': [(6, 0, [tag.id])],
            })
            line.reset_line_id = reset_line.id

    @api.model
    def create(self, vals):
        line = super().create(vals)
        if self._context.get('reset_balance'):
            line.create_reset_balance()
        return line

    def unlink(self):
        for line in self:
            if line.reset_line_id:
                line.reset_line_id.unlink()
        return super().unlink()
