# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _, exceptions


class SaleCostSimulator(models.Model):
    _name = 'sale.cost.simulator'
    _description = 'Sale cost simulator'
    _inherit = ['mail.thread']
    _order = 'date'

    name = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Name')
    simulation_number = fields.Char(
        string='Name',
        compute='_compute_label')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        ondelete='set null',
        default=lambda self: self.env.user.company_id.id)
    ref = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Reference',
        required=True)
    partner_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='res.partner',
        string='Partner')
    partner_data = fields.Text(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Partner',
        required=True)
    pricelist_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='product.pricelist',
        required=True,
        domain=[('type', '=', 'sale')],
        string='Pricelist')
    line_ids = fields.One2many(
        comodel_name='sale.cost.line',
        inverse_name='simulator_id',
        ondelete='cascade',
        copy=True,
        domain=[('parent_id', '=', False)],
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Lines')
    amount_untaxed = fields.Float(
        string='Untaxed',
        compute='compute_total')
    amount_tax = fields.Float(
        string='Taxes',
        compute='compute_total')
    amount_total = fields.Float(
        string='Total',
        compute='compute_total')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('send', 'Sended'),
            ('cancel', 'Cancel'),
            ('done', 'Done')],
        track_visibility='onchange',
        copy=False,
        string='State',
        default='draft')
    date = fields.Date(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Date',
        default=fields.Date.today)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if not name:
            name = '%'
        if not args:
            args = []
        args = args[:]
        records = self.search([('ref', operator, name)] + args, limit=limit)
        return records.name_get()

    @api.one
    @api.constrains('ref')
    def _check_ref(self):
        if self.search([('id', '!=', self.id), ('ref', '=', self.ref)]):
            raise exceptions.Warning(_('Ref %s already exist.') % self.ref)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        partner = self.partner_id
        if not partner:
            return
        self.pricelist_id = partner.property_product_pricelist.id
        self.partner_data = '\n'.join([partner.name or '',
                                       partner.contact_address or '',
                                       partner.phone or '',
                                       partner.mobile or '',
                                       partner.vat or ''])

    @api.one
    @api.depends('name')
    def _compute_label(self):
        self.simulation_number = self.name

    @api.one
    @api.depends('line_ids')
    def compute_total(self):
        for line in self.line_ids:
            line.compute_total()
        self.amount_untaxed = sum(l.total_untaxed for l in self.line_ids)
        self.amount_tax = sum(l.total_tax for l in self.line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        default['ref'] = _('%s (copy)') % self.ref
        res = super(SaleCostSimulator, self).copy(default)

        def set_simulator(line, simulator_id):
            line.simulator_id = simulator_id
            for l in line.child_ids:
                set_simulator(l, simulator_id)

        for simulator in res:
            for line in res.line_ids:
                set_simulator(line, res.id)
        return res

    @api.one
    def button_dummy(self):
        self.compute_total()

    @api.multi
    def to_cancel(self):
        self.state = 'cancel'

    @api.multi
    def to_draft(self):
        self.state = 'draft'

    @api.multi
    def to_send(self):
        self.state = 'send'
        self.compute_total()

    @api.multi
    def to_done(self):
        self.state = 'done'

    @api.multi
    def action_send_email(self):
        self.ensure_one()
        template = self.env.ref(
            'sale_cost_simulator.email_template_edi_sale_simulate_cost', False)
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='sale.cost.simulator',
            default_use_template=bool(template),
            default_template_id=template.id,
            default_res_id=self.id,
            default_composition_mode='comment')
        return {'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx}
