##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleCostSimulator(models.Model):
    _name = 'sale.cost.simulator'
    _description = 'Sale cost simulator'
    _inherit = ['mail.thread']
    _order = 'date'

    name = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Name',
    )
    simulation_number = fields.Char(
        string='Name',
        compute='_compute_label',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        ondelete='restrict',
        default=lambda self: self.env.company,
    )
    ref = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Reference',
        required=True,
    )
    partner_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='res.partner',
        string='Partner',
    )
    partner_data = fields.Text(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Partner',
        required=True,
    )
    pricelist_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='product.pricelist',
        required=True,
        string='Pricelist',
    )
    line_ids = fields.One2many(
        comodel_name='sale.cost.line',
        inverse_name='simulator_id',
        ondelete='cascade',
        copy=True,
        domain=[('parent_id', '=', False)],
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Lines',
    )
    amount_untaxed = fields.Float(
        string='Untaxed',
        compute='compute_total',
    )
    amount_tax = fields.Float(
        string='Taxes',
        compute='compute_total',
    )
    amount_total = fields.Float(
        string='Total',
        compute='compute_total',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('send', 'Sended'),
            ('cancel', 'Cancel'),
            ('done', 'Done'),],
        tracking=True,
        copy=False,
        string='State',
        default='draft',
    )
    date = fields.Date(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Date',
        default=fields.Date.today,
    )

    def name_search(self, name='', args=None, operator='ilike', limit=80):
        if not args:
            args = []
        if name:
            records = self.search([
                ('ref', operator, name),
            ] + args, limit=limit)
        else:
            records = self.search(args, limit=limit)
        return records.name_get()

    @api.constrains('ref')
    def _check_ref(self):
        for record in self:
            ref_exist = self.search_count([
                ('id', '!=', record.id),
                ('ref', '=', record.ref),
            ])
            if ref_exist:
                raise ValidationError(_('Ref %s already exist.') % record.ref)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        partner = self.partner_id
        if not partner:
            return
        self.pricelist_id = partner.property_product_pricelist
        self.partner_data = '\n'.join([
            partner.name or '',
            partner.contact_address or '',
            partner.phone or '',
            partner.mobile or '',
            partner.vat or ''
        ])

    @api.depends('name')
    def _compute_label(self):
        for record in self:
            record.simulation_number = record.name

    @api.depends('line_ids.total_untaxed', 'line_ids.total_tax')
    def compute_total(self):
        for record in self:
            record.line_ids.compute_total()
            record.amount_untaxed = sum(
                record.line_ids.mapped('total_untaxed'))
            record.amount_tax = sum(record.line_ids.mapped('total_tax'))
            record.amount_total = record.amount_untaxed + record.amount_tax

    def copy(self, default=None):
        default = dict(default or {})
        default['ref'] = _('%s (copy)') % self.ref
        new_simulator = super(SaleCostSimulator, self).copy(default)

        def _set_simulator(line, simulator):
            line.simulator_id = simulator
            for child in line.child_ids:
                _set_simulator(child, simulator)

        for simulator in new_simulator:
            for line in simulator.line_ids:
                _set_simulator(line, simulator)
        return new_simulator

    def button_dummy(self):
        self.compute_total()

    def to_cancel(self):
        self.state = 'cancel'

    def to_draft(self):
        self.state = 'draft'

    def to_send(self):
        self.state = 'send'
        self.compute_total()

    def to_done(self):
        self.state = 'done'

    def action_send_email(self):
        self.ensure_one()
        template = self.env.ref(
            'sale_cost_simulator.email_template_edi_sale_simulate_cost', False)
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = {
            'default_model': 'sale.cost.simulator',
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_res_id': self.id,
            'default_composition_mode': 'comment',
            'active_model': 'sale.cost.simulator',
            'active_id': self.id,
            'active_ids': [self.id],
        }
        if self.partner_id:
            if self.partner_id not in self.message_partner_ids:
                self.message_subscribe(partner_ids=self.partner_id.ids)
            ctx['default_partner_ids'] = self.message_partner_ids.ids
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
