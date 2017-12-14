# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sup_inv_lines_count = fields.Float(
        string='Supplier Lines',
        compute='_supplier_lines_count')
    cus_inv_lines_count = fields.Float(
        string='Customer Lines',
        compute='_customer_lines_count')

    @api.multi
    def _supplier_lines_count(self):
        for prod in self:
            prod.sup_inv_lines_count = self.env[
                'account.invoice.line'].search_count(
                    prod._get_product_supplier_domain())

    @api.multi
    def _customer_lines_count(self):
        for prod in self:
            prod.cus_inv_lines_count = self.env[
                'account.invoice.line'].search_count(
                    prod._get_product_customer_domain())

    @api.multi
    def _get_product_supplier_domain(self):
        return [
            ('product_id', 'in', self.ids),
            ('invoice_id.type', 'in', ['in_invoice', 'in_refund']),
            ('invoice_id.state', '!=', 'cancel')]

    @api.multi
    def _get_product_customer_domain(self):
        return [
            ('product_id', 'in', self.ids),
            ('invoice_id.type', 'in', ['out_invoice', 'out_refund']),
            ('invoice_id.state', '!=', 'cancel')]

    @api.multi
    def action_view_supplier_invoice_lines(self):
        tree_view = self.env.ref(
            'product_invoiced_line.product_account_invoice_line_tree')
        search_view = self.env.ref(
            'product_invoiced_line.product_account_invoice_line_search')
        return {
            'name': _('Supplier Lines invoiced'),
            'domain': self._get_product_supplier_domain(),
            'res_model': 'account.invoice.line',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree')],
            'view_mode': 'tree',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'context': {
                'search_default_inv_open': 1,
                'search_default_inv_paid': 1}}

    @api.multi
    def action_view_customer_invoice_lines(self):
        tree_view = self.env.ref(
            'product_invoiced_line.product_account_invoice_line_tree')
        search_view = self.env.ref(
            'product_invoiced_line.product_account_invoice_line_search')
        return {
            'name': _('Customer Lines invoiced'),
            'domain': self._get_product_customer_domain(),
            'res_model': 'account.invoice.line',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree')],
            'view_mode': 'tree',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'context': {
                'search_default_inv_open': 1,
                'search_default_inv_paid': 1}}
