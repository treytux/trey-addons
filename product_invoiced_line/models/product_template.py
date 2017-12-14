# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sup_inv_lines_count = fields.Float(
        string='Supplier Lines',
        compute='_supplier_lines_count')
    cus_inv_lines_count = fields.Float(
        string='Customer Lines',
        compute='_customer_lines_count')

    @api.multi
    def _supplier_lines_count(self):
        for template in self:
            template.sup_inv_lines_count = sum(
                [p.sup_inv_lines_count for p in template.product_variant_ids])

    @api.multi
    def _customer_lines_count(self):
        for template in self:
            template.cus_inv_lines_count = sum(
                [p.cus_inv_lines_count for p in template.product_variant_ids])

    @api.multi
    def _get_product_template_supplier_domain(self):
        return [
            ('product_id', 'in', self._get_products()),
            ('invoice_id.type', 'in', ['in_invoice', 'in_refund']),
            ('invoice_id.state', '!=', 'cancel')]

    @api.multi
    def _get_product_template_customer_domain(self):
        return [
            ('product_id', 'in', self._get_products()),
            ('invoice_id.type', 'in', ['out_invoice', 'out_refund']),
            ('invoice_id.state', '!=', 'cancel')]

    @api.multi
    def action_view_pt_supplier_invoice_lines(self):
        tree_view = self.env.ref(
            'product_invoiced_line.product_account_invoice_line_tree')
        search_view = self.env.ref(
            'product_invoiced_line.product_account_invoice_line_search')
        return {
            'name': _('Supplier Lines invoiced'),
            'domain': self._get_product_template_supplier_domain(),
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
    def action_view_pt_customer_invoice_lines(self):
        tree_view = self.env.ref(
            'product_invoiced_line.product_account_invoice_line_tree')
        search_view = self.env.ref(
            'product_invoiced_line.product_account_invoice_line_search')
        return {
            'name': _('Customer Lines invoiced'),
            'domain': self._get_product_template_customer_domain(),
            'res_model': 'account.invoice.line',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree')],
            'view_mode': 'tree',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'context': {
                'search_default_inv_open': 1,
                'search_default_inv_paid': 1}}
