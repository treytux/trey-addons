##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleCostSimulatorLine(models.Model):
    _name = 'sale.cost.line'
    _description = 'Sale cost simulator line'
    _order = 'sequence'

    def _default_tax_ids(self):
        return self.env['account.tax'].browse()

    name = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Name',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('send', 'Sended'),
            ('cancel', 'Cancel'),
            ('done', 'Done'),],
        copy=False,
        string='state',
        related='simulator_id.state',
    )
    company_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        comodel_name='res.company',
        string='Company',
        required=True,
        ondelete='restrict',
        default=lambda self: self.env.company,
    )
    display_name = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
        string='Display name',
        store=True,
        compute='_compute_display_name',
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
        string='Simulator ref',
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
        string='Number of childs',
        compute='_compute_childs_number',
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
        string='Taxs',
        default=_default_tax_ids,
    )
    amount_untaxed = fields.Float(
        readonly=True,
        string='Untaxed',
        compute='compute_total',
        store=False,
    )
    amount_discount = fields.Float(
        string='Discount',
        compute='compute_total',
    )
    amount_tax = fields.Float(
        string='Taxes',
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
        for record in self:
            if record.parent_id.id == record.id:
                raise ValidationError(_('Error! Parent with cross reference.'))
            parent = record.parent_id
            while parent:
                if parent.id == record.id:
                    raise ValidationError(_('Cycle detected in parent chain.'))
                parent = parent.parent_id

    @api.depends('parent_id')
    def _compute_level(self):
        def _count(obj):
            return obj.parent_id and 1 + _count(obj.parent_id) or 1
        for line in self:
            line.level = _count(line)

    @api.depends('child_ids')
    def _compute_childs_number(self):
        for line in self:
            line.childs_number = len(line.child_ids)

    def _compute_this(self):
        for line in self:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.amount_untaxed = price_unit * line.quantity
            line.amount_discount = (
                line.amount_untaxed - (line.price_unit * line.quantity))
            currency = (
                line.pricelist_id.currency_id
                or line.simulator_id.pricelist_id.currency_id
                or line.company_id.currency_id
                or line.env.company.currency_id
            )
            tax_results = line.tax_ids.compute_all(
                price_unit=price_unit,
                quantity=line.quantity,
                product=line.product_id,
                partner=line.partner_id,
                currency=currency)
            line.amount_tax = (
                tax_results['total_included'] - tax_results['total_excluded'])
            line.amount_total = line.amount_untaxed + line.amount_tax
            children_total_untaxed = sum(
                c.total_untaxed for c in line.child_ids)
            children_total_tax = sum(c.total_tax for c in line.child_ids)
            line.total_untaxed = children_total_untaxed + line.amount_untaxed
            line.total_tax = children_total_tax + line.amount_tax
            line.total_total = line.total_untaxed + line.total_tax

    @api.depends(
        'price_unit', 'quantity', 'discount', 'tax_ids',
        'child_ids.price_unit', 'child_ids.quantity', 'child_ids.discount',
        'child_ids.tax_ids', 'child_ids.total_untaxed',
        'child_ids.total_tax')
    def compute_total(self):
        for line in self:
            line._compute_this()

    def button_dummy(self):
        self.compute_total()

    def action_open_line(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale cost line'),
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }

    def _get_partner_id(self):
        return self.partner_id or self.env.company.partner_id

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        self.name = self.product_id.name
        self.description = self.product_id.description_sale
        self.uom_id = self.product_id.uom_id
        if not self.pricelist_id:
            self.pricelist_id = (
                self.parent_id.pricelist_id or self.simulator_id.pricelist_id)
        if self.pricelist_id:
            self.price_unit = self.pricelist_id._get_product_price(
                self.product_id, self.quantity or 1.0, uom=self.uom_id)
        taxes = self.product_id.taxes_id.filtered(
            lambda t: t.company_id == self.company_id)
        partner = self._get_partner_id()
        acc_fiscal_pos_obj = self.env['account.fiscal.position']
        if partner:
            fpos = acc_fiscal_pos_obj._get_fiscal_position(partner)
            taxes = fpos.map_tax(taxes)
        self.tax_ids = [(6, 0, taxes.ids)]

    def compute_pricelist(self, pricelist_id=None):
        self.ensure_one()
        if pricelist_id:
            self.pricelist_id = pricelist_id
        if not self.product_id:
            return
        if self.pricelist_id:
            self.price_unit = self.pricelist_id._get_product_price(
                self.product_id, self.quantity or 1.0, uom=self.uom_id)
        else:
            self.price_unit = 1.0
        self._compute_this()
        for child in self.child_ids:
            child.compute_pricelist(pricelist_id)

    @api.depends('name', 'parent_id')
    def _compute_display_name(self):
        for line in self:
            parts = []
            current = line
            visited = set()
            while current:
                if current.id in visited:
                    break
                visited.add(current.id)
                parts.insert(0, current.name or '')
                current = current.parent_id
            line.display_name = ' / '.join(parts)
