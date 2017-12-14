# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class SaleCostSimulatorLine(models.Model):
    _name = 'sale.cost.line'
    _description = 'Sale cost simulator line'
    _order = 'sequence'

    @api.multi
    def _default_tax_ids(self):
        return self.env['ir.values'].get_default(
            'product.template', 'supplier_taxes_id',
            company_id=self.env.user.company_id.id)

    name = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Name',
        required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('send', 'Sended'),
            ('cancel', 'Cancel'),
            ('done', 'Done')],
        copy=False,
        string='state',
        related='simulator_id.state')
    company_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='res.company',
        string='Company',
        required=True,
        ondelete='set null',
        default=lambda self: self.env.user.company_id.id)
    display_name = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Display Name',
        store=True,
        compute='_compute_display_name')
    sequence = fields.Integer(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Sequence')
    simulator_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='sale.cost.simulator',
        string='Simulator')
    simulator_ref_id = fields.Char(
        readonly=True,
        related='simulator_id.ref',
        string='Simulator Ref')
    partner_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        related='simulator_id.partner_id')
    level = fields.Integer(
        string='Level',
        compute='_compute_level')
    parent_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='sale.cost.line',
        ondelete='cascade',
        string='Parent')
    child_ids = fields.One2many(
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=True,
        comodel_name='sale.cost.line',
        inverse_name='parent_id')
    childs_number = fields.Integer(
        string="Number of childs",
        compute='_get_childs_number')
    product_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='product.product',
        string='Product')
    pricelist_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='product.pricelist',
        domain=[('type', '=', 'sale')],
        string='Pricelist')
    uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')
    uom_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='product.uom',
        domain='[("category_id", "=", uom_category_id)]',
        string='UoM')
    quantity = fields.Float(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Quantity',
        default=1)
    price_unit = fields.Float(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Unit price')
    discount = fields.Float(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Discount (%)')
    description = fields.Text(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Description')
    tax_ids = fields.Many2many(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='account.tax',
        relation='sale_cost_list2tax_rel',
        column1='line_id',
        column2='tax_od',
        string='Taxs',
        default=_default_tax_ids)
    amount_untaxed = fields.Float(
        readonly=True,
        string='Untaxed',
        # store=True,
        compute='compute_total')
    amount_discount = fields.Float(
        string='Discount',
        # store=True,
        compute='compute_total')
    amount_tax = fields.Float(
        string='Taxes',
        # store=True,
        compute='compute_total')
    amount_total = fields.Float(
        string='Subtotal',
        # store=True,
        compute='compute_total')
    total_untaxed = fields.Float(
        string='Total untaxed',
        # store=True,
        compute='compute_total')
    total_tax = fields.Float(
        string='Total taxes',
        # store=True,
        compute='compute_total')
    total_total = fields.Float(
        string='Total',
        # store=True,
        compute='compute_total')

    @api.one
    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self.parent_id:
            return
        if self.parent_id.id == self.id:
            raise exceptions.Warning(_('Error! parent with cross reference.'))

    @api.one
    @api.depends('parent_id')
    def _compute_level(self):
        def count(obj):
            return obj.parent_id and 1 + count(obj.parent_id) or 1

        self.level = count(self)

    @api.one
    def _get_childs_number(self):
        self.childs_number = len(self.child_ids.ids)

    @api.one
    def compute_this(self):
        def compute_tax(tax):
            res = tax.compute_all(self.price_unit, self.quantity,
                                  self.product_id.id, self.partner_id.id)
            return res['total_included'] - res['total']

        price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        self.amount_untaxed = price_unit * self.quantity
        self.amount_discount = self.amount_untaxed - (
            self.price_unit * self.quantity)
        self.amount_tax = sum([compute_tax(t) for t in self.tax_ids])
        self.amount_total = self.amount_untaxed + self.amount_tax

        self.total_untaxed = (
            sum(c.total_untaxed for c in self.child_ids) + self.amount_untaxed)
        self.total_tax = (
            sum(c.total_tax for c in self.child_ids) + self.amount_tax)
        self.total_total = self.total_untaxed + self.total_tax

    @api.one
    @api.depends('price_unit', 'quantity', 'discount', 'tax_ids', 'child_ids')
    def compute_total(self):
        for child in self.child_ids:
            child.compute_total()
        self.compute_this()

    @api.one
    def button_dummy(self):
        self.compute_total()

    @api.multi
    def partner_id_get(self):
        self.ensure_one()
        return (self.partner_id and self.partner_id.id or
                self.env.user.company_id.partner_id.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.name = self.product_id.name
        self.description = self.product_id.description_sale
        self.uom_id = self.product_id.uom_id.id
        if not self.pricelist_id:
            self.pricelist_id = (
                (self.parent_id and self.parent_id.pricelist_id) and
                self.parent_id.pricelist_id.id or
                self.simulator_id.pricelist_id.id)
        res = self.env['sale.order.line'].product_id_change(
            self.pricelist_id.id, self.product_id.id, qty=self.quantity,
            uom=self.uom_id.id or None, partner_id=self.partner_id_get())
        self.price_unit = res['value']['price_unit']
        if res['value']['tax_id'] not in self.tax_ids.ids:
            self.tax_ids = [(6, 0, res['value']['tax_id'])]

    @api.one
    def compute_pricelist(self, pricelist_id=None):
        if pricelist_id:
            self.pricelist_id = pricelist_id
        if not self.product_id:
            return
        res = self.env['sale.order.line'].product_id_change(
            self.pricelist_id.id, self.product_id.id, qty=self.quantity,
            uom=self.uom_id.id, partner_id=self.partner_id_get())
        self.price_unit = res['value'].get('price_unit', 1.)
        self.compute_this()

    @api.multi
    def action_open_line(self):
        return {'type': 'ir.actions.act_window',
                'name': 'Model Title',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': self._name,
                'res_id': self.ids[0],
                'target': 'current'}

    @api.one
    @api.depends('name', 'parent_id')
    def _compute_display_name(self):
        def get_all_parents(line):
            if not line.parent_id:
                return [line.name or '']
            return get_all_parents(line.parent_id) + [line.name or '']

        self.display_name = ' / '.join(get_all_parents(self))
