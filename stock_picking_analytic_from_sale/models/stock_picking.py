###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _create_analytic_lines_from_stock_moves(self):
        self.ensure_one()
        if not self.analytic_account_id:
            return
        AnalyticLine = self.env['account.analytic.line']
        for move in self.move_ids.filtered(
            lambda m: m.state == 'done' and not m.analytic_account_line_id
        ):
            vals = move._prepare_data_for_create_analytic_line()
            if vals:
                AnalyticLine.create(vals)

    def action_create_analytic_lines(self):
        self.ensure_one()
        return {
            'name': _('Create Analytic Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.analytic.create',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_analytic_account_id': (
                    self.analytic_account_id.id
                    or self.sale_id.analytic_account_id.id
                ),
            },
        }
