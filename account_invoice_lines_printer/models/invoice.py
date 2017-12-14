# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api, fields, exceptions, _
from openerp.tools import float_compare
from openerp.addons import decimal_precision as dp
import logging
_log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    print_line = fields.Boolean(
        string='Print lines?')
    print_line_untaxed = fields.Float(
        string='Untaxes',
        compute='_compute_diff_total')
    print_line_tax = fields.Float(
        string='Tax',
        compute='_compute_diff_total')
    print_line_total = fields.Float(
        string='Total',
        compute='_compute_diff_total')
    print_line_ids = fields.One2many(
        comodel_name='account.invoice.print_line',
        inverse_name='invoice_id',
        string='Print Line')

    @api.one
    @api.depends('print_line_ids')
    def _compute_diff_total(self):
        untaxes = tax = total = 0
        for line in self.print_line_ids:
            untaxes += line.untaxes
            tax += (line.subtotal - line.untaxes)
            total += line.subtotal
        self.print_line_untaxed = untaxes
        self.print_line_tax = tax
        self.print_line_total = total

    @api.one
    def button_diff_update(self):
        self._compute_diff_total()

    @api.one
    def action_print_line_copy(self):
        for line in self.print_line_ids:
            line.unlink()
        for line in self.invoice_line:
            self.env['account.invoice.print_line'].create({
                'invoice_id': line.invoice_id.id,
                'name': line.name,
                'qty': line.quantity,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'tax_ids': [(6, 0, line.invoice_line_tax_id.ids)]})

    @api.one
    def check_print_lines(self):
        def msg(field):
            return _(
                'You can\'t activate print lines. The original %s and the %s '
                'of lines to print has to be the same amounts') % (
                    field, field)
        if float_compare(
                self.amount_total, self.print_line_total, precision_digits=2):
            raise exceptions.Warning(msg('total'))
        if float_compare(
                self.amount_tax, self.print_line_tax, precision_digits=2):
            raise exceptions.Warning(msg('tax'))
        if float_compare(
                self.amount_untaxed, self.print_line_untaxed,
                precision_digits=2):
            raise exceptions.Warning(msg('untaxed'))

    @api.onchange('print_line')
    def onchange_print_line(self):
        if self.print_line:
            self.check_print_lines()

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if res.print_line:
            res.check_print_lines()
        return res

    @api.multi
    def write(self, vals):
        if 'print_line' in vals and vals['print_line']:
            for rec in self:
                rec.check_print_lines()
        return super(AccountInvoice, self).write(vals)


class AccountInvoicePrintLines(models.Model):
    _name = 'account.invoice.print_line'
    _description = 'Invoice Print Lines'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    name = fields.Char(string='Description')
    qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'))
    price_unit = fields.Float(
        string='Price Unit',
        digits=dp.get_precision('Product Price'))
    discount = fields.Float(string='Dto (%)')
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='account_invoice_print_line_tax',
        column1='line_id',
        column2='tax_id')
    untaxes = fields.Float(
        string='Untaxes',
        compute='_compute_subtotal')
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal')

    @api.one
    @api.depends('qty', 'price_unit', 'discount')
    def _compute_subtotal(self):
        self.untaxes = self.qty * self.price_unit
        if self.discount:
            self.untaxes = (self.untaxes *
                            (1.0 - (self.discount or 0.0) / 100.0))
        taxs = self.tax_ids.compute_all(
            (self.price_unit * (1.0 - (self.discount or 0.0) / 100.0)),
            self.qty, None, self.invoice_id.partner_id)
        self.subtotal = taxs['total_included']
