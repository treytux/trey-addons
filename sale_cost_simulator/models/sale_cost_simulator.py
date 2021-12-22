###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
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
        string='Number',
        compute='_compute_label',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        ondelete='set null',
        default=lambda self: self.env.user.company_id,
    )
    ref = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Reference',
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Partner',
    )
    partner_data = fields.Text(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Partner Data',
        required=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        readonly=True,
        states={'draft': [('readonly', False)]},
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
            ('send', 'Sent'),
            ('cancel', 'Cancel'),
            ('done', 'Done'),
        ],
        track_visibility='onchange',
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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if not name:
            name = '%'
        if not args:
            args = []
        args = args[:]
        records = self.search([('ref', operator, name)] + args, limit=limit)
        return records.name_get()

    @api.constrains('ref')
    def _check_ref(self):
        for sale in self:
            if self.search([
                    ('id', 'not in', sale.ids), ('ref', '=', sale.ref)]):
                raise ValidationError(_('Ref %s already exist.') % sale.ref)

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

    @api.depends('name')
    def _compute_label(self):
        for sale in self:
            sale.simulation_number = sale.name

    @api.depends('line_ids')
    def compute_total(self):
        for sale in self:
            for line in sale.line_ids:
                line.compute_total()
            sale.amount_untaxed = sum(
                line.total_untaxed for line in sale.line_ids)
            sale.amount_tax = sum(line.total_tax for line in sale.line_ids)
            sale.amount_total = sale.amount_untaxed + sale.amount_tax

    @api.multi
    def copy(self, default=None):
        def set_simulator(line, simulator_id):
            line.simulator_id = simulator_id
            for sline in line.child_ids:
                set_simulator(sline, simulator_id)

        self.ensure_one()
        default = dict(default or {})
        default['ref'] = _('%s (copy)') % self.ref
        res = super().copy(default)
        for line in res.mapped('line_ids'):
            set_simulator(line, res.id)
        return res

    @api.multi
    def button_dummy(self):
        for sale in self:
            sale.compute_total()

    @api.multi
    def to_cancel(self):
        for sale in self:
            sale.state = 'cancel'

    @api.multi
    def to_draft(self):
        for sale in self:
            sale.state = 'draft'

    @api.multi
    def to_send(self):
        for sale in self:
            sale.state = 'send'
            sale.compute_total()

    @api.multi
    def to_done(self):
        for sale in self:
            sale.state = 'done'

    @api.multi
    def action_send_email(self):
        self.ensure_one()
        template = self.env.ref(
            'sale_cost_simulator.email_template_edi_sale_simulate_cost', False)
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = dict(default_model='sale.cost.simulator',
                   default_use_template=bool(template),
                   default_template_id=template.id,
                   default_res_id=self.id,
                   default_composition_mode='comment')
        partners = self.mapped('message_follower_ids.partner_id')
        if self.partner_id not in partners:
            partners |= self.partner_id
            ctx.update(default_partner_ids=partners.ids)
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def open_simulation_lines(self):
        self.ensure_one()
        Line = self.env['sale.cost.line']
        lines = self.mapped('line_ids')
        self.ensure_one()
        parents = Line.search([('parent_id', 'child_of', lines.ids)])
        action = self.env.ref(
            'sale_cost_simulator.sale_cost_line_tree_action').read()[0]
        action.update({
            'name': _("Simulation Cost Lines"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.cost.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'current',
            'domain': [('id', 'in', self.ids + parents.ids)],
        })
        return action
