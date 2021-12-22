###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleCostSimulatorLine(models.Model):
    _name = 'sale.cost.line'
    _description = 'Sale cost simulator line'
    _order = 'sequence'

    name = fields.Char(
        states={'draft': [('readonly', False)]},
        string='Name',
        required=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('send', 'Sent'),
            ('cancel', 'Cancel'),
            ('done', 'Done'),
        ],
        related='simulator_id.state',
        string='State',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        states={'draft': [('readonly', False)]},
        string='Company',
        required=True,
        readonly=True,
        ondelete='set null',
        default=lambda self: self.env.user.company_id.id,
    )
    display_name = fields.Char(
        compute='_compute_display_name',
        states={'draft': [('readonly', False)]},
        string='Display Name',
        store=True,
        readonly=True,
    )
    sequence = fields.Integer(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Sequence',
    )
    simulator_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='sale.cost.simulator',
        string='Simulator',
    )
    simulator_ref_id = fields.Char(
        readonly=True,
        related='simulator_id.ref',
        string='Simulator Ref',
    )
    partner_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        related='simulator_id.partner_id',
    )
    level = fields.Integer(
        string='Level',
        compute='_compute_level',
    )
    parent_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='sale.cost.line',
        ondelete='cascade',
        string='Parent',
    )
    child_ids = fields.One2many(
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=True,
        comodel_name='sale.cost.line',
        inverse_name='parent_id',
    )
    childs_number = fields.Integer(
        string="Number of childs",
        compute='_get_childs_number',
    )
    product_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='product.product',
        string='Product',
    )
    pricelist_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='product.pricelist',
        string='Pricelist',
    )
    uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id',
    )
    uom_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='uom.uom',
        domain='[("category_id", "=", uom_category_id)]',
        string='UoM',
    )
    quantity = fields.Float(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Quantity',
        default=1,
    )
    price_unit = fields.Float(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Unit price',
    )
    discount = fields.Float(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Discount (%)',
    )
    description = fields.Text(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Description',
    )
    tax_ids = fields.Many2many(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='account.tax',
        relation='sale_cost_list2tax_rel',
        column1='line_id',
        column2='tax_od',
        string='Taxes',
    )
    amount_untaxed = fields.Float(
        readonly=True,
        string='Untaxed',
        compute='compute_total',
    )
    amount_discount = fields.Float(
        string='Discount',
        compute='compute_total',
    )
    amount_tax = fields.Float(
        string='Total Taxes',
        compute='compute_total',
    )
    amount_total = fields.Float(
        string='Subtotal',
        compute='compute_total',
    )
    total_untaxed = fields.Float(
        string='Total untaxed',
        compute='compute_total',
    )
    total_tax = fields.Float(
        string='Total taxes',
        compute='compute_total',
    )
    total_total = fields.Float(
        string='Total',
        compute='compute_total',
    )

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for line in self:
            if not line.parent_id:
                return
            if line.parent_id == line:
                raise ValidationError(_('Error! parent with cross reference.'))

    @api.depends('parent_id')
    def _compute_level(self):
        def count(obj):
            return obj.parent_id and 1 + count(obj.parent_id) or 1

        for line in self:
            line.level = count(line)

    @api.multi
    def _get_childs_number(self):
        for line in self:
            line.childs_number = len(line.child_ids.ids)

    @api.multi
    def compute_this(self):
        def compute_tax(tax):
            res = tax.compute_all(
                self.price_unit, self.pricelist_id.currency_id,
                self.quantity, self.product_id.id, self.partner_id)
            return res['total_included'] - res['base']

        for line in self:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.amount_untaxed = price_unit * line.quantity
            line.amount_discount = line.amount_untaxed - (
                line.price_unit * line.quantity)
            line.amount_tax = sum([compute_tax(t) for t in line.tax_ids])
            line.amount_total = line.amount_untaxed + line.amount_tax

            line.total_untaxed = sum(c.total_untaxed for c in
                                     line.child_ids) + line.amount_untaxed
            line.total_tax = (
                sum(c.total_tax for c in line.child_ids) + line.amount_tax)
            line.total_total = line.total_untaxed + line.total_tax

    @api.depends('price_unit', 'quantity', 'discount', 'tax_ids', 'child_ids')
    def compute_total(self):
        for line in self:
            for child in line.child_ids:
                child.compute_total()
            line.compute_this()

    @api.multi
    def button_dummy(self):
        for line in self:
            line.compute_total()

    @api.multi
    def partner_id_get(self):
        self.ensure_one()
        return self.partner_id.id or self.env.user.company_id.partner_id.id

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.partner_id.property_account_position_id
            taxes = line.product_id.taxes_id.filtered(lambda r: (
                not line.company_id or r.company_id == line.company_id))
            line.tax_ids = fpos.map_tax(
                taxes, line.product_id, line.order_id.partner_shipping_id) \
                if fpos else taxes

    @api.multi
    def _get_display_price(self, product):
        if self.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(
                pricelist=self.pricelist_id.id,
                uom=self.uom_id.id).price
        product_context = dict(
            self.env.context, partner_id=self.partner_id.id,
            date=fields.Date.today(), uom=self.uom_id.id)
        final_price, rule_id = self.pricelist_id.with_context(
            product_context).get_product_price_rule(
                product or self.product_id,
                self.quantity or 1.0, self.partner_id)
        base_price, currency = self.with_context(
            product_context)._get_real_price_currency(
                product, rule_id, self.quantity, self.uom_id,
                self.pricelist_id.id)
        if currency != self.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.pricelist_id.currency_id,
                self.company_id or self.env.user.company_id,
                fields.Date.today())
        return max(base_price, final_price)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.name = self.product_id.name
        self.description = self.product_id.description_sale
        self.uom_id = self.product_id.uom_id.id
        if not self.pricelist_id:
            self.pricelist_id = (
                (self.parent_id and self.parent_id.pricelist_id)
                and (self.parent_id.pricelist_id.id
                     or self.simulator_id.pricelist_id.id))
        self._compute_tax_id()
        if self.pricelist_id and self.partner_id:
            self.price_unit = self.env['account.tax'].\
                _fix_tax_included_price_company(
                    self._get_display_price(self.product_id),
                    self.product_id.taxes_id, self.tax_ids,
                    self.company_id)

    @api.multi
    def compute_pricelist(self, pricelist_id=None):
        Tax = self.env['account.tax']
        for line in self:
            if pricelist_id:
                line.pricelist_id = pricelist_id
            if not line.product_id:
                return
            if line.partner_id:
                line.price_unit = Tax._fix_tax_included_price_company(
                    self._get_display_price(line.product_id),
                    line.product_id.taxes_id, line.tax_ids, line.company_id)
            line.compute_this()

    @api.multi
    def action_open_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Model Title',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.ids[0],
            'target': 'current',
        }

    @api.depends('name', 'parent_id')
    def _compute_display_name(self):
        def get_all_parents(line):
            if not line.parent_id:
                return [line.name or '']
            return get_all_parents(line.parent_id) + [line.name or '']
        for line in self:
            line.display_name = ' / '.join(get_all_parents(line))
