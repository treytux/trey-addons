###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class ContractLiteLine(models.Model):
    _name = 'contract_lite.line'
    _description = 'Contract Line'
    _order = 'id asc'

    name = fields.Text(
        string='Description',
    )
    contract_id = fields.Many2one(
        comodel_name='contract_lite.contract',
        required=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        related='contract_id.company_id',
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        related='contract_id.partner_id',
        store=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True,
    )
    automatic_price = fields.Boolean(
        string='Automatic price',
        default=True,
    )
    price_unit = fields.Float(
        string='Unit price',
        compute='_compute_price_unit',
        inverse='_inverse_price_unit',
        store=True,
    )
    manual_price_unit = fields.Float(
        string='Manual unit price',
        default=0.0,
    )
    quantity = fields.Float(
        default=1.0,
        required=True,
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        compute='_compute_uom_id',
        store=True,
        readonly=False,
        required=True,
    )
    discount = fields.Float(
        string='Discount (%)',
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        store=True,
        readonly=True,
    )
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True,
        currency_field='currency_id',
    )
    recurring_interval = fields.Integer(
        default=1,
        required=True,
    )
    recurring_rule_type = fields.Selection(
        selection=[
            ('dayly', 'Days'),
            ('weekly', 'Weeks'),
            ('monthly', 'Months'),
            ('quarterly', 'Quarters'),
            ('four_monthly', 'Four-month periods'),
            ('semesterly', 'Semesters'),
            ('yearly', 'Years'),
        ],
        default='monthly',
        required=True,
    )
    date_start = fields.Date(
        string='Start date',
        required=True,
        default=fields.Date.context_today,
    )
    recurring_next_date = fields.Date(
        string='Next invoice date',
        compute='_compute_recurring_next_date',
        inverse='_inverse_recurring_next_date',
        store=True,
        readonly=False,
        required=True,
    )
    manual_recurring_next_date = fields.Date(
        string='Manual next invoice date',
    )
    date_end = fields.Date(
        string='End date',
    )
    next_period_date_end = fields.Date(
        string='Next period end date',
        compute='_compute_next_period_date_end',
        store=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
    )

    @api.depends('product_id')
    def _compute_uom_id(self):
        for line in self:
            if line.uom_id:
                continue
            if line.product_id:
                line.uom_id = line.product_id.uom_id

    @api.depends(
        'automatic_price',
        'product_id',
        'quantity',
        'uom_id',
        'partner_id',
        'manual_price_unit',
    )
    def _compute_price_unit(self):
        for line in self:
            if not line.product_id:
                line.price_unit = 0.0
                continue
            if line.automatic_price:
                line.price_unit = line.get_pricelist_price_unit()
            else:
                line.price_unit = line.manual_price_unit or 0.0

    def _inverse_price_unit(self):
        for line in self:
            if not line.automatic_price:
                line.manual_price_unit = line.price_unit

    @api.depends('date_start', 'manual_recurring_next_date')
    def _compute_recurring_next_date(self):
        for line in self:
            line.recurring_next_date = (
                line.manual_recurring_next_date or line.date_start)

    def _inverse_recurring_next_date(self):
        for line in self:
            line.manual_recurring_next_date = line.recurring_next_date

    @api.depends('quantity', 'price_unit', 'discount')
    def _compute_price_subtotal(self):
        for line in self:
            disc = max(line.discount or 0.0, 0.0)
            line.price_subtotal = (
                (line.quantity or 0.0)
                * (line.price_unit or 0.0)
                * (1.0 - (disc / 100.0))
            )

    @api.depends(
        'recurring_next_date', 'recurring_interval', 'recurring_rule_type')
    def _compute_next_period_date_end(self):
        for line in self:
            if not line.recurring_next_date:
                line.next_period_date_end = False
                continue
            line.next_period_date_end = line.period_date_end(
                line.recurring_next_date)

    def get_pricelist_price_unit(self):
        self.ensure_one()
        if not self.product_id:
            return 0.0
        pricelist = self.partner_id.property_product_pricelist
        if not pricelist:
            return self.product_id.lst_price
        qty = self.quantity or 1.0
        uom = self.uom_id or self.product_id.uom_id
        pricelist_ctx = pricelist.with_context(partner_id=self.partner_id.id)
        today = fields.Date.context_today(self)
        if hasattr(pricelist_ctx, 'get_product_price'):
            try:
                return pricelist_ctx.get_product_price(
                    self.product_id,
                    qty,
                    self.partner_id,
                    uom_id=uom.id,
                    date=today,
                )
            except Exception:
                pass
            try:
                return pricelist_ctx.get_product_price(
                    self.product_id,
                    qty,
                    self.partner_id,
                )
            except Exception:
                pass
        try:
            return pricelist_ctx._get_product_price(
                self.product_id,
                qty,
                uom,
                date=today,
            )
        except Exception:
            pass
        try:
            return pricelist_ctx._get_product_price(self.product_id, qty, uom)
        except Exception:
            return self.product_id.lst_price

    def compute_next_date(self, from_date):
        self.ensure_one()
        interval = max(self.recurring_interval, 1)
        if self.recurring_rule_type == 'dayly':
            return from_date + relativedelta(days=interval)
        if self.recurring_rule_type == 'weekly':
            return from_date + relativedelta(weeks=interval)
        if self.recurring_rule_type == 'monthly':
            return from_date + relativedelta(months=interval)
        if self.recurring_rule_type == 'quarterly':
            return from_date + relativedelta(months=3 * interval)
        if self.recurring_rule_type == 'four_monthly':
            return from_date + relativedelta(months=4 * interval)
        if self.recurring_rule_type == 'semesterly':
            return from_date + relativedelta(months=6 * interval)
        return from_date + relativedelta(years=interval)

    def period_date_end(self, date_start):
        self.ensure_one()
        return self.compute_next_date(date_start) + relativedelta(days=-1)

    def render_invoice_line_description(self, date_start):
        self.ensure_one()
        date_end = self.period_date_end(date_start)
        template = self.name or self.product_id.display_name
        return self.contract_id.render_line_description(
            template,
            date_start,
            date_end,
        ) or (self.product_id.display_name or '')
