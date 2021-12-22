###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class SaleOpenSimulator(models.TransientModel):
    _name = 'sale.open.simulator'
    _description = 'Simulator Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('readonly', 'Readonly'),
        ],
        string='label',
        default='draft',
    )
    line_ids = fields.One2many(
        comodel_name='sale.open.simulator.line',
        inverse_name='simulation_id',
        string='Lines',
        states={'readonly': [('readonly', True)]},
    )
    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Related',
        ondelete='set null',
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        readonly=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        states={'readonly': [('readonly', True)]},
    )
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
        default=0.0,
        states={'readonly': [('readonly', True)]},
    )
    margin = fields.Float(
        string='Margin',
        digits=dp.get_precision('Discount'),
        default=0.0,
        states={'readonly': [('readonly', True)]},
    )
    amount_total = fields.Monetary(
        string='Total',
        readonly=True,
        compute='_compute_total',
        store=True,
    )
    cost_total = fields.Monetary(
        string='Cost',
        readonly=True,
        compute='_compute_total',
        store=True,
    )
    margin_total = fields.Float(
        string='Margin',
        digits=dp.get_precision('Discount'),
        compute='_compute_total',
        store=True,
        readonly=True,
    )

    @api.onchange('pricelist_id')
    def onchange_pricelist(self):
        for line in self.line_ids:
            line.update_prices(self.pricelist_id)

    @api.onchange('discount')
    def onchange_discount(self):
        for line in self.line_ids:
            line.discount = self.discount
        self.line_ids._onchange_discount()

    @api.onchange('margin')
    def onchange_margin(self):
        for line in self.line_ids:
            line.margin = self.margin
        self.line_ids._onchange_margin()

    @api.depends('line_ids.price_subtotal', 'line_ids.standard_price',
                 'line_ids.price_unit')
    def _compute_total(self):
        for wizard in self:
            wizard.amount_total = sum(wizard.mapped('line_ids.price_subtotal'))
            cost = sum(
                [ln.standard_price * ln.product_qty for ln in wizard.line_ids])
            wizard.cost_total = cost
            if not cost or not wizard.amount_total:
                wizard.margin_total = 0
                continue
            wizard.margin_total = self.line_ids._calculate_margin(
                cost, wizard.amount_total, 0)

    @api.multi
    def action_update(self):
        for line in self.line_ids:
            line.sale_line_id.write({
                'product_uom_qty': line.product_qty,
                'price_unit': line.price_unit,
                'standard_price': line.standard_price,
                'discount': line.discount,
            })


class SaleOpenSimulatorLine(models.TransientModel):
    _name = 'sale.open.simulator.line'
    _description = 'Simulator Line'

    simulation_id = fields.Many2one(
        comodel_name='sale.open.simulator',
        string='Simulator',
    )
    name = fields.Char(
        string='Description',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    product_qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        default=1.0,
    )
    price_unit = fields.Float(
        string='Unit Price',
        digits=dp.get_precision('Product Price'),
        default=0.0,
    )
    pl_discount = fields.Float(
        related='sale_line_id.pl_discount',
        depends=['sale_line_id'],
        string='Pricelist Discount',
        readonly=True,
    )
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
        default=0.0,
    )
    margin = fields.Float(
        string='Margin (%)',
        digits=dp.get_precision('Discount'),
        default=0.0,
    )
    standard_price = fields.Float(
        string='Cost',
        digits=dp.get_precision('Product Price'),
        default=0.0,
    )
    price_subtotal = fields.Monetary(
        compute='_compute_subtotal',
        string='Subtotal',
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='sale_line_id.order_id.currency_id',
        depends=['sale_line_id.order_id'],
        string='Currency',
        readonly=True,
    )
    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Line',
    )
    stop_update = fields.Boolean(
        string='Stop Update',
        store=False,
    )

    @api.constrains('product_qty')
    def _check_quantity(self):
        for line in self:
            if not line.product_qty > 0.0:
                raise ValidationError(
                    _('Quantity of product must be greater than 0.'))

    def _calculate_subtotal(self):
        self.ensure_one()
        return (
            self.product_qty * self.price_unit
            * (1 - (self.discount or 0.0) / 100.0)
        )

    def _calculate_margin(self, cost, price_unit, discount):
        if not cost:
            return 0
        price_dto = price_unit - (price_unit * (discount / 100))
        margin = cost / (price_dto or 0.01)
        return round((margin - 1) * -100, 2)

    def _calculate_price_unit(self, cost, margin):
        if margin >= 100:
            margin = 99.99
        margin = margin and (margin / 100) or 0
        return cost / (1 - margin)

    def _calculate_discount(self, cost, margin):
        if margin >= 100:
            margin = 99.99
        margin = margin and (margin / 100) or 0
        return cost / (1 - margin)

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        for line in self:
            if line.stop_update:
                continue
            line.stop_update = True
            line.margin = line._calculate_margin(
                line.standard_price, line.price_unit, line.discount)

    @api.onchange('margin')
    def _onchange_margin(self):
        for line in self:
            if line.stop_update:
                continue
            line.stop_update = True
            price = line._calculate_price_unit(
                line.standard_price, line.margin)
            line.price_unit = price / (1 - (line.discount / 100))

    @api.onchange('standard_price')
    def _onchange_standard_price(self):
        for line in self:
            if line.stop_update:
                continue
            line.stop_update = True
            line.price_unit = line._calculate_price_unit(
                line.standard_price, line.margin)

    @api.onchange('discount')
    def _onchange_discount(self):
        for line in self:
            if line.stop_update:
                continue
            line.stop_update = True
            line.margin = line._calculate_margin(
                line.standard_price, line.price_unit, line.discount)

    @api.depends('product_qty', 'price_unit', 'discount')
    def _compute_subtotal(self):
        for line in self:
            line.price_subtotal = line._calculate_subtotal()

    def update_prices(self, pricelist):
        self.ensure_one()
        sale = self.sale_line_id.order_id
        product = self.product_id.with_context(
            lang=sale.partner_id.lang,
            partner=sale.partner_id,
            quantity=self.product_qty,
            date=sale.date_order,
            pricelist=sale.pricelist_id.id,
            uom=self.sale_line_id.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )
        product_ctx = dict(
            self._context,
            partner_id=sale.partner_id.id,
            date=sale.date_order,
            uom=self.sale_line_id.product_uom.id,
        )
        pricelist = pricelist.with_context(product_ctx)
        price, rule_id = pricelist.get_product_price_rule(
            self.product_id, self.product_qty or 1.0, sale.partner_id)
        sale_line = self.sale_line_id.with_context(product_ctx)
        new_list_price, currency = sale_line._get_real_price_currency(
            product, rule_id, self.product_qty,
            sale_line.product_uom, pricelist.id)
        if new_list_price != 0:
            if pricelist.currency_id != currency:
                new_list_price = currency._convert(
                    new_list_price, pricelist.currency_id,
                    sale.company_id or self.env.user.company_id,
                    sale.date_order or fields.Date.today())
            self.price_unit = new_list_price
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) \
               or (discount < 0 and new_list_price < 0):
                self.discount = discount
        else:
            self.price_unit = price
