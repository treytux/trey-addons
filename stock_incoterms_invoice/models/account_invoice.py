# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class AccountInvoiceIncoterm(models.Model):
    _name = 'account.invoice.incoterm'
    _description = "Account Invoice Incoterms"

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string="Invoice",
        required=False,
        ondelete='cascade',
        index=True)
    concept_id = fields.Many2one(
        comodel_name='stock.incoterms.concept',
        string="Incoterm Concept",
        required=False)
    price = fields.Float(
        string='Amount',
        digits=dp.get_precision('Account'))
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='invoice_id.company_id',
        store=True,
        readonly=True)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    incoterms_ids = fields.One2many(
        comodel_name='account.invoice.incoterm',
        inverse_name='invoice_id',
        string="Incoterms Concepts",
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]})

    @api.onchange('incoterm')
    def check_incoterm(self):
        '''Assign the concepts associated with the incoterm assigned in the
        invoice.'''
        concept_obj = self.env['stock.incoterms.concept']
        if self.state == 'draft' and self.incoterm:
            # Reset old incoterms concept values
            self.incoterms_ids = None
            concept_ids = concept_obj.search([
                ('incoterm_id', '=', self.incoterm.id)])
            if concept_ids:
                values = []
                for concept in concept_ids:
                    values.append({
                        'concept_id': concept.id,
                        'price': concept.price,
                        'invoice_id': self.id,
                    })
                self.incoterms_ids = values

    @api.multi
    def action_move_create(self):
        if not self.incoterms_ids:
            super(AccountInvoice, self).action_move_create()
        for incoterm in self.incoterms_ids:
            if incoterm.concept_id.in_invoice:
                product_id = incoterm.concept_id.product_id
                fpos = self.env['account.fiscal.position'].browse(
                    self.fiscal_position.id)
                if self.type in ('out_invoice', 'out_refund'):
                    account = (
                        product_id.property_account_income or
                        product_id.categ_id.property_account_income_categ)
                    taxes = product_id.taxes_id or account.tax_ids
                else:
                    account = (
                        product_id.property_account_expense or
                        product_id.categ_id.property_account_expense_categ)
                    taxes = product_id.supplier_taxes_id or account.tax_ids
                taxes = fpos.map_tax(taxes)
                values = {
                    'invoice_id': self.id,
                    'product_id': product_id.id,
                    'uos_id': product_id.uos_id.id or product_id.uom_id.id,
                    'price_unit': incoterm.price,
                    'account_id': account.id,
                    'name': product_id.name,
                    'invoice_line_tax_id': [(6, 0, taxes.ids)],
                    'quantity': 1,
                    'company_id': self.company_id.id,
                }
                self.env['account.invoice.line'].create(values)
            super(AccountInvoice, self).button_reset_taxes()
            super(AccountInvoice, self).action_move_create()
        return True
