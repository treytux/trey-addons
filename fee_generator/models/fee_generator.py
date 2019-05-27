# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
from dateutil.relativedelta import relativedelta
import datetime
import openerp.addons.decimal_precision as dp
import time


class FeeGenerator(models.Model):
    _name = 'fee.generator'
    _inherit = ['mail.thread']
    _description = 'Fee Generator'

    def _get_journal(self):
        return self.env['account.invoice'].default_get(
            ['journal_id'])['journal_id']

    name = fields.Char(
        string='Name',
        default=lambda s: s.env['ir.sequence'].get('fee.generator'),
        readonly=True,
        copy=False)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        track_visibility='onchange',
        required=True)
    model_name = fields.Char(
        string='Model name')
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model')
    res_id = fields.Integer(
        string='Resource Id')
    total_untaxed = fields.Float(
        string='Total',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        track_visibility='onchange',
        digits_compute=dp.get_precision('Account'))
    discount = fields.Float(
        string='Discount (%)',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        track_visibility='onchange')
    amount_discount = fields.Float(
        string='Amount discount',
        compute='compute_amount_discount',
        store=True,
        digits_compute=dp.get_precision('Account'))
    start_date = fields.Date(
        string='Start Date',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        default=fields.Date.context_today)
    next_date = fields.Date(
        string='Next Date',
        default=fields.Date.context_today,
        states={
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        track_visibility='onchange')
    end_date = fields.Date(
        string='End Date',
        compute='compute_end_date',
        store=True)
    recurring_interval = fields.Integer(
        string='Repeat Every',
        help='Repeat every (Days/Week/Month/Year)',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        track_visibility='onchange',
        default=1)
    recurring_rule_type = fields.Selection(
        selection=[
            ('daily', 'Day(s)'),
            ('weekly', 'Week(s)'),
            ('monthly', 'Month(s)'),
            ('yearly', 'Year(s)')
        ],
        string='Recurrency',
        help='Invoice automatically repeat at specified interval',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        track_visibility='onchange',
        default='monthly')
    fee_number = fields.Integer(
        string='Total Fees',
        help='Fees Number',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        track_visibility='onchange',
        default=1)
    fee_number_remaining = fields.Integer(
        string='Remaining Fees',
        compute='compute_fee_number_remaining',
        store=True)
    fee_amount_untaxed = fields.Float(
        string='Fee Amount',
        compute='compute_fee_amount_untaxed',
        store=True,
        digits_compute=dp.get_precision('Account'))
    fee_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Fee Product',
        states={
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        track_visibility='onchange',
        required=True)
    reference = fields.Char(
        string='Invoice Reference',
        help='You can use: `#MONTH_INT#`, `#MONTH_STR#`  or `#YEAR_INT#',
        states={
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        required=True)
    description = fields.Char(
        string='Product Description',
        help='Description for product invoice lines',
        states={
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]})
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        domain=[('type', '=', 'sale')],
        default=_get_journal,
        states={
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        required=True)
    invoice_ids = fields.One2many(
        comodel_name='account.invoice',
        inverse_name='fee_generator_id',
        string='Generated Invoices',
        states={
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)]},
        copy=False)
    residual_untaxed = fields.Float(
        string='Amount Residual',
        compute='compute_residual_untaxed',
        store=True,
        digits_compute=dp.get_precision('Account'))
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda s: s.env.user.company_id,
        required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('ended', 'Ended'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
        track_visibility='onchange')

    @api.one
    @api.depends('discount', 'total_untaxed')
    def compute_amount_discount(self):
        discount = (self.discount / 100)
        self.amount_discount = self.total_untaxed * discount

    @api.one
    @api.depends('invoice_ids', 'invoice_ids.state', 'fee_number')
    def compute_fee_number_remaining(self):
        inv_fees = len(
            [i.id for i in self.invoice_ids if i.state != 'cancel'])
        self.fee_number_remaining = self.fee_number - inv_fees

    @api.one
    @api.depends('total_untaxed', 'residual_untaxed', 'fee_number_remaining')
    def compute_fee_amount_untaxed(self):
        if not self.total_untaxed:
            return
        if not self.residual_untaxed:
            return
        if self.fee_number_remaining < 2:
            self.fee_amount_untaxed = self.residual_untaxed
            return
        amount = self.total_untaxed / self.fee_number
        self.fee_amount_untaxed = amount

    @api.one
    @api.depends('next_date', 'fee_number_remaining', 'recurring_interval',
                 'recurring_rule_type')
    def compute_end_date(self):
        if not self.next_date and not self.start_date:
            return
        end_date = self.next_date or self.start_date
        if self.fee_number_remaining:
            for fee in range(self.fee_number_remaining - 1):
                end_date = self._get_new_date(end_date)
        self.end_date = end_date

    @api.one
    @api.depends(
        'invoice_ids.state', 'invoice_ids.amount_untaxed', 'discount',
        'total_untaxed')
    def compute_residual_untaxed(self):
        discount = (1 - self.discount / 100)
        if not self.invoice_ids:
            self.residual_untaxed = self.total_untaxed * discount
            return
        residual_untaxed = self.total_untaxed * discount
        for invoice in self.invoice_ids:
            if invoice.state != 'cancel':
                residual_untaxed -= invoice.amount_untaxed
        self.residual_untaxed = residual_untaxed

    @api.onchange('fee_product_id')
    def onchange_fee_product_id(self):
        if not self.fee_product_id:
            return
        self.description = self.fee_product_id.name

    @api.onchange('model_name')
    def onchange_model_name(self):
        if not self.model_name:
            return
        self.model_id = self.env['ir.model'].search(
            [('model', '=', self.model_name)])

    @api.onchange('start_date')
    def onchange_start_date(self):
        if not self.start_date:
            return
        if not self.invoice_ids:
            self.next_date = self.start_date

    @api.one
    def to_draft(self):
        if self.state != 'cancelled':
            return
        self.state = 'draft'

    @api.one
    def to_active(self):
        if not self.state == 'draft':
            return
        if self.discount < 0 or self.discount > 100:
            raise exceptions.Warning(_('Discount must be between 0 and 100.'))
        if not self.fee_number or self.fee_number < 0:
            raise exceptions.Warning(_('Fees number must be greater than 0.'))
        self.state = 'active'

    @api.one
    def to_ended(self):
        if self.state != 'active':
            return
        self.state = 'ended'

    @api.one
    def to_cancelled(self):
        if self.state not in ['draft', 'active']:
            return
        self.state = 'cancelled'

    @api.model
    def _get_new_date(self, next_date):
        if not next_date:
            return
        next_date = datetime.datetime.strptime(next_date, '%Y-%m-%d')
        interval = self.recurring_interval
        if self.recurring_rule_type == 'daily':
            new_date = next_date + relativedelta(days=+interval)
        elif self.recurring_rule_type == 'weekly':
            new_date = next_date + relativedelta(weeks=+interval)
        elif self.recurring_rule_type == 'monthly':
            new_date = next_date + relativedelta(months=+interval)
        else:
            new_date = next_date + relativedelta(years=+interval)
        return new_date.strftime('%Y-%m-%d')

    @api.model
    def _get_recurring_reference(self):
        if not self.reference:
            return ''
        next_date = datetime.datetime.strptime(self.next_date, '%Y-%m-%d')
        reference = self.reference.replace(
            '#MONTH_INT#', next_date.strftime('%m'))
        reference = reference.replace(
            '#MONTH_STR#', str(next_date.strftime('%B')).capitalize())
        reference = reference.replace(
            '#YEAR_INT#', next_date.strftime('%Y'))
        return str(reference)

    @api.model
    def _prepare_invoice_line_vals(self):
        res = self.env['account.invoice.line'].product_id_change(
            product=self.fee_product_id.id,
            uom_id=self.fee_product_id.uom_id.id, qty=1, name='',
            type='out_invoice', partner_id=self.partner_id.id,
            fposition_id=False, price_unit=None,
            currency_id=False, company_id=None)
        values = res['value']
        values['product_id'] = self.fee_product_id.id
        values['name'] = self.description
        values['origin'] = self.name
        if self.fee_number_remaining < 2:
            values['price_unit'] = self.fee_amount_untaxed / (
                1 - self.discount / 100)
        else:
            values['price_unit'] = self.fee_amount_untaxed
        values['discount'] = self.discount
        if values.get('invoice_line_tax_id'):
            taxes = values['invoice_line_tax_id']
            values['invoice_line_tax_id'] = [(6, 0, taxes)]
        return values

    @api.model
    def _prepare_invoice_vals(self):
        origins = self.model_id and self.env[self.model_id.model].search(
            [('id', '=', self.res_id)]) or None
        date_inv = self.next_date or time.strftime('%Y-%m-%d')
        res = self.env['account.invoice'].onchange_partner_id(
            type='out_invoice', partner_id=self.partner_id.id,
            date_invoice=date_inv, payment_term=False, partner_bank_id=False,
            company_id=False)
        values = res['value']
        line_vals = self._prepare_invoice_line_vals()
        ref = self._get_recurring_reference()
        values['origin'] = origins and origins[0].name or None
        values['type'] = 'out_invoice'
        values['name'] = ref
        values['reference'] = ref
        values['partner_id'] = self.partner_id.id
        values['journal_id'] = self.journal_id.id
        values['date_invoice'] = self.next_date or time.strftime('%Y-%m-%d')
        values['fee_generator_id'] = self.id
        values['invoice_line'] = [(0, 0, line_vals)]
        return values

    @api.multi
    def button_generate_next_invoice(self):
        for fee_gen in self:
            inv_vals = fee_gen._prepare_invoice_vals()
            created_inv = fee_gen.env['account.invoice'].create(inv_vals)
            created_inv.button_reset_taxes()
            current_date = time.strftime('%Y-%m-%d')
            new_date = fee_gen._get_new_date(fee_gen.next_date or current_date)
            if fee_gen.fee_number_remaining > 0:
                fee_gen.next_date = new_date

    @api.multi
    def cron_generate_next_invoice(self):
        current_date = time.strftime('%Y-%m-%d')
        domain = [
            ('state', '=', 'active'),
            ('residual_untaxed', '>', 0),
            ('next_date', '<=', current_date)]
        fee_generators = self.env['fee.generator'].search(domain)
        for fee_generator in fee_generators:
            fee_generator.button_generate_next_invoice()
