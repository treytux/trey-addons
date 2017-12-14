# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, exceptions, api, _


class InvoiceApplyPricelist(models.TransientModel):
    _name = 'wizard.invoice_apply_pricelist'

    name = fields.Char(
        string='Name')

    @api.multi
    def action_accept(self):
        form_view = self.env.ref('account.invoice_form')
        invoice_ids = self.env.context['active_ids']
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            if invoice.state != 'draft':
                raise exceptions.Warning(_(
                    'The partner pricelist can only be applied when invoices '
                    'are in \'Draft\' state.'))
            if not invoice.partner_id:
                raise exceptions.Warning(_('You must assign a partner!'))
            if invoice.type in ('out_invoice', 'out_refund'):
                pricelist = invoice.partner_id.property_product_pricelist
            else:
                pricelist = (
                    invoice.partner_id.property_product_pricelist_purchase)
                form_view = self.env.ref('account.invoice_supplier_form')
            if not pricelist.exists():
                raise exceptions.Warning(_(
                    'The partner \'%s\' does have not pricelist.\n'
                    'You must assign it.') % (invoice.partner_id.name))
            for line in invoice.invoice_line:
                if line.product_id.exists():
                    price = pricelist.price_get(
                        line.product_id.id, line.quantity, invoice.partner_id)[
                            pricelist.id]
                    line.write({'price_unit': price})
            invoice.button_reset_taxes()
        tree_view = self.env.ref('account.invoice_tree')
        search_view = self.env.ref('account.view_account_invoice_filter')
        return {
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'account.invoice',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'search_view_id': search_view.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', invoice_ids)],
            'context': self.env.context}
