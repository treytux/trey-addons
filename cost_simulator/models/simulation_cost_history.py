# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
import logging
_log = logging.getLogger(__name__)


class SimulationCostHistory(models.Model):
    _name = 'simulation.cost.history'
    _description = 'Simulation Cost History'

    simulation_number = fields.Char(
        string='Serial',
        size=64,
        default='/',
        copy=False)
    cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        required=True,
        index=True,
        ondelete='cascade')
    active_cost_ids = fields.One2many(
        comodel_name='simulation.cost',
        inverse_name='simulation_id',
        string='Simulation')
    name = fields.Char(
        string='Description/Name',
        size=250,
        required=True,
        attrs={'readonly': [('historical_ok', '=', True)]})
    sequence = fields.Integer(
        string="Sequence",
        required=False)
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        help="Pricelist for current sales order.")
    date = fields.Datetime(
        string='Date',
        readonly=True,
        default=fields.Datetime.now)
    total_sales = fields.Float(
        string='Total Sales',
        readonly=True,
        compute='compute_totals',
        digits_compute=dp.get_precision('Purchase Price'),
        store=True)
    line_ids = fields.One2many(
        comodel_name='simulation.cost.history.line',
        inverse_name='history_id',
        string='Cost Line History',
        required=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')

    @api.one
    def compute_totals(self):
        total_sales = sum([s.subtotal_sale for s in self.line_ids])
        total_costs = sum([c.subtotal_cost for c in self.cost_id.line_ids])
        total_benefits = total_sales - total_costs
        self.total_sales = total_sales
        self.total_costs = total_costs
        self.total_benefits = total_benefits
        if total_sales != 0 and total_costs != 0:
            self.gross_margin_percentage = \
                ((total_sales * 100) / total_costs) - 100
            self.net_margin_percentage = \
                100 - ((total_costs * 100) / total_sales)
        else:
            self.gross_margin_percentage = 0
            self.net_margin_percentage = 0

    @api.one
    def write(self, values):
        # self.env['simulation.cost'].compute_total_chapter()
        res = super(SimulationCostHistory, self).write(values)
        return res


class SimulationCostHistoryLine(models.Model):
    _name = 'simulation.cost.history.line'
    _description = 'Simulation Cost History Line'
    _order = 'id'

    sequence = fields.Integer(
        string='Sequence',
        required=False)
    cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        required=True,
        index=True,
        ondelete='cascade')
    history_id = fields.Many2one(
        comodel_name="simulation.cost.history",
        string="Cost History",
        required=False)
    line_id = fields.Many2one(
        comodel_name="simulation.cost.line",
        string="Cost Line",
        required=False)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    name = fields.Char(
        string='Name',
        size=64,
        required=True)
    price = fields.Float(
        string='Price Unit',
        digits=(7, 2),
        default=0)
    quantity = fields.Float(
        string='Quantity',
        store=True,
        digits_compute=dp.get_precision('Product UoS'),
        default=1)
    discount = fields.Float(
        string='Discount (%)',
        digits_compute=dp.get_precision('Discount'))
    discount_type = fields.Selection(
        selection=[
            ('included', 'Incluido'),
            ('visible', 'Visible'),
            ('simulation', 'Simulado')],
        string="% Type",
        default='simulation',
        required=True)
    price_sale = fields.Float(
        string='Price Unit Sale',
        compute='calculate_subtotals')
    quantity_sale = fields.Float(
        string='Qty Sale')
    discount_sale = fields.Float(
        string='Dto. Sale',
        compute='calculate_subtotals')
    subtotal_sale = fields.Float(
        string='Subtotal Sale',
        compute='calculate_subtotals')
    lock_update_price = fields.Boolean(
        string='Lock update price')

    @api.one
    @api.depends('price', 'discount', 'discount_type', 'quantity_sale')
    def calculate_subtotals(self):
        p = self.price
        d = self.discount / 100

        if self.discount_type == 'simulation':
            self.price_sale = p / (1 - d)
            self.discount_sale = self.discount
        elif self.discount_type == 'visible':
            self.price_sale = p  # p - (p * d)
            self.discount_sale = self.discount
        elif self.discount_type == 'included':
            self.price_sale = p - (p * d)
            self.discount_sale = 0.0
        else:
            self.subtotal_sale = p
            self.discount_sale = 0.0
        subtotal = (self.price_sale * self.quantity)
        dto = self.discount_sale and (
            subtotal * (self.discount_sale / 100)) or 0
        subtotal = subtotal - dto
        if self.quantity != self.quantity_sale:
            self.price_sale = subtotal / (self.quantity_sale or 1)
        self.subtotal_sale = subtotal

        self.env['simulation.cost.history'].compute_totals()
