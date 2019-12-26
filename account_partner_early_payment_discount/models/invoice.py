###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    early_discount = fields.Float(
        string='% Early Payment Discount',
        states={'draft': [('readonly', False)]},
        readonly=True,
        help='Early Payment Discount in %.')

    @api.model
    def create(self, vals):
        if not vals.get('early_discount'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            vals['early_discount'] = partner.early_discount
        return super(AccountInvoice, self).create(vals)

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.partner_id:
            self.early_discount = self.partner_id.early_discount
        return res

    @api.multi
    def action_move_create(self):
        if not self.early_discount:
            super().action_move_create()
            return True
        if not self.company_id.discount_product_id:
            raise UserError(
                _('Please select product for early discount in company '
                  'config Product Early Discount no set'))
        product_id = self.company_id.discount_product_id
        is_early_discount = self.mapped('invoice_line_ids').filtered(
            lambda l: l.product_id == product_id)
        if is_early_discount:
            is_early_discount.unlink()
        self.compute_taxes()
        early_discount = (float(self.early_discount) or 0.0) / 100
        early_amount = float(self.amount_untaxed) * early_discount
        if self.type in ('out_invoice', 'out_refund'):
            account = (
                product_id.property_account_income_id or
                product_id.categ_id.property_account_income_categ_id)
            if not account:
                raise UserError(_(
                    'Product must be assigned an income account.'))
            taxes = product_id.taxes_id or account.tax_ids
        else:
            account = (
                product_id.property_account_expense_id or
                product_id.categ_id.property_account_expense_categ_id)
            if not account:
                raise UserError(_(
                    'Product must be assigned an expense account.'))
            taxes = product_id.supplier_taxes_id or account.tax_ids
        taxes = self.fiscal_position_id.map_tax(
            taxes, partner=self._onchange_partner_id)
        values = {
            'invoice_id': self.id,
            'product_id': product_id.id,
            'uom_id': product_id.uom_id.id or product_id.uom_id.id,
            'price_unit': early_amount * -1,
            'account_id': account.id,
            'name': product_id.name,
            'invoice_line_tax_ids': [(6, 0, taxes.ids)],
            'quantity': 1
        }
        self.env['account.invoice.line'].create(values)
        self.compute_taxes()
        super().action_move_create()
        return True
