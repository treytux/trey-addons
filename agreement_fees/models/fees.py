# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import api, models, fields, exceptions, _
import logging

_log = logging.getLogger(__name__)


class AgreementFees(models.Model):
    _name = 'agreement.fees'
    _description = 'Agreement by fees'
    _inherit = ['mail.thread']
    _order = 'name desc'

    # Sistema de logging automatico
    _track = {
        'state': {
            'agreement_fees.mt_new': (
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'draft'),
            'agreement_fees.mt_financed': (
                lambda self, cr, uid, obj, ctx=None:
                obj['state'] == 'financed'),
            'agreement_fees.mt_cancel': (
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'cancel'),
        },
    }

    @api.one
    @api.depends('fees_number', 'fees_amount', 'line_ids', 'tax_ids',
                 'invoice_ids')
    def _compute(self):
        if self.line_ids:
            self.amount_total = sum([l.amount for l in self.line_ids])
            self.amount_taxes = sum([l.amount_tax for l in self.line_ids])
        elif self.amount_base:
            tax_factor = (
                self.compute_taxes(self.amount_base) / self.amount_base)
            self.amount_total = (
                (self.fees_amount * self.fees_number) / (1 + tax_factor))
            self.amount_taxes = self.compute_taxes(self.amount_total)

        self.amount_profit = (self.amount_total - self.amount_base)
        self.fees_amount_min = (
            self.amount_base +
            self.compute_taxes(self.amount_base)) / self.fees_number
        self.amount_invoiced = sum([
            i.amount_untaxed
            for i in self.invoice_ids
            if i.state in ['proforma', 'proforma2', 'paid']])
        self.amount_invoiced_taxes = sum([
            i.amount_tax
            for i in self.invoice_ids
            if i.state in ['proforma', 'proforma2', 'paid']])
        self.amount_invoiced_total = (
            self.amount_invoiced + self.amount_invoiced_taxes)
        self.amount_pending = self.amount_total - self.amount_invoiced
        self.amount_pending_taxes = (
            self.amount_taxes - self.amount_invoiced_taxes)
        self.amount_pending_total = (
            self.amount_pending + self.amount_pending_taxes)

        self.amount_pending_fees = sum([1 for l in self.line_ids
                                        if not l.invoice_id])
        lines_total = sum([l.amount_total for l in self.line_ids])
        # fees_total = self.fees_number * self.fees_amount
        self.amount_deviation = round(self.total - lines_total, 2)

    @api.one
    @api.depends('line_ids')
    def _compute_date_end(self):
        line = self.line_ids.search(
            [('fees_id', '=', self.id)],
            order='date desc', limit=1)
        self.date_end = line and line[0].date or fields.Date.today()

    total = fields.Float(
        string='Total (for desviation calc)',
        states={'draft': [('readonly', False)]})
    amount_base = fields.Float(
        string='Amount without tax',
        required=True,
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]})
    amount_total = fields.Float(
        string='Total without tax',
        compute=_compute,
        track_visibility='onchange')
    amount_taxes = fields.Float(
        string='Taxes',
        compute=_compute)
    amount_profit = fields.Float(
        string='Profit',
        compute=_compute)
    amount_invoiced = fields.Float(
        string='Invoiced',
        compute=_compute)
    amount_invoiced_taxes = fields.Float(
        string='Invoiced taxes',
        compute=_compute)
    amount_invoiced_total = fields.Float(
        string='Invoiced total',
        compute=_compute)
    amount_pending = fields.Float(
        string='Pending',
        compute=_compute)
    amount_pending_taxes = fields.Float(
        string='Pending taxes',
        compute=_compute)
    amount_pending_total = fields.Float(
        string='Pending total',
        compute=_compute)
    amount_pending_fees = fields.Integer(
        string='Pending fees',
        compute=_compute)
    amount_deviation = fields.Float(
        string='Desviation',
        compute=_compute)
    fees_number = fields.Integer(
        string='Number of fees',
        required=True,
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=1)
    fees_amount = fields.Float(
        string='Amount fee',
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]})
    fees_amount_min = fields.Float(
        string='Amount min',
        compute=_compute,
        readonly=True)
    name = fields.Char(
        string='Name',
        required=True,
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        domain=[('type', '=', 'sale')],
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('standby', 'Stand by'),
            ('cancel', 'Canceled'),
        ],
        string='State',
        default='draft',
        readonly=True,
        track_visibility='onchange')
    date_init = fields.Date(
        string='Start',
        required=True,
        track_visibility='onchange',
        default=fields.Date.context_today,
        readonly=True,
        states={'draft': [('readonly', False)]})
    date_sign = fields.Date(
        string='Sign',
        readonly=True,
        states={'draft': [('readonly', False)]})
    date_end = fields.Date(
        string='End',
        readonly=True,
        compute=_compute_date_end)
    date_next_invoice = fields.Date(
        string='Next invoice',
        default=fields.Date.today,
        track_visibility='onchange')
    period_id = fields.Many2one(
        comodel_name='period',
        string='Period',
        required=True,
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]})
    line_ids = fields.One2many(
        comodel_name='agreement.fees.amortization_line',
        inverse_name='fees_id',
        ondelete='cascade',
        string='Amortization lines',
        track_visibility='onchange')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Partner',
        track_visibility='onchange',
        readonly=True,
        domain=[('customer', '=', True)],
        states={'draft': [('readonly', False)]})
    partner_bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        domain="[('partner_id', '=', partner_id)]",
        string='Bank',
        track_visibility='onchange')
    invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        relation='agreement_fees_invoice_rel',
        column1='fees_id',
        column2='invoice_id',
        readonly=True)
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='agreement_fees_tax_rel',
        column1='fees_id',
        column2='tax_id',
        domain=[('type_tax_use', '=', 'sale')],
        readonly=True,
        states={'draft': [('readonly', False)]})
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Financial Product',
        required=True,
        help="Product for invoices generated by payment financing.",
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]})
    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode',
        string='Payment mode',
        track_visibility='onchange')
    description_product = fields.Char(
        string='Description',
        help="Description for invoices generated by payment financing."
             "If omitted, the description of the product is used.",
        track_visibility='onchange')
    payment_meet = fields.Selection(
        selection=[
            ('pending', 'Pendiente de negociar'),
            ('unique', 'Pago único'),
            ('2_3_fees', 'Pago en 2/3 cuotas'),
            ('owner', 'Financiación propia'),
            ('external', 'Financiación externa')],
        default='pending',
        string='Compromiso de pago',
        track_visibility='onchange')
    cancel_issue = fields.Selection(
        selection=[
            ('null', 'Anulado'),
            ('reclaimable', 'Fallido reclamable'),
            ('reclaimable', 'Fallido NO reclamable')],
        string='Contrato cancelado',
        track_visibility='onchange')
    notes = fields.Text(
        string='Notes')

    @api.constrains('amount_base')
    @api.one
    def _check_amount_base(self):
        if self.amount_base <= 0:
            raise exceptions.ValidationError(
                _('Amount must be a value greater than zero.'))

    @api.constrains('fees_number')
    @api.one
    def _check_fees_number(self):
        if self.fees_number < 0:
            raise exceptions.ValidationError(
                _('Fees number must be a value greater than zero.'))

    @api.one
    def to_draft(self):
        self.state = 'draft'

    @api.one
    def to_cancel(self):
        self.state = 'cancel'

    @api.one
    def to_standby(self):
        self.state = 'standby'

    @api.one
    def to_confirmed(self):
        self.state = 'confirmed'
        if not self.line_ids:
            self.compute_amortization()

        # Actualizar la fecha final de la financiacion: coincide con la fecha
        # de la ultima linea de amortizacion
        lines = self.line_ids.search(
            [('invoice_id', '=', False),
             ('fees_id', '=', self.id)],
            order='date desc', limit=1)
        if lines:
            self.date_end = lines[0].date

        # Por defecto la fecha de la proxima factura sera hoy (para la primera)
        self.date_next_invoice = self.date_init

    @api.one
    def to_done(self):
        self.state = 'done'

    @api.one
    def compute_all(self):
        self._compute()

    @api.multi
    def compute_taxes(self, amount):
        taxes = 0
        for r in self:
            for tax in r.tax_ids:
                taxes += tax.compute_all(
                    amount, 1, r.product_id,
                    r.partner_id)['total_included'] - amount
        return taxes

    @api.one
    def compute_amortization(self):
        # Eliminar las lineas no facturadas
        for line in self.line_ids:
            if not line.invoice_id.exists():
                line.unlink()

        date = self.date_next_invoice

        fees_profit = self.fees_number * self.fees_amount

        if fees_profit >= self.amount_total + self.amount_taxes:
            financing_amount = fees_profit - self.amount_invoiced_total
        else:
            financing_amount = abs(
                self.amount_profit + self.compute_taxes(self.amount_profit))

        # tax_factor = (
        #      self.compute_taxes(self.fees_amount) / self.fees_amount)
        # amount = round(self.fees_amount / (1 + tax_factor), 2)
        # amount_tax = round(amount * tax_factor, 2)
        # quote = amount + amount_tax
        quote = self.fees_amount
        while financing_amount != 0:
            line = {
                'fees_id': self.id,
                'date': date,
                'amount_total': 0
            }
            if financing_amount > quote:
                line['amount_total'] = quote
                financing_amount -= quote
            else:
                line['amount_total'] = financing_amount
                financing_amount = 0
            self.line_ids.create(line)
            date = fields.Datetime.to_string(self.period_id.next(date))

    @api.one
    def generate_invoice(self, amount=None, manual_invoice=False,
                         date_invoice=None, tax_ids=[], fee_line_id=None):
        # if self.amount_pending_total == 0:
        #     raise exceptions.Warning(
        #         _('The amount pending is zero, it is not create invoice.'))

        if not amount:
            if fee_line_id is None:
                line = self.line_ids.search(
                    [('invoice_id', '=', False),
                     ('fees_id', '=', self.id)],
                    order='date asc', limit=1)
            else:
                line = self.line_ids.browse(fee_line_id)
                date_invoice = line.date
                tax_ids = [t.id for t in line.fees_id.tax_ids]
                manual_invoice = True
            amount = line.amount

        if not date_invoice:
            date_invoice = fields.Date.today()

        invoice = self.env['account.invoice'].create({
            'name': self.name or '',
            'date_invoice': date_invoice,
            'origin': self.name,
            'type': 'out_invoice',
            'reference': self.name,
            'account_id': self.partner_id.property_account_receivable.id,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'payment_mode_id': self.payment_mode_id.id,
            'fiscal_position': self.partner_id.property_account_position.id,
            'currency_id': self.partner_id.company_id.currency_id.id,
        })

        # El amount biene con los impuestos incluidos, quitarselos
        # tax_factor = (self.compute_taxes(amount) / amount)
        # amount = amount / (1 + tax_factor)

        invoice.invoice_line.create({
            'invoice_id': invoice.id,
            'name': (
                self.description_product and
                self.description_product or self.product_id.name_template),
            'origin': self.name,
            'product_id': self.product_id and self.product_id.id or None,
            'account_id': self.product_id.property_account_income.id,
            'invoice_line_tax_id': [(6, 0, tax_ids)],
            'price_unit': amount,
            'quantity': 1.0,
        })
        invoice.button_reset_taxes()
        if fee_line_id:
            if invoice.tax_line:
                invoice.tax_line[0].amount = line.amount_tax
            invoice.amount_tax = line.amount_tax
            line.write({
                'fees_id': self.id,
                # 'amount_total': invoice.amount_total,
                'date': date_invoice,
                'invoice_id': invoice.id
            })
        else:
            self.line_ids.create({
                'fees_id': self.id,
                'amount_total': invoice.amount_total,
                'date': date_invoice,
                'invoice_id': invoice.id
            })

        date_invoice = fields.Date.from_string(invoice.date_invoice)
        date_next_invoice = fields.Date.from_string(self.date_next_invoice)
        if date_invoice > date_next_invoice:
            self.write({
                'invoice_ids': [(4, invoice.id)],
                'date_next_invoice':
                self.period_id.next(invoice.date_invoice)})
        else:
            self.write({'invoice_ids': [(4, invoice.id)]})

        self.message_post(
            _('''%s invoice has created.<br/>
                 <p>&nbsp; &nbsp; • <b>Date</b><span>: %s</span><br/>
                 &nbsp; &nbsp; • <b>Total</b><span>: %s</span></p>
              ''' % (manual_invoice and 'Manual' or 'Automatic',
                     invoice.date_invoice,
                     invoice.amount_total))
        )

        return invoice

    @api.model
    def generate_schelude_invoices(self):
        line_obj = self.env['agreement.fees.amortization_line']
        lines = line_obj.search([
            ('invoice_id', '=', False),
            ('date', '<=', fields.Date.today()),
            ('fees_id.state', '=', 'confirmed')])
        for line in lines:
            invoices = line.fees_id.generate_invoice()

            for invoice in invoices:
                line.fees_id.message_post(
                    _('''A automatic invoice has created.<br/>
                         <p>&nbsp; &nbsp; • <b>Date</b><span>: %s</span><br/>
                         &nbsp; &nbsp; • <b>Total</b><span>: %s</span></p>
                      ''' % (invoice.date_invoice, invoice.amount_total))
                )


