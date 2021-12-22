###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SimulationCostHistory(models.Model):
    _name = 'simulation.cost.history'
    _description = 'Simulation Cost History'

    simulation_number = fields.Char(
        string='Serial',
        default='/',
        copy=False,
    )
    cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        required=True,
        index=True,
        ondelete='cascade',
    )
    active_cost_ids = fields.One2many(
        comodel_name='simulation.cost',
        inverse_name='simulation_id',
        string='Simulation',
    )
    name = fields.Char(
        string='Description/Name',
        required=True,
        attrs={'readonly': [('historical_ok', '=', True)]},
    )
    sequence = fields.Integer(
        string='Sequence',
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        help='Pricelist for current sales order.',
    )
    date = fields.Datetime(
        string='Date',
        readonly=True,
        default=fields.Datetime.now,
    )
    total_sales = fields.Float(
        string='Total Sales',
        readonly=True,
        compute='compute_totals',
        digits=dp.get_precision('Purchase Price'),
        store=True,
    )
    line_ids = fields.One2many(
        comodel_name='simulation.cost.history.line',
        inverse_name='history_id',
        string='Cost Line History',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
    )

    @api.multi
    def compute_totals(self):
        for cost in self:
            total_sales = sum([s.subtotal_sale for s in cost.line_ids])
            total_costs = sum([c.subtotal_cost for c in cost.cost_id.line_ids])
            total_benefits = total_sales - total_costs
            cost.total_sales = total_sales
            cost.total_costs = total_costs
            cost.total_benefits = total_benefits
            if total_sales != 0 and total_costs != 0:
                cost.gross_margin_percentage = \
                    ((total_sales * 100) / total_costs) - 100
                cost.net_margin_percentage = \
                    100 - ((total_costs * 100) / total_sales)
            else:
                cost.gross_margin_percentage = 0
                cost.net_margin_percentage = 0
