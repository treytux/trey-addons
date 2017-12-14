# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class SimulationCost(models.Model):
    _name = 'simulation.cost'
    _description = 'Simulation Costs'

    name = fields.Char(
        string='Description/Name',
        size=250,
        required=True)
    simulation_number = fields.Char(
        string='Serial',
        size=64,
        default='/',
        copy=False)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda s: s.env.user.company_id,
        ondelete='set null',
        required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('simulation', 'Simulation'),
            ('accepted', 'Accepted'),
            ('canceled', 'Canceled')],
        string='State',
        readonly=True,
        default='draft')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        related="company_id.currency_id")
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Pricelist for current sales order.")
    date = fields.Date(
        string='Date',
        readonly=True,
        default=fields.Date.context_today)
    line_ids = fields.One2many(
        comodel_name='simulation.cost.line',
        inverse_name='cost_id',
        copy=True,
        string='Cost Line',
        required=True)
    history_ids = fields.One2many(
        comodel_name='simulation.cost.history',
        inverse_name='cost_id',
        compute='compute_history_ids',
        string='Simulation history')
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesperson',
        select=True,
        required=True)
    section_id = fields.Many2one(
        comodel_name='crm.case.section',
        string='Sales Team',
        required=True)
    simulation_id = fields.Many2one(
        comodel_name='simulation.cost.history',
        string='Simulation')
    simulation_name = fields.Char(
        related='simulation_id.name')
    simulation_line_ids = fields.One2many(
        related='simulation_id.line_ids')
    simulation_pricelist_id = fields.Many2one(
        related='simulation_id.pricelist_id')
    sale_type = fields.Selection(
        string='Sales Type',
        selection=[('chapter', 'Per Chapter'),
                   ('simulation', 'Per Simulation')])
    project_type = fields.Selection(
        string='Proyect Type',
        selection=[('closed', 'Closed'),
                   ('open', 'Open')])
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='simulator_cost2tax',
        column1='cost_id',
        column2='tax_id',
        string='Taxes', domain=[('parent_id', '=', False)])
    total = fields.Float(
        string='Total',
        compute='compute_totals',
        digits_compute=dp.get_precision('Sale Price'),
        store=True)
    total_untaxed = fields.Float(
        string='Total untaxed',
        compute='compute_totals',
        digits_compute=dp.get_precision('Sale Price'),
        store=True)
    total_tax = fields.Float(
        string='Total taxes',
        compute='compute_totals',
        digits_compute=dp.get_precision('Sale Price'),
        store=True)
    net_cost = fields.Float(
        string='Net Cost',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    net_cost_percentage = fields.Float(
        string='Net Cost %',
        digits_compute=dp.get_precision('Account'),
        readonly=True)
    gross_margin = fields.Float(
        string='Gross Margin',
        readonly=True,
        compute='compute_totals',
        digits_compute=dp.get_precision('Purchase Price'))
    gross_margin_percentage = fields.Float(
        string='Gross Margin %',
        digits_compute=dp.get_precision('Account'),
        compute='compute_totals',
        readonly=True)
    net_margin = fields.Float(
        string='Net Margin',
        readonly=True,
        compute='compute_totals',
        digits_compute=dp.get_precision('Purchase Price'))
    net_margin_percentage = fields.Float(
        string='Net Margin %',
        digits=(3, 2),
        compute='compute_totals',
        readonly=True)
    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='simulation_cost_sale_order_rel',
        column1='cost_id',
        column2='sale_order_id',
        string='Sale Orders',
        readonly=True)
    project_ids = fields.Many2many(
        comodel_name='account.analytic.account',
        relation='simulation_cost_project_rel',
        column1='cost_id',
        column2='project_id',
        string='Projects',
        readonly=True)
    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode',
        string='Payment Mode',
        domain="[('sale_ok', '=', True)]")

    @api.one
    @api.depends('tax_ids')
    def compute_totals(self):
        pass

    @api.one
    @api.depends('simulation_id')
    def compute_history_ids(self):
        rows = self.env['simulation.cost.history'].search([
            ('cost_id', '=', self.id),
            ('active_cost_ids', '=', self.simulation_id.id)])
        self.history_ids = rows

    @api.one
    def switch_simulation(self, simulation_id):
        self.simulation_id.active_cost_ids = [(6, 0, [])]
        simulation_id.active_cost_ids = [(6, 0, [self.id])]

    @api.one
    def new_simulation(self):
        self.write({'active_cost_ids': [(5)]})
        new = self.env['simulation.cost.history'].create({
            'cost_id': self.id,
            'active_cost_ids': [(6, 0, [self.id])],
            'pricelist_id': self.pricelist_id.id,
            'currency_id': self.currency_id.id,
            'name': self.name,
            'simulation_number': self.simulation_number,
        })
        for line in self.line_ids:
            if line.product_id:
                res_sale = self.env['sale.order.line'].product_id_change(
                    pricelist=line.cost_id.pricelist_id.id,
                    product=line.product_id.id, qty=line.uom_qty or 0,
                    uom=line.product_id.uom_id.id or False, qty_uos=0,
                    uos=False, name='',
                    partner_id=line.cost_id.partner_id.id or False,
                    lang=False, update_tax=True,
                    date_order=False, packaging=False,
                    fiscal_position=False, flag=False)
                sale_price = res_sale['value']['price_unit'] or None
                if 'discount' in res_sale['value']:
                    sale_discount = res_sale['value']['discount']
                else:
                    sale_discount = 0
            self.env['simulation.cost.history.line'].create({
                'history_id': new.id,
                'product_id': line.product_id.id,
                'sequence': line.sequence,
                'cost_id': line.cost_id.id,
                'line_id': line.id,
                'name': line.name,
                'uom_id': line.uom_id.id,
                'quantity': line.uom_qty,
                'price': sale_price,
                'discount': sale_discount,
                'quantity_sale': line.uom_qty,
            })

    @api.one
    def set_simulation(self):
        self.state = 'simulation'

    @api.one
    def set_cancel(self):
        self.state = 'draft'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            return
        self.user_id = self.partner_id.user_id.id or None
        section = self.user_id.default_section_id
        self.section_id = section and section.id or None
        if not self.env.user.company_id:
            raise exceptions.Warning(
                _('Error!'),
                _('There is no default company for the current user!'))
        self.pricelist_id = self.partner_id.property_product_pricelist.id
        self.payment_mode_id = self.partner_id.customer_payment_mode.id

    @api.onchange('user_id')
    def onchange_user_id(self):
        if not self.user_id:
            return
        section = self.user_id.default_section_id
        self.section_id = section and section.id or None

    @api.multi
    def button_wizard_history_pricelist(self):
        view = self.env.ref('cost_simulator.view_wizard_history_pricelist')
        return {
            'name': _('Update Sales Prices'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.history.pricelist',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def button_wizard_simulation_accepted(self):
        if not self.simulation_id:
            raise exceptions.Warning(
                _('Error'), _('Please create simulation'))

        view = self.env.ref('cost_simulator.view_wizard_simulation_accepted')
        return {
            'name': _('Simulation Accepted'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.simulation.accepted',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.one
    def update_cost(self):
        for line in self.line_ids:
            line.product_id_change()

    @api.model
    def create(self, values):
        if values.get('simulation_number', '/') == '/':
            values['simulation_number'] = self.env['ir.sequence'].get(
                'cost.simulation') or '/'
            return super(SimulationCost, self).create(values)

    @api.one
    def write(self, values):
        res = super(SimulationCost, self).write(values)
        return res
