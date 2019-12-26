# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    commission_total = fields.Float(
        compute='_compute_commission_total',
        string='Commissions')
    booking_net_price = fields.Float(
        related='booking_id.booking_net_price',
        readonly=True)
    settlement_id = fields.Many2one(
        comodel_name='booking.commission.settlement',
        string='settlement',
        required=False)

    @api.multi
    def _compute_commission_total(self):
        for invoice in self:
            commission_total = sum(
                [line.commission_amount for line in invoice.invoice_line])
            invoice.commission_total = commission_total

    @api.multi
    def action_cancel(self):
        """Put settlements associated to the invoices in exception."""
        settlements = self.env['booking.commission.settlement'].search(
            [('invoice', 'in', self.ids)])
        settlements.write({'state': 'except_invoice', 'settlement_id': None})
        return super(AccountInvoice, self).action_cancel()

    @api.multi
    def invoice_validate(self):
        """Put settlements associated to the invoices again in invoice."""
        settlements = self.env['booking.commission.settlement'].search(
            [('invoice', 'in', self.ids)])
        settlements.write({'state': 'invoiced'})
        return super(AccountInvoice, self).invoice_validate()

    @api.model
    def _refund_cleanup_lines(self, lines):
        """ugly function to map all fields of account.invoice.line
        when creates refund invoice"""
        res = super(AccountInvoice, self)._refund_cleanup_lines(lines)
        if lines and lines[0]._name != 'account.invoice.line':
            return res
        for i, line in enumerate(lines):
            vals = res[i][2]
            agents = super(AccountInvoice, self)._refund_cleanup_lines(
                line['agents'])
            # Remove old reference to source invoice
            for agent in agents:
                agent_vals = agent[2]
                del agent_vals['invoice']
                del agent_vals['invoice_line']
            vals['agents'] = agents
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.model
    def _default_agents(self):
        agents = []
        partner_id = self.env.context.get('partner_id')
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            invoice_line_agent_obj = self.env['account.invoice.line.agent']
            for agent in partner.agents:
                vals = {'agent': agent.id,
                        'commission': agent.commission.id,
                        'amount': agent.amount}
                vals['display_name'] = (
                    invoice_line_agent_obj.new(vals).display_name)
                agents.append(vals)
        return [(0, 0, x) for x in agents]

    agents = fields.One2many(
        comodel_name="account.invoice.line.agent",
        inverse_name="invoice_line",
        string="Agents & commissions",
        help="Agents/Commissions related to the invoice line.",
        default=_default_agents,
        copy=True)
    commission_amount = fields.Float(
        string='Commission amount')
    commission_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='commission tax')


class AccountInvoiceLineAgent(models.Model):
    _name = "account.invoice.line.agent"

    @api.depends('agent_line', 'agent_line.settlement.state', 'invoice',
                 'invoice.state')
    def _compute_settled(self):
        # Count lines of not open or paid invoices as settled for not
        # being included in settlements
        for line in self:
            state = (
                line.invoice.state not in ('open', 'paid') or
                any(x.settlement.state != 'cancel' for x in line.agent_line))
            line.settled = state
        return

    @api.depends('invoice_line.price_subtotal')
    def _compute_amount(self):
        #  REVISAR
        for line in self:
            line.amount = 0.0
            if line.commission:
                if line.commission.commission_type == 'fixed':
                    line.amount = line.invoice_line.commission_amount

    invoice_line = fields.Many2one(
        comodel_name="account.invoice.line",
        ondelete="cascade",
        required=True,
        copy=False)
    invoice = fields.Many2one(
        string="Invoice",
        comodel_name="account.invoice",
        related="invoice_line.invoice_id",
        store=True)
    invoice_date = fields.Date(
        string="Invoice date",
        related="invoice.date_invoice",
        store=True, readonly=True)
    product = fields.Many2one(
        comodel_name='product.product',
        related="invoice_line.product_id")
    agent = fields.Many2one(
        comodel_name="res.partner",
        domain="[('agent', '=', True)]",
        ondelete="restrict",
        required=True)
    commission = fields.Many2one(
        comodel_name="booking.commission",
        ondelete="restrict",
        required=True)
    amount = fields.Float(
        string="Amount settled",
        compute="_compute_amount",
        store=True)
    agent_line = fields.Many2many(
        comodel_name='booking.commission.settlement.line',
        relation='settlement_agent_line_rel',
        column1='agent_line_id',
        column2='settlement_id',
        copy=False)
    settled = fields.Boolean(
        compute="_compute_settled",
        store=True,
        copy=False)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="invoice.company_id",
        store=True)

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = "%s: %s" % (record.agent.name, record.commission.name)
            res.append((record.id, name))
        return res

    @api.depends('agent', 'commission')
    def _compute_display_name(self):
        return super(AccountInvoiceLineAgent, self)._compute_display_name()

    @api.onchange('agent')
    def onchange_agent(self):
        self.commission = self.agent.commission

    _sql_constraints = [
        ('unique_agent', 'UNIQUE(invoice_line, agent)',
         'You can only add one time each agent.')
    ]
