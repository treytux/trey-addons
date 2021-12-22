###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class SimulationCost(models.Model):
    _name = 'simulation.cost'
    _description = 'Simulation Costs'

    name = fields.Char(
        string='Description/Name',
        required=True,
    )
    simulation_number = fields.Char(
        string='Serial',
        default='/',
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        ondelete='set null',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('simulation', 'Simulation'),
            ('accepted', 'Accepted'),
            ('canceled', 'Canceled')],
        string='State',
        readonly=True,
        default='draft',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Pricelist for current sales order.',
    )
    date = fields.Date(
        string='Date',
        readonly=True,
        default=fields.Date.context_today,
    )
    line_ids = fields.One2many(
        comodel_name='simulation.cost.line',
        inverse_name='cost_id',
        string='Cost Line',
        required=True,
    )
    history_ids = fields.One2many(
        comodel_name='simulation.cost.history',
        inverse_name='cost_id',
        compute='compute_history_ids',
        string='Simulation history',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesperson',
        index=True,
        required=True,
    )
    section_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        required=True,
    )
    simulation_id = fields.Many2one(
        comodel_name='simulation.cost.history',
        string='Simulation',
    )
    simulation_name = fields.Char(
        related='simulation_id.name',
        readonly=True,
        string='Simulation Name',
    )
    simulation_line_ids = fields.One2many(
        related='simulation_id.line_ids',
        readonly=True,
    )
    simulation_pricelist_id = fields.Many2one(
        related='simulation_id.pricelist_id',
        readonly=True,
        string='Simulation Pricelist',
    )
    sale_type = fields.Selection(
        string='Sales Type',
        selection=[
            ('chapter', 'Per Chapter'),
            ('simulation', 'Per Simulation'),
        ],
    )
    project_type = fields.Selection(
        string='Proyect Type',
        selection=[
            ('closed', 'Closed'),
            ('open', 'Open'),
        ],
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='simulator_cost2tax',
        column1='cost_id',
        column2='tax_id',
        string='Taxes',
    )
    total = fields.Float(
        string='Total',
        compute='compute_totals',
        digits=dp.get_precision('Sale Price'),
        store=True,
    )
    total_untaxed = fields.Float(
        string='Total untaxed',
        compute='compute_totals',
        digits=dp.get_precision('Sale Price'),
        store=True,
    )
    total_tax = fields.Float(
        string='Total taxes',
        compute='compute_totals',
        digits=dp.get_precision('Sale Price'),
        store=True,
    )
    net_cost = fields.Float(
        string='Net Cost',
        readonly=True,
        digits=dp.get_precision('Purchase Price'),
    )
    net_cost_percentage = fields.Float(
        string='Net Cost %',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    gross_margin = fields.Float(
        string='Gross Margin',
        readonly=True,
        compute='compute_totals',
        digits=dp.get_precision('Purchase Price'),
    )
    gross_margin_percentage = fields.Float(
        string='Gross Margin %',
        digits=dp.get_precision('Account'),
        compute='compute_totals',
        readonly=True,
    )
    net_margin = fields.Float(
        string='Net Margin',
        readonly=True,
        compute='compute_totals',
        digits=dp.get_precision('Purchase Price'),
    )
    net_margin_percentage = fields.Float(
        string='Net Margin %',
        digits=(3, 2),
        compute='compute_totals',
        readonly=True,
    )
    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='simulation_cost_sale_order_rel',
        column1='cost_id',
        column2='sale_order_id',
        string='Sale Orders',
        readonly=True,
    )
    project_ids = fields.Many2many(
        comodel_name='account.analytic.account',
        relation='simulation_cost_project_rel',
        column1='cost_id',
        column2='project_id',
        string='Projects',
        readonly=True,
    )
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode',
        string='Payment Mode',
        domain='[("payment_type", "=", "inbound")]',
    )
    chapter_ids = fields.One2many(
        comodel_name='simulation.cost.chapter',
        inverse_name='cost_id',
        string='Simulation Cost',
    )
    total_costs = fields.Float(
        string='Total Costs',
        compute='compute_chapter',
    )
    total_sales = fields.Float(
        string='Total Sales',
        compute='compute_chapter',
    )
    total_benefits = fields.Float(
        string='Total Benefits',
        compute='compute_chapter',
    )

    @api.depends('tax_ids')
    def compute_totals(self):
        pass

    @api.depends('simulation_id')
    def compute_history_ids(self):
        History = self.env['simulation.cost.history']
        for cost in self:
            rows = History.search([
                ('cost_id', '=', cost.id),
                ('active_cost_ids', '=', cost.simulation_id.id)])
            cost.history_ids = rows

    @api.multi
    def _prepare_history_values(self):
        self.ensure_one()
        return {
            'cost_id': self.id,
            'active_cost_ids': [(6, 0, [self.id])],
            'pricelist_id': self.pricelist_id.id,
            'currency_id': self.currency_id.id,
            'name': self.name,
            'simulation_number': self.simulation_number,
        }

    @api.multi
    def new_simulation(self):
        History = self.env['simulation.cost.history']
        HistoryLine = self.env['simulation.cost.history.line']
        SaleLine = self.env['sale.order.line']
        for cost in self:
            cost.simulation_id.write({'active_cost_ids': [(5,)]})
            new = History.create(
                cost._prepare_history_values())
            for line in cost.line_ids:
                new_list_price = 0.0
                discount = 0.0
                if line.product_id:
                    product_context = dict(
                        self.env.context,
                        partner_id=cost.partner_id.id,
                        date=cost.date, uom=line.uom_id.id)
                    price, rule_id = cost.pricelist_id.with_context(
                        product_context).get_product_price_rule(
                            line.product_id, line.uom_qty, cost.partner_id)
                    new_list_price, currency = SaleLine.with_context(
                        product_context)._get_real_price_currency(
                            line.product_id, rule_id, line.uom_qty,
                            line.uom_id, cost.pricelist_id.id)
                    if new_list_price != 0:
                        if cost.pricelist_id.currency_id != currency:
                            new_list_price = currency._convert(
                                new_list_price, cost.pricelist_id.currency_id,
                                cost.company_id,
                                cost.date or fields.Date.today())
                            discount = \
                                (new_list_price - price) / new_list_price * 100
                HistoryLine.create({
                    'history_id': new.id,
                    'product_id': line.product_id.id,
                    'sequence': line.sequence,
                    'cost_id': line.cost_id.id,
                    'line_id': line.id,
                    'name': line.name,
                    'quantity': line.uom_qty,
                    'price': new_list_price,
                    'discount': discount,
                    'quantity_sale': line.uom_qty,
                })

    @api.multi
    def set_simulation(self):
        for cost in self:
            cost.state = 'simulation'

    @api.multi
    def set_cancel(self):
        for cost in self:
            cost.state = 'draft'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            return
        self.user_id = self.partner_id.user_id.id
        self.section_id = self.partner_id.team_id.id
        if not self.env.user.company_id:
            raise ValidationError(
                _('There is no default company for the current user!'))
        self.pricelist_id = self.partner_id.property_product_pricelist.id
        self.payment_mode_id = self.partner_id.customer_payment_mode_id.id

    @api.onchange('user_id')
    def onchange_user_id(self):
        if not self.user_id:
            return
        section = self.user_id.partner_id.team_id
        self.section_id = section.id

    @api.multi
    def button_wizard_history_pricelist(self):
        self.ensure_one()
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
        self.ensure_one()
        if not self.simulation_id:
            raise ValidationError(
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

    @api.multi
    def update_cost(self):
        for cost in self:
            for line in cost.line_ids:
                line.product_id_change()

    @api.model
    def create(self, values):
        if values.get('simulation_number', '/') == '/':
            values['simulation_number'] = self.env['ir.sequence'].next_by_code(
                'cost.simulation') or '/'
            return super().create(values)

    @api.depends('line_ids', 'simulation_line_ids')
    def update_chapters(self):
        self.ensure_one()
        tmpls_now = list(set([c.chapter_tmpl_id.id for c in self.chapter_ids]))

        def _create_chapter(tmpl):
            if tmpl.id not in tmpls_now:
                tmpls_now.append(tmpl.id)
                self.chapter_ids.create({
                    'cost_id': self.id,
                    'chapter_tmpl_id': tmpl.id,
                    'name': tmpl.name,
                    'description': tmpl.description,
                })

        def _create_chapter_recursive(tmpl):
            if not tmpl.parent_id:
                _create_chapter(tmpl)
                return False
            _create_chapter_recursive(tmpl.parent_id)
            _create_chapter(tmpl)

        for line in self.line_ids:
            _create_chapter_recursive(line.chapter_tmpl_id)

        self.compute_chapter()

    @api.multi
    def sum_chapter(self, tmpl_id, cost=0, sale=0):
        for chapter in self.chapter_ids:
            if chapter.chapter_tmpl_id.id == tmpl_id:
                chapter.subtotal_cost += cost
                chapter.subtotal_sale += sale
                chapter.subtotal_benefits = (
                    chapter.subtotal_sale - chapter.subtotal_cost)

    @api.multi
    def compute_chapter(self):
        for cost in self:
            cost.total_sales = 0
            cost.total_costs = 0
            cost.total_benefits = 0
            for chapter in cost.chapter_ids:
                chapter.subtotal_cost = 0
                chapter.subtotal_sale = 0
                chapter.subtotal_benefits = 0
            for line in cost.line_ids:
                tmpl = line.chapter_tmpl_id
                cost.total_costs += line.subtotal_cost
                cost.sum_chapter(tmpl.id, cost=line.subtotal_cost)
                for parent in tmpl.get_parents():
                    cost.sum_chapter(parent.id, cost=line.subtotal_cost)
            for line in cost.simulation_line_ids:
                tmpl = line.line_id.chapter_tmpl_id
                cost.total_sales += line.subtotal_sale
                cost.sum_chapter(tmpl.id, sale=line.subtotal_sale)
                if not tmpl.exists():
                    continue
                for parent in tmpl.get_parents():
                    cost.sum_chapter(parent.id, sale=line.subtotal_sale)
            cost.total_benefits = (cost.total_sales - cost.total_costs)
            cost.total_untaxed = cost.total_sales
            tax = cost.tax_ids.compute_all(cost.total_sales, cost.currency_id)
            cost.total_tax = tax['total_included'] - cost.total_untaxed
            cost.total = tax['total_included']
