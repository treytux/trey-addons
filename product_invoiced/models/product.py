# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields, _
import logging
_log = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sum_price = fields.Float(
        compute='_compute_product_invoiced',
        string='Sum price',
        store=False)
    sum_price_cur_year = fields.Float(
        compute='_compute_product_invoiced',
        string='Sum price (current year)',
        store=False)

    @api.multi
    def action_view_invoices(self):
        form_view = self.env.ref('account.view_invoice_line_tree')
        tree_view = self.env.ref('product_invoiced.tree_account_invoice_line')
        search_view = self.env.ref(
            'product_invoiced.search_account_invoice_line')
        return {
            'name': _('Lines invoiced'),
            'domain': self._get_product_invoiced_domain(),
            'res_model': 'account.invoice.line',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form'}

    @api.multi
    def action_view_invoices_cur_year(self):
        form_view = self.env.ref('account.view_invoice_line_tree')
        tree_view = self.env.ref('product_invoiced.tree_account_invoice_line')
        search_view = self.env.ref(
            'product_invoiced.search_account_invoice_line')
        return {
            'name': _('Lines invoiced'),
            'domain': (
                self._get_product_invoiced_domain() +
                self._get_domain_current_year()),
            'res_model': 'account.invoice.line',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form'}

    @api.multi
    def _get_domain_current_year(self):
        date_from = fields.Date.to_string(
            fields.Date.from_string(
                fields.Date.today()).replace(month=1, day=1))
        date_to = fields.Date.to_string(
            fields.Date.from_string(
                fields.Date.today()).replace(month=12, day=31))
        return [
            ('date_invoice', '>=', date_from),
            ('date_invoice', '<=', date_to)]

    @api.multi
    def _get_product_inv_domain(self):
        return [
            ('product_id', 'in', self.product_variant_ids.ids),
            ('invoice_id.type', 'in', ['out_invoice', 'in_invoice']),
            ('invoice_id.state', '=', 'paid')]

    @api.multi
    def _get_product_inv_ref_domain(self):
        return [
            ('product_id', 'in', self.product_variant_ids.ids),
            ('invoice_id.type', 'in', ['out_refund', 'in_refund']),
            ('invoice_id.state', '=', 'paid')]

    @api.multi
    def _get_product_invoiced_domain(self, date_from=None, date_to=None):
        domain = [
            ('product_id', 'in', self.product_variant_ids.ids),
            ('invoice_id.type', 'in', [
                'out_invoice', 'in_invoice', 'out_refund', 'in_refund']),
            ('invoice_id.state', '=', 'paid')]
        return domain

    @api.one
    def _compute_product_invoiced(self):
        '''Products in invoice lines whose invoice is in 'paid' state.'''
        invoice_lines_obj = self.env['account.invoice.line']

        # Witout filter in date
        inv_lines = invoice_lines_obj.search(self._get_product_inv_domain())
        amount_inv = sum([l.price_subtotal for l in inv_lines])
        inv_ref_lines = invoice_lines_obj.search(
            self._get_product_inv_ref_domain())
        amount_inv_ref = sum([l.price_subtotal for l in inv_ref_lines])
        self.sum_price = round(amount_inv - amount_inv_ref, 2)

        # For current year
        inv_lines_cur = invoice_lines_obj.search(
            self._get_product_inv_domain() +
            self._get_domain_current_year())
        amount_inv_cur = sum([l.price_subtotal for l in inv_lines_cur])
        inv_ref_lines_cur = invoice_lines_obj.search(
            self._get_product_inv_ref_domain() +
            self._get_domain_current_year())
        amount_inv_cur_ref = sum([l.price_subtotal for l in inv_ref_lines_cur])
        self.sum_price_cur_year = round(
            amount_inv_cur - amount_inv_cur_ref, 2)
