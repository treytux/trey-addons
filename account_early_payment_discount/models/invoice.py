# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    early_discount = fields.Float(
        string='% Early Payment Discount',
        help='Early Payment Discount in %.')

    @api.model
    def create(self, vals):
        '''Inherit the function to check if the 'early_discount' field is
        empty. If so, it is assigned which has defined in the partner.'''
        if ('early_discount' not in vals or (
                'early_discount' in vals and vals['early_discount'] == 0)):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            vals['early_discount'] = partner.early_discount
        return super(AccountInvoice, self).create(vals)

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False,
                            company_id=False):
        result = super(AccountInvoice, self).onchange_partner_id(
            type=type, partner_id=partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        if partner_id:
            p = self.env['res.partner'].browse(partner_id)
            result['value']['early_discount'] = p.early_discount

        return result

    @api.multi
    def action_move_create(self):
        if self.early_discount != 0:
            if self.company_id.discount_product_id:
                product_id = self.company_id.discount_product_id
                fpos = self.env['account.fiscal.position'].browse(
                    self.fiscal_position.id)
                early_discount = (float(self.early_discount) or 0.0) / 100
                early_amount = float(self.amount_untaxed) * early_discount
                if self.type in ('out_invoice', 'out_refund'):
                    account = (
                        product_id.property_account_income or
                        product_id.categ_id.property_account_income_categ)
                    if not account.exists():
                        raise exceptions.Warning(_(
                            'Product must be assigned an income account.'))
                    taxes = product_id.taxes_id or account.tax_ids
                else:
                    account = (
                        product_id.property_account_expense or
                        product_id.categ_id.property_account_expense_categ)
                    if not account.exists():
                        raise exceptions.Warning(_(
                            'Product must be assigned an expense account.'))
                    taxes = product_id.supplier_taxes_id or account.tax_ids
                taxes = fpos.map_tax(taxes)
                values = {
                    'invoice_id': self.id,
                    'product_id': product_id.id,
                    'uos_id': product_id.uos_id.id or product_id.uom_id.id,
                    'price_unit': early_amount * -1,
                    'account_id': account.id,
                    'name': product_id.name,
                    'invoice_line_tax_id': [(6, 0, taxes.ids)],
                    'qty': 1,
                }
                self.env['account.invoice.line'].create(values)
                super(AccountInvoice, self).button_reset_taxes()
                super(AccountInvoice, self).action_move_create()
                return True
            else:
                raise exceptions.Warning(
                    _("Please select product for early discount in company "
                      "config"
                      "Produc Early Discount no set"))
        else:
            super(AccountInvoice, self).action_move_create()
