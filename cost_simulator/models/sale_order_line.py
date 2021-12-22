###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    generate_task = fields.Boolean(
        string='Generate Task',
    )
    history_line_id = fields.Many2one(
        comodel_name='simulation.cost.history.line',
        string='Simulation Line',
    )