class AgreementFeesAmortizationLine(models.Model):
    _name = 'agreement.fees.amortization_line'
    _description = 'Agreement fees amortizacion line'
    _order = 'date asc'

    @api.one
    @api.depends('amount_total')
    def _compute_total(self):
        if self.invoice_id:
            self.amount = self.invoice_id.amount_untaxed
            self.amount_tax = self.invoice_id.amount_tax
            self.amount_total = self.amount + self.amount_tax
        elif self.amount_total:
            tax_factor = (
                self.fees_id.compute_taxes(self.amount_total) /
                self.amount_total)
            tax_factor = round(tax_factor, 2)
            if tax_factor > 0:
                self.amount = round(self.amount_total / (1 + tax_factor), 2)
            else:
                self.amount = round(self.amount_total, 2)
            self.amount_tax = self.amount_total - self.amount

    name = fields.Char(
        string='Name',
        translate=True)
    fees_id = fields.Many2one(
        comodel_name='agreement.fees',
        string='Payment Financing',
        required=True)
    fees_state = fields.Selection(
        related='fees_id.state',
        string='State',
        readonly=True)
    date = fields.Date('Date')
    amount = fields.Float(
        string='Untaxed',
        compute=_compute_total)
    amount_tax = fields.Float(
        string='Taxes',
        compute=_compute_total)
    amount_total = fields.Float(string='Total')
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
        readonly=True)
    invoice_state = fields.Selection(
        related='invoice_id.state',
        string='Invoice State',
        readonly=True)

    @api.one
    def create_invoice(self):
        invoices = self.fees_id.generate_invoice(manual_invoice=True,
                                                 fee_line_id=self.id)
        self.invoice_id = invoices and invoices[0] or None
        return True

    @api.multi
    def goto_invoice(self):
        self.ensure_one()
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'res_id': self.invoice_id.id,
            'view_id': self.env.ref('account.invoice_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': [('type', '=', 'out_invoice')],
            'context': {'default_type': 'out_invoice',
                        'type': 'out_invoice',
                        'journal_type': 'sale'}
        }

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.invoice_id:
                raise exceptions.Warning(
                    _('You can not delete the line'),
                    _('The line is assigned an invoice, delete the invoice '
                      'before deleting the line.'))
        super(AgreementFeesAmortizationLine, self).unlink()
