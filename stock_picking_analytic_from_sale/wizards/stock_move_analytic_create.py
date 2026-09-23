###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockMoveAnalyticCreate(models.TransientModel):
    _name = 'stock.move.analytic.create'
    _description = 'Create Analytic Lines From Stock Picking'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
        required=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        required=True,
    )

    def action_create_analytic(self):
        self.ensure_one()
        picking = self.picking_id
        picking.analytic_account_id = self.analytic_account_id
        if picking.state == 'done':
            picking._create_analytic_lines_from_stock_moves()
        return {'type': 'ir.actions.act_window_close'}
